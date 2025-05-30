# Initialize the API package
from flask import Blueprint

# Create main API blueprint
api_bp = Blueprint('api', __name__)

# Import and register all API modules
from . import auth
from . import alerts
from . import assets
from . import events
from . import isolation

# Additional initialization if needed

# This file makes the api directory a Python package

api_bp.register_blueprint(isolation.isolation_bp, url_prefix='/isolation')

__all__ = ['api_bp', 'auth', 'alerts', 'assets', 'events']