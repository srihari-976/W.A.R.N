#!/usr/bin/env python3
"""
Initialize W.A.R.N Database
"""
import sys
import os

# Add backend directory to Python path
backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_dir)

from app import create_app
from db import db

def init_database():
    """Initialize database with sample security data"""
    app = create_app()
    
    with app.app_context():
        print("🔧 Creating database tables...")
        db.create_all()
        
    # Skipping sample data population to keep backend free of mock data
    # If needed, import and call populate_sample_data() here.
        
        print("✅ Database initialization complete!")

if __name__ == '__main__':
    init_database()