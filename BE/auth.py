from functools import wraps
import jwt
from flask import jsonify, request
from config import JWT_SECRET_KEY
from functools import wraps

# Modify the jwt_required decorator to handle optional parameter
def jwt_required(optional=False):
    # Check if called directly with a function (no parameters)
    if callable(optional):
        # This handles @jwt_required without parameters
        f = optional
        optional = False
        
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Your JWT validation logic here for required JWT
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({
                    'success': False,
                    'message': 'Missing or invalid authorization token'
                }), 401
            
            token = auth_header.split(' ')[1]
            
            try:
                decoded_token = jwt.decode(
                    token, 
                    JWT_SECRET_KEY, 
                    algorithms=['HS256'],
                    options={"verify_signature": True}
                )
                return f(decoded_token, *args, **kwargs)
            except Exception as e:
                return jsonify({
                   'success': False,
                    'message': f'JWT error: {str(e)}'
                }), 401
                
        return decorated_function
    
    # This handles @jwt_required(optional=True) with parameters
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            auth_header = request.headers.get('Authorization')
            
            # Handle optional token case
            if optional and (not auth_header or not auth_header.startswith('Bearer ')):
                return f(None, *args, **kwargs)
            
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({
                   'success': False,
                    'message': 'Missing or invalid authorization token'
                }), 401
            
            token = auth_header.split(' ')[1]
            
            try:
                decoded_token = jwt.decode(
                    token, 
                    JWT_SECRET_KEY, 
                    algorithms=['HS256'],
                    options={"verify_signature": True}
                )
                return f(decoded_token, *args, **kwargs)
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'JWT error: {str(e)}'
                }), 401
                
        return decorated_function
        
    return decorator