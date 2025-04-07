from flask import jsonify
from api import api_bp
from api.models.product import Product
from api.models.comment import Comment
import logging
from flask import request
from auth import jwt_required

# สร้าง API สำหรับดึงข้อมูลสินค้าพร้อมคอมเมนต์
@api_bp.route('/products-with-comments', methods=['GET'], endpoint='get_products_with_comments')
@jwt_required
def get_products_with_comments(decoded_token):
    try:
        # Get all products
        products, error = Product.get_all()
        
        if error:
            return jsonify({
                'status': 'error',
                'message': error
            }), 500
        
        # For each product, get its comments
        result_data = []
        for product in products:
            product_id = product['productId']
            user_id = decoded_token['sub']
            
            # Get comments for this product
            comments, comment_error = Comment.get_by_product_id(product_id, user_id)
            
            if comment_error:
                logging.error(f"Error fetching comments for product {product_id}: {comment_error}")
                comments = []
            
            # Add comments to product data
            product_with_comments = product.copy()
            product_with_comments['comments'] = comments
            result_data.append(product_with_comments)
        
        return jsonify({
            'status': 'success',
            'data': result_data
        }), 200
    
    except Exception as e:
        logging.error(f"Error in get_products_with_comments: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Server error: {str(e)}'
        }), 500

# สร้าง API สำหรับดึงข้อมูลสินค้าเฉพาะพร้อมคอมเมนต์
@api_bp.route('/product/<int:product_id>/with-comments', methods=['GET'], endpoint='get_product_with_comments')
@jwt_required
def get_product_with_comments(decoded_token, product_id):
    try:
        # Get the specific product
        product, product_error = Product.get_by_id(product_id)
        
        if product_error:
            return jsonify({
                'status': 'error',
                'message': product_error
            }), 500
        
        if not product:
            return jsonify({
                'status': 'error',
                'message': 'Product not found'
            }), 404
        
        # Get comments for this product
        user_id = decoded_token['sub']
        comments, comment_error = Comment.get_by_product_id(product_id, user_id)
        
        if comment_error:
            logging.error(f"Error fetching comments for product {product_id}: {comment_error}")
            comments = []
        
        # Add comments to product data
        product['comments'] = comments
        
        return jsonify({
            'status': 'success',
            'data': [product]  # Wrap in array to match desired structure
        }), 200
    
    except Exception as e:
        logging.error(f"Error in get_product_with_comments: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Server error: {str(e)}'
        }), 500