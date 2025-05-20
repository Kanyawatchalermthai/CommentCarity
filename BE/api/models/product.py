from app import mysql
from flask import jsonify
from flask import current_app
from db import mysql

class Product:
    @staticmethod
    def get_all():
        try:
            cursor = mysql.connection.cursor()
            cursor.execute("""
                SELECT productId, productName, startDate, endDate, createdAt, userId
                FROM products
            """)
            
            products = []
            for row in cursor.fetchall():
                product = {
                    'productId': row[0],
                    'productName': row[1],
                    'startDate': row[2],
                    'endDate': row[3],
                    'createdAt': row[4],
                    'userId': row[5]
                }
                products.append(product)
            
            cursor.close()
            return products, None
            
        except Exception as e:
            return None, str(e)
    
    @staticmethod
    def get_by_id(product_id, user_id):
        try:
            cursor = mysql.connection.cursor()
            cursor.execute("""
                SELECT productId, productName, startDate, endDate, createdAt, userId
                FROM products
                WHERE productId = %s AND userId = %s
            """, (product_id, user_id))
            
            row = cursor.fetchone()
            cursor.close()

            if row:
                product = {
                    'productId': row[0],
                    'productName': row[1],
                    'startDate': row[2],
                    'endDate': row[3],
                    'createdAt': row[4],
                    'userId': row[5]
                }
                return product, None
            else:
                return None, 'Product not found or not owned by this user'
            
        except Exception as e:
            return None, str(e)

    @staticmethod
    def get_user_products(user_id):
        try:
            cursor = mysql.connection.cursor()
            cursor.execute("""
                SELECT productId, productName, startDate, endDate, createdAt, userId
                FROM products
                WHERE userId = %s
            """, (user_id,))
            
            products = []
            for row in cursor.fetchall():
                product = {
                    'productId': row[0],
                    'productName': row[1],
                    'startDate': row[2],
                    'endDate': row[3],
                    'createdAt': row[4],
                    'userId': row[5]
                }
                products.append(product)
            
            cursor.close()
            return products, None
            
        except Exception as e:
            return None, str(e)
            
    @staticmethod
    def delete_user_product(user_id, product_id):
        try:
            cursor = mysql.connection.cursor()
            
            cursor.execute("""
                SELECT * FROM products 
                WHERE productId = %s AND userId = %s
            """, (product_id, user_id))
            
            if not cursor.fetchone():
                cursor.close()
                return False, "Product not found or not owned by this user"
            
            cursor.execute("""
                DELETE FROM comments 
                WHERE productId = %s
            """, (product_id,))

            cursor.execute("""
                DELETE FROM products 
                WHERE productId = %s AND userId = %s
            """, (product_id, user_id))
            
            mysql.connection.commit()
            cursor.close()
            
            return True, "Product and related comments successfully deleted"
            
        except Exception as e:
            mysql.connection.rollback()
            return False, str(e)
            
    @staticmethod
    def create_product_if_unique_for_user(product_name, start_date, end_date, user_id, connection=None):
        if connection:
            conn = connection
            cursor = conn.cursor()
            external_conn = True
        else:
            cursor = mysql.connection.cursor()
            external_conn = False
        
        try:
            cursor.execute("""
                SELECT * FROM products 
                WHERE productName = %s AND userId = %s
            """, (product_name, user_id))
            
            if cursor.fetchone():
                if not external_conn:
                    cursor.close()
                return None, "This product name already exists for this user."
                
            cursor.execute("""
                INSERT INTO products (productName, startDate, endDate, createdAt, userId)
                VALUES (%s, %s, %s, CONVERT_TZ(NOW(), '+00:00', '+07:00'), %s)
            """, (product_name, start_date, end_date, user_id))
            
            # ถ้าไม่ได้ใช้ external connection ให้ commit เลย
            if not external_conn:
                mysql.connection.commit()
                product_id = cursor.lastrowid
                cursor.close()
            else:
                # ถ้าใช้ external connection ให้เก็บ lastrowid และไม่ต้อง commit
                product_id = cursor.lastrowid
                
            return product_id, None
            
        except Exception as e:
            if not external_conn:
                mysql.connection.rollback()
                cursor.close()
            return None, str(e)
