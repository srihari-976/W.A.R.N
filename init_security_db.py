#!/usr/bin/env python3
"""
Initialize W.A.R.N Security Database with Sample Data
Run this script to set up the SQLite database with security events from 12-05-2025
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app import create_app
from backend.db import db
from backend.utils.populate_security_data import populate_sample_data

def init_database():
    """Initialize database with sample security data"""
    app = create_app()
    
    with app.app_context():
        print("🔧 Creating database tables...")
        db.create_all()
        
        print("📊 Populating sample security data...")
        populate_sample_data()
        
        print("✅ Database initialization complete!")
        print("\n📋 Summary:")
        print("   - DoS attacks: 15 events")
        print("   - Brute force: 25 events") 
        print("   - Phishing: 12 events")
        print("   - Malware: 8 events")
        print("   - Blocked IPs: 3")
        print("   - Locked accounts: 2")
        print("\n🚀 Start the server with: python backend/app.py")

if __name__ == '__main__':
    init_database()