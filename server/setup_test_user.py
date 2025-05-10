from backend.app import create_app
from backend.models.user import User
from backend.db import db
from werkzeug.security import generate_password_hash

def setup_test_user():
    app = create_app()
    with app.app_context():
        # Drop all tables and recreate them
        db.drop_all()
        db.create_all()
        
        # Create test user
        test_user = User(
            username='testuser',
            email='test@example.com',
            password='testpass',  # This will be hashed by User.__init__
            role='admin'
        )
        
        # Save the user
        db.session.add(test_user)
        db.session.commit()
        
        # Verify the user was created
        user = User.query.filter_by(username='testuser').first()
        if user and user.check_password('testpass'):
            print("Test user created successfully!")
            print(f"Username: testuser")
            print(f"Password: testpass")
            print(f"Role: {user.role}")
        else:
            print("Error: User creation failed!")

if __name__ == '__main__':
    setup_test_user() 