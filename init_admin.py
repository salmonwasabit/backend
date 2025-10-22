#!/usr/bin/env python3
"""
Initialize admin user for the secure authentication system
"""
import sys
import os
sys.path.append('.')

from app.main import engine, Base, get_password_hash, SessionLocal
from app.main import User

def init_admin_user():
    # Drop and recreate tables to add new columns
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    # Create admin user
    db = SessionLocal()
    try:
        # Check if admin user already exists
        existing_user = db.query(User).filter(User.username == "admin").first()
        if existing_user:
            print("Admin user already exists")
            return
        
        # Create admin user
        hashed_password = get_password_hash("admin123")
        admin_user = User(
            username="admin",
            email="admin@vapelife.com",
            hashed_password=hashed_password,
            is_active=1
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print(f"Admin user created successfully:")
        print(f"Username: admin")
        print(f"Password: admin123")
        print(f"Email: admin@vapelife.com")
        
    except Exception as e:
        print(f"Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_admin_user()
