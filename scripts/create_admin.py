#!/usr/bin/env python3
"""Script to create the first admin user"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import User, UserRole
from app.auth import get_password_hash
from app.config import settings
import getpass


def create_admin_user():
    """Create an admin user interactively"""
    print("=" * 60)
    print("Clinical FHIR Extractor - Create Admin User")
    print("=" * 60)
    print()
    
    # Connect to database
    engine = create_engine(settings.database_url, connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    try:
        # Get admin details
        print("Please enter admin user details:")
        print()
        
        username = input("Username: ").strip()
        if not username:
            print("❌ Username is required")
            return
        
        # Check if username exists
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            print(f"❌ User '{username}' already exists")
            return
        
        email = input("Email: ").strip()
        if not email:
            print("❌ Email is required")
            return
        
        # Check if email exists
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            print(f"❌ Email '{email}' already exists")
            return
        
        full_name = input("Full Name (optional): ").strip() or None
        
        password = getpass.getpass("Password: ")
        if len(password) < settings.password_min_length:
            print(f"❌ Password must be at least {settings.password_min_length} characters")
            return
        
        password_confirm = getpass.getpass("Confirm Password: ")
        if password != password_confirm:
            print("❌ Passwords do not match")
            return
        
        # Create admin user
        admin = User(
            username=username,
            email=email,
            full_name=full_name,
            hashed_password=get_password_hash(password),
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True
        )
        
        db.add(admin)
        db.commit()
        
        print()
        print("=" * 60)
        print("✅ Admin user created successfully!")
        print("=" * 60)
        print(f"Username: {username}")
        print(f"Email: {email}")
        print(f"Role: ADMIN")
        print()
        print("You can now login using:")
        print(f'  curl -X POST "http://localhost:8000/auth/login" \\')
        print(f'    -H "Content-Type: application/json" \\')
        print(f'    -d \'{{"username":"{username}","password":"YOUR_PASSWORD"}}\'')
        print()
    
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_admin_user()

