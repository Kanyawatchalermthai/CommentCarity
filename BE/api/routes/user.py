from flask import jsonify
from api import api_bp
from flask import request
from api.models.user import User
from flask import Response
from flask_jwt_extended import create_access_token
from auth import jwt_required  # เพิ่มการใช้ JWT

# สร้าง API สำหรับดึงข้อมูลจากตาราง users
@api_bp.route('/users', methods=['GET'])
@jwt_required
def get_all_users(decoded_token):
    user_id = decoded_token['sub']

    users, error = User.get_all(user_id)
    
    if error:
        status_code = 404 if 'not found' in error.lower() else 500
        return jsonify({
            'success': False,
            'message': error
        }), status_code
    
    if users is None or len(users) == 0:
        return jsonify({
            'success': True,
            'data': []
        }), 200
    
    return jsonify({
        'success': True,
        'data': users
    }), 200

# สร้าง API สำหรับดึงข้อมูลจากตาราง users โดยระบุ user_id
@api_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user_by_id(user_id):
    user, error = User.get_by_id(user_id)
    
    if error:
        status_code = 404 if 'not found' in error.lower() else 500
        return jsonify({
            'success': False,
            'message': error
        }), status_code
    
    if user is None:
        return jsonify({
            'success': False,
            'message': f"User with ID {user_id} not found"
        }), 404
    
    return jsonify({
       'success': True,
        'data': user
    }), 200

# สร้าง API สำหรับ Register ผู้ใช้งาน
@api_bp.route('/users/register', methods=['POST'])
def register_user():
    data = request.get_json()
    firstName = data.get('firstName')
    lastName = data.get('lastName')
    email = data.get('email')
    password = data.get('password')
    
    if not firstName or not lastName or not email or not password:
        return jsonify({
            'success': False,
            'message': 'Invalid input'
        }), 400
    
    if User.user_exists(email):
        return jsonify({
            'success': False,
            'message': 'User already exists'
        }), 400
    
    if User.register(firstName, lastName, email, password):
        return jsonify({
            'success': True,
            'message': 'User registered successfully'
        }), 201
    
    return jsonify({
        'success': False,
        'message': 'Error registering user'
    }), 500

# สร้าง API สำหรับ login ผู้ใช้งาน
@api_bp.route('/users/login', methods=['POST'])
def login_user():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({
            'success': False,
            'message': 'Invalid input'
        }), 400
    
    user = User.login(email, password)
    
    if user:
        access_token = create_access_token(identity=str(user.userId))
        
        return jsonify({
           'success': True,
            'data': {
                'access_token': access_token,
                'user': {
                    'userId': getattr(user, 'userId', None),
                    'firstName': getattr(user, 'firstName', None),
                    'lastName': getattr(user, 'lastName', None),
                    'email': getattr(user, 'email', None)
                }
            }
        }), 200
    
    return jsonify({
        'success': False,
        'message': 'Invalid email or password'
    }), 401

