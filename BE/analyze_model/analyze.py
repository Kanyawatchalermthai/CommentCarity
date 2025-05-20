from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import re
import pandas as pd
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from dateutil.relativedelta import relativedelta
import emoji
from pythainlp.tokenize import word_tokenize
from pythainlp.corpus import thai_words
import joblib
import logging
import psutil
import os

# กำหนด path ไปยังโฟลเดอร์ที่เก็บโมเดล
MODEL_PATH = os.path.join(os.path.dirname(__file__), '.') 

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('analyzer')

def analyze(link_url, start_date, end_date):
    """
    Scrape and analyze reviews from a Lazada product page
    
    Args:
        link_url (str): URL of the Lazada product
        start_date (str): Start date in YYYY-MM format
        end_date (str): End date in YYYY-MM format
        
    Returns:
        pandas.DataFrame: DataFrame containing analyzed reviews
    """
    try:
        logger.info(f"Starting analysis for URL: {link_url}")
        logger.info(f"Time period: {start_date} to {end_date}")
        
        # URL configuration
        url = link_url

        # XPath configurations
        XPATHS = {
            "next_button": "/html/body/div[5]/div/div[10]/div[1]/div[2]/div/div/div/div[3]/div[2]/div/button[2]",
            "sort_button": "/html/body/div[5]/div/div[10]/div[1]/div[2]/div/div/div/div[2]/div/div[2]",
            "newest_first": "/html/body/div[9]/div/div/ul/li[2]"
        }

        # Thai month abbreviations mapping
        THAI_MONTHS = {
            "ม.ค.": "01", "ก.พ.": "02", "มี.ค.": "03", "เม.ย.": "04", 
            "พ.ค.": "05", "มิ.ย.": "06", "ก.ค.": "07", "ส.ค.": "08", 
            "ก.ย.": "09", "ต.ค.": "10", "พ.ย.": "11", "ธ.ค.": "12"
        }

        def create_driver(max_retries=3):
            for attempt in range(max_retries):
                try:
                    options = Options()
                    options.add_argument("--disable-blink-features=AutomationControlled")
                    options.add_experimental_option("excludeSwitches", ["enable-automation"])
                    options.add_experimental_option("useAutomationExtension", False)
                    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
                    options.add_argument("--no-sandbox")
                    options.add_argument("--window-size=1920,1080")
                    options.add_argument("--disable-gpu")
                    options.add_argument("--disable-dev-shm-usage")
                    # Add this option to help with connection issues
                    options.add_experimental_option("detach", True)

                    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
                    return driver
                except Exception as e:
                    logger.error(f"Driver creation attempt {attempt+1} failed: {str(e)}")
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(2)

        def safe_driver_quit(driver):
            """Safely quit the driver with error handling"""
            if driver:
                try:
                    # Close all windows first
                    driver.close()
                    time.sleep(1)
                    driver.quit()
                except Exception as e:
                    logger.warning(f"Error while closing driver: {str(e)}")
                    # Try a more forceful approach if regular quit fails
                    try:
                        process = psutil.Process(driver.service.process.pid)
                        for proc in process.children(recursive=True):
                            proc.kill()
                        process.kill()
                    except:
                        pass

        def parse_thai_date(text):
            """Convert Thai date formats to YYYY-MM-DD format"""
            now = datetime.now()
       
            time_patterns = {
                "ชั่วโมง": lambda x: now - timedelta(hours=int(x)),
                "วัน": lambda x: now - timedelta(days=int(x)),
                "สัปดาห์": lambda x: now - timedelta(weeks=int(x)),
                "นาที": lambda x: now - timedelta(minutes=int(x)),
                "วินาที": lambda x: now - timedelta(seconds=int(x))
            }
            
            for pattern, time_func in time_patterns.items():
                if pattern in text:
                    match = re.search(r'\d+', text)
                    if match:
                        return time_func(match.group()).strftime("%Y-%m-%d")
            
            parts = text.split()
            if len(parts) == 3:
                day, month_thai, year = parts
                month = THAI_MONTHS.get(month_thai)
                if month:
                    try:
                        date_str = f"{year}-{month}-{day.zfill(2)}"
                        return datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m-%d")
                    except ValueError:
                        pass
            
            return None

        def scroll_page(driver):
            """Scroll down the page to load all content"""
            for _ in range(3):  # Limited scrolling to avoid infinite loops
                driver.execute_script("window.scrollBy(0, 1000);")
                time.sleep(1)
                current_position = driver.execute_script("return window.scrollY + window.innerHeight")
                page_height = driver.execute_script("return document.body.scrollHeight")
                if current_position >= page_height:
                    break

        def click_element(driver, xpath, max_attempts=3):
            """Safely click an element by xpath with retry logic"""
            for attempt in range(max_attempts):
                try:
                    element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, xpath)))
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                    driver.execute_script("arguments[0].click();", element)
                    time.sleep(1)
                    return True
                except Exception as e:
                    logger.warning(f"Click attempt {attempt+1} failed: {str(e)}")
                    if attempt == max_attempts - 1:
                        return False
                    time.sleep(2)

        def try_next_page(driver):
            """Attempt to navigate to the next page of reviews"""
            try:
                next_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, XPATHS["next_button"]))
                )
                if 'disabled' in next_button.get_attribute('class'):
                    return False
                    
                driver.execute_script("arguments[0].click();", next_button)
                time.sleep(2)
                return True
            except Exception as e:
                logger.warning(f"Next page navigation failed: {str(e)}")
                return False

        def scrape_reviews(url, start_period, end_period, max_retries=3):
            """Scrape reviews from Lazada within the specified time period"""
            start_dt = datetime.strptime(start_period, "%Y-%m")
            stop_dt = start_dt - relativedelta(months=1)
            stop_period = stop_dt.strftime("%Y-%m")
            
            driver = None
            for attempt in range(max_retries):
                try:
                    logger.info(f"Starting scraping attempt {attempt+1}")
                    driver = create_driver()
                    driver.get(url)
                    time.sleep(5)  # Increased wait time
                    scroll_page(driver)

                    # Wait for sort button
                    try:
                        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, XPATHS["sort_button"])))
                        logger.info("✅ Sort button found")
                    except Exception as e:
                        logger.error(f"Sort button not found: {str(e)}")
                        safe_driver_quit(driver)
                        driver = None
                        if attempt == max_retries - 1:
                            return pd.DataFrame()  # Return empty DataFrame on failure
                        continue

                    # Sort by newest
                    if not click_element(driver, XPATHS["sort_button"]):
                        logger.error("Failed to click sort button")
                        continue
                        
                    if not click_element(driver, XPATHS["newest_first"]):
                        logger.error("Failed to click newest first option")
                        continue

                    collect_active = False
                    all_reviews = []
                    
                    logger.info("🔄 Starting review collection...")
                    page_count = 0

                    while True:  # No page limit, continue until we hit the stop condition
                        page_count += 1
                        logger.info(f"Processing page {page_count}")
                        
                        # Ensure page has loaded completely
                        time.sleep(3)
                        
                        soup = BeautifulSoup(driver.page_source, "html.parser")

                        content_divs = [
                            content for item in soup.find_all('div', class_='item-content')
                            if item.get('class') == ['item-content']
                            for content in item.find_all('div', class_='content')
                        ]
                        reviews = [div.get_text(strip=True) for div in content_divs]
                        
                        star_divs = soup.find_all('div', class_='container-star starCtn left')
                        star_ratings = [
                            len([img for img in div.find_all('img', class_='star') 
                                if img.get('src') == "//img.lazcdn.com/g/tps/tfs/TB19ZvEgfDH8KJjy1XcXXcpdXXa-64-64.png"])
                            for div in star_divs
                        ]
                        
                        date_spans = soup.find_all("span", class_="title right")
                        raw_dates = [span.get_text(strip=True) for span in date_spans]
                        full_dates = [parse_thai_date(d) for d in raw_dates]

                        min_len = min(len(reviews), len(star_ratings), len(full_dates))
                        reviews = reviews[:min_len]
                        star_ratings = star_ratings[:min_len]
                        full_dates = full_dates[:min_len]
                        
                        logger.info(f"Found {len(reviews)} reviews on this page")
                        
                        stop_collection = False
                        items_added = 0

                        for review, rating, full_date in zip(reviews, star_ratings, full_dates):
                            if not full_date:
                                continue
                                
                            month_year = full_date[:7]

                            if not collect_active:
                                if month_year <= end_period:
                                    collect_active = True
                                    logger.info(f"✅ Collection started at: {month_year}")

                            if collect_active:
                                if month_year <= stop_period:
                                    stop_collection = True
                                    break
                                all_reviews.append({"ratings": rating, "text": review, "date": full_date})
                                items_added += 1
                        
                        logger.info(f"Added {items_added} reviews from this page")
                        
                        if stop_collection:
                            logger.info("✅ Collection complete: reached cutoff date")
                            break
                            
                        if not try_next_page(driver):
                            logger.info("🛑 No more pages available")
                            break
                    
                    logger.info(f"Total reviews collected: {len(all_reviews)}")
                    safe_driver_quit(driver)
                    driver = None
                        
                    return pd.DataFrame(all_reviews)
                    
                except Exception as e:
                    logger.error(f"Scraping attempt {attempt+1} failed: {str(e)}")
                    if attempt == max_retries - 1:
                        return pd.DataFrame()  # Return empty DataFrame on failure
                    time.sleep(5)  # Wait before retrying
                finally:
                    if driver:
                        safe_driver_quit(driver)
                        driver = None

        try:
            logger.info("Loading Thai words vocabulary...")
            VOCAB = set(thai_words())
        except Exception as e:
            logger.error(f"Error loading Thai vocabulary: {str(e)}")
            VOCAB = set()

        def clean_text(text):
            """Clean and tokenize Thai text"""
            if not isinstance(text, str):
                return None
                
            try:
                # Remove emojis and newlines
                text = emoji.replace_emoji(text, '').replace('\n', ' ').replace('\r', ' ')
                # Remove repeated characters (more than 3 of the same)
                text = re.sub(r'(.)\1{3,}', r'\1\1', text)
                # Remove special characters except Thai, Latin, numbers
                text = re.sub(r'[^\u0E00-\u0E7Fa-zA-Z0-9\s:]', '', text)
                # Remove duplicate words
                seen = set()
                text = " ".join([w for w in text.split() if not (w in seen or seen.add(w))])
                # Tokenize and filter by vocabulary
                tokens = word_tokenize(text, engine="newmm", keep_whitespace=True)
                return [w for w in tokens if w in VOCAB or w.isnumeric()]
            except Exception as e:
                logger.error(f"Error processing text: {e}")
                return None

        # Main analysis process
        logger.info(f"Starting analysis for time period {start_date} to {end_date}")
        
        # Scrape reviews
        df = scrape_reviews(url, start_date, end_date)
        
        if df.empty:
            logger.warning("No reviews found for the specified time period")
            return df
            
        logger.info(f"Scraped {len(df)} reviews, now cleaning and tokenizing text")
        
        # Process reviews
        df["text_token"] = df["text"].apply(clean_text)
        df = df[~df['text_token'].isin(['[]', '', None])]
        
        # Load models
        try:
            logger.info("Loading ML models...")
            cvec = joblib.load(os.path.join(MODEL_PATH, 'cvec.pkl'))
            le_sentiment = joblib.load(os.path.join(MODEL_PATH, 'le_sentiment.pkl'))
            xgb_sentiment = joblib.load(os.path.join(MODEL_PATH, 'xgb_sentiment.pkl'))
            le_category = joblib.load(os.path.join(MODEL_PATH, 'le_category.pkl'))
            xgb_category = joblib.load(os.path.join(MODEL_PATH, 'xgb_category.pkl'))
        except Exception as e:
            logger.error(f"Error loading ML models: {str(e)}")
            # If models fail to load, add placeholder columns and return early
            df['sentimentType'] = 'Neutral'
            df['commentCategoryName'] = 'Other'
            df = df.drop(columns=['text_token'])
            return df

        # Predict sentiment and category
        try:
            logger.info("Vectorizing text and predicting sentiment/category")
            X_vec = cvec.transform(df['text_token'])
            
            y_sentiment_pred = xgb_sentiment.predict(X_vec)
            df['sentimentType'] = le_sentiment.inverse_transform(y_sentiment_pred)
            
            y_category_pred = xgb_category.predict(X_vec)
            df['commentCategoryName'] = le_category.inverse_transform(y_category_pred)
        except Exception as e:
            logger.error(f"Error during prediction: {str(e)}")
            # If prediction fails, add placeholder columns
            df['sentimentType'] = 'Neutral'
            df['commentCategoryName'] = 'Other'
            
        # Map values to friendly names
        df['sentimentType'] = df['sentimentType'].replace({
            'pos': 'Positive', 'neg': 'Negative', 'neu': 'Neutral'
        })
        df['commentCategoryName'] = df['commentCategoryName'].replace({
            'product': 'Product', 'delivery': 'Delivery', 
            'service': 'Service', 'none': 'Other'
        })
        
        # Drop intermediate columns and save results
        df = df.drop(columns=['text_token'])
        
        logger.info(f"Analysis complete with {len(df)} processed reviews")
        df.to_csv('output.csv', index=False, encoding='utf-8-sig')
        
        return df
        
    except Exception as e:
        logger.error(f"Major error in analyze function: {str(e)}")
        # Return empty DataFrame on major error
        return pd.DataFrame()
        

# NOTE: ตัวอย่างการเรียกใช้งานฟังก์ชัน 

# หากต้องการทดสอบ
# > py analyze.py
# result = analyze(
#     "https://www.lazada.co.th/products/3-i5432338284-s23195260672.html?pvid=95e452bf-d588-4c34-bec7-f84bf9de8bdc&search=jfy&scm=1007.45039.432958.0&priceCompare=skuId%3A23195260672%3Bsource%3Atpp-recommend-plugin-32104%3Bsn%3A95e452bf-d588-4c34-bec7-f84bf9de8bdc%3BoriginPrice%3A5900%3BdisplayPrice%3A5900%3BsinglePromotionId%3A-1%3BsingleToolCode%3AmockedSalePrice%3BvoucherPricePlugin%3A0%3Btimestamp%3A1746879709497&spm=a2o4m.homepage.just4u.d_5432338284", 
#     "2025-5", 
#     "2025-05"
# )