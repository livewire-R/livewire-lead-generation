#!/usr/bin/env python3
"""
Database initialization script for SalesFuel.au platform
This script creates all necessary database tables
"""

import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def create_app():
    """Create Flask app for database initialization"""
    app = Flask(__name__)
    
    # Database configuration
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    else:
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///leed_io.db"
    
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_timeout": 20,
        "max_overflow": 0
    }
    
    return app

def init_database():
    """Initialize database tables"""
    app = create_app()
    
    with app.app_context():
        # Import all models to register them
        from models.client import db, Client, Admin
        from models.lead_model import Lead
        from models.campaign import Campaign
        
        print("🔧 Creating database tables...")
        
        # Create all tables
        db.init_app(app)
        db.create_all()
        
        print("✅ Database tables created successfully!")
        
        # Verify tables exist
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        print(f"📊 Created tables: {', '.join(tables)}")
        
        return True

if __name__ == "__main__":
    try:
        init_database()
        print("🎉 Database initialization completed successfully!")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        sys.exit(1)

