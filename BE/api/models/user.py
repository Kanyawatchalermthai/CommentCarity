from app import mysql
from flask import session
from flask_bcrypt import Bcrypt
from flask import jsonify

bcrypt = Bcrypt()

class User:
    def __init__(self, userId=None, firstName=None, lastName=None, email=None, password=None, createdAt=None, is_hashed=False):
        self.userId = userId
        self.firstName = firstName
        self.lastName = lastName
        self.email = email
        if password:
            if not is_hashed:
                self.password = bcrypt.generate_password_hash(password).decode('utf-8')
            else:
                self.password = password
        else:
            self.password = None
        self.createdAt = createdAt

    def to_dict(self):
        return {
            'userId': self.userId,
            'firstName': self.firstName,
            'lastName': self.lastName,
            'email': self.email,
            'createdAt': self.createdAt
        }

    @staticmethod
    def register(firstName, lastName, email, password):
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        try:
            cursor = mysql.connection.cursor()
            cursor.execute("""
                INSERT INTO users (firstName, lastName, email, password, createdAt) 
                VALUES (%s, %s, %s, %s, CONVERT_TZ(NOW(), '+00:00', '+07:00'))
            """, (firstName, lastName, email, hashed_password))

            mysql.connection.commit()
            cursor.close()
            return True
        except Exception as e:
            print(f"Error registering user: {str(e)}")
            return False

    @staticmethod
    def login(email, password):
        try:
            cursor = mysql.connection.cursor()
            cursor.execute("""
                SELECT userId, firstName, lastName, email, password 
                FROM users WHERE email = %s
            """, (email,))
            row = cursor.fetchone()
            cursor.close()
            
            if row:
                user = User(
                    userId=row[0],
                    firstName=row[1],
                    lastName=row[2],
                    email=row[3],
                    password=row[4],
                    is_hashed=True
                )
                if bcrypt.check_password_hash(user.password, password):
                    return user
            return None
        except Exception as e:
            print(f"Error logging in user: {str(e)}")
            return None

    @staticmethod
    def user_exists(email):
        try:
            cursor = mysql.connection.cursor()
            cursor.execute("""
                SELECT 1 FROM users WHERE email = %s
            """, (email,))
            row = cursor.fetchone()
            cursor.close()
            return row is not None
        except Exception as e:
            print(f"Error checking user existence: {str(e)}")
            return False
        
    @staticmethod
    def get_all(user_id=None):
        try:
            cursor = mysql.connection.cursor()
            cursor.execute("""
                SELECT userId, firstName, lastName, email 
                FROM users
            """)
            users = cursor.fetchall()
            cursor.close()
            
            user_list = []
            for user in users:
                user_list.append({
                    "userId": user[0],
                    "firstName": user[1],
                    "lastName": user[2],
                    "email": user[3]
                })
            
            return user_list, None  
        except Exception as e:
            print(f"Error getting users by user_id: {str(e)}")
            return None, str(e)
        
    @staticmethod
    def get_by_id(user_id):
            try:
                cursor = mysql.connection.cursor()
                cursor.execute("""
                    SELECT userId, firstName, lastName, email, createdAt
                    FROM users WHERE userId = %s
                """, (user_id,))
                row = cursor.fetchone()
                cursor.close()
                
                if row:
                    user_data = {
                        "userId": row[0],
                        "firstName": row[1],
                        "lastName": row[2],
                        "email": row[3],
                        "createdAt": row[4].strftime('%Y-%m-%d %H:%M:%S') if row[4] else None
                    }
                    return user_data, None
                else:
                    return None, f"User with ID {user_id} not found"
            except Exception as e:
                print(f"Error getting user by ID: {str(e)}")
                return None, str(e)   
            
    @staticmethod
    def get_latest_product_by_user(user_id, limit=1):
        try:
            cursor = mysql.connection.cursor()
            cursor.execute("""
                SELECT p.productId, p.productName
                FROM UserProducts up
                JOIN products p ON up.productId = p.productId
                WHERE up.userId = %s
                ORDER BY up.userProductId DESC
                LIMIT %s
            """, (user_id, limit))
            
            rows = cursor.fetchall()
            cursor.close()
            
            products = [{'productId': row[0], 'productName': row[1]} for row in rows]
            return products, None

        except Exception as e:
            return None, str(e)
