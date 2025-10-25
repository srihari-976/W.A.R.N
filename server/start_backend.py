#!/usr/bin/env python3
"""
Simple backend startup script for W.A.R.N
"""
import sys
import os

# Add backend directory to Python path
backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_dir)

# Import and run the app
from app import create_app

if __name__ == '__main__':
    app = create_app()
    print("🚀 Starting W.A.R.N Backend Server...")
    print("📊 Database: SQLite (warn_security.db)")
    print("🔗 API: http://localhost:5000")
    print("🛡️ Security monitoring: Active")
    app.run(host='0.0.0.0', port=5000, debug=True)