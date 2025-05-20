-- สร้างฐานข้อมูลพร้อมกำหนด character set และ collation
CREATE DATABASE IF NOT EXISTS comment_clarity_schema
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

-- ใช้งานฐานข้อมูล
USE comment_clarity_schema;

-- สร้างตาราง Users
CREATE TABLE Users (
    userId INT PRIMARY KEY AUTO_INCREMENT,
    firstName VARCHAR(50) NOT NULL,
    lastName VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- สร้างตาราง Products
CREATE TABLE Products (
    productId INT PRIMARY KEY AUTO_INCREMENT,
    productName VARCHAR(100) NOT NULL,
    startDate VARCHAR(7) NOT NULL,
    endDate VARCHAR(7) NOT NULL,
    createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    userId INT NOT NULL,
    FOREIGN KEY (userId) REFERENCES Users(userId) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- สร้างตาราง SentimentAnalysis
CREATE TABLE SentimentAnalysis (
    sentimentId INT PRIMARY KEY AUTO_INCREMENT,
    sentimentType ENUM('Positive', 'Negative', 'Neutral') NOT NULL
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- สร้างตาราง CommentCategory
CREATE TABLE CommentCategory (
    commentCategoryId INT PRIMARY KEY AUTO_INCREMENT,
    commentCategoryName ENUM('Product', 'Delivery','Service','Other') NOT NULL
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- สร้างตาราง Comments
CREATE TABLE Comments (
    commentId INT PRIMARY KEY AUTO_INCREMENT,
    ratings INT NOT NULL CHECK (ratings BETWEEN 1 AND 5),
    text VARCHAR(1000) NOT NULL,
    date DATE DEFAULT CURRENT_TIMESTAMP,
    sentimentId INT,
    userId INT,
    productId INT,
    commentCategoryId INT,
    FOREIGN KEY (sentimentId) REFERENCES SentimentAnalysis(sentimentId),
    FOREIGN KEY (userId) REFERENCES Users(userId),
    FOREIGN KEY (productId) REFERENCES Products(productId),
    FOREIGN KEY (commentCategoryId) REFERENCES CommentCategory(commentCategoryId)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- สร้าง Index
CREATE INDEX idx_comments_sentiment ON Comments(sentimentId);
CREATE INDEX idx_comments_product ON Comments(productId);
CREATE INDEX idx_comments_category ON Comments(commentCategoryId);
