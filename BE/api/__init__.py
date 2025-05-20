from flask import Blueprint

# Create Blueprint for API
api_bp = Blueprint('api', __name__)

# Import routes
from .routes import comment
from .routes import user
from .routes import product