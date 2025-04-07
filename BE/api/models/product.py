from app import mysql
from flask import jsonify


# NOTE: if ADD check if +7.00 is correct
class Product:
    @staticmethod
    def get_all():
        try:
            cursor = mysql.connection.cursor()
            cursor.execute("""
                SELECT productId, productName ,startDate , endDate, createdAt
                FROM products
            """)
            
            products = []
            for row in cursor.fetchall():
                product = {
                    'productId': row[0],
                    'productName': row[1],
                    'startDate': row[2],
                    'endDate': row[3],
                    'createdAt': row[4]
                }
                products.append(product)
            
            cursor.close()
            return products, None
            
        except Exception as e:
            return None, str(e)
    
    @staticmethod
    def get_by_id(product_id):
        try:
            cursor = mysql.connection.cursor()
            cursor.execute("""
                SELECT productId, productName, startDate, endDate, createdAt
                FROM products
                WHERE productId = %s
            """, (product_id,))
            
            row = cursor.fetchone()
            cursor.close()
            
            if row:
                product = {
                    'productId': row[0],
                    'productName': row[1],
                    'startDate': row[2],
                    'endDate': row[3],
                    'createdAt': row[4]
                    
                }
                return product, None
            else:
                return None, 'Product not found'
            
        except Exception as e:
            return None, str(e)

    @staticmethod
    def get_user_products(user_id):
        try:
            cursor = mysql.connection.cursor()
            cursor.execute("""
                SELECT p.productId, p.productName, p. startDate, p.endDate, p.createdAt, up.isCreator
                FROM products p
                JOIN userproducts up ON p.productId = up.productId
                WHERE up.userId = %s
            """, (user_id,))
            
            products = []
            for row in cursor.fetchall():
                product = {
                    'productId': row[0],
                    'productName': row[1],
                    'startDate': row[2],
                    'endDate': row[3],
                    'createdAt': row[4],
                    'isCreator': bool(row[5])
                }
                products.append(product)
            
            cursor.close()
            return products, None
            
        except Exception as e:
            return None, str(e)
