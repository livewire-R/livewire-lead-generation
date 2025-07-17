import os
import sys
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

# Add the src directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import models and services
from models.client import Client, client_db
from models.lead import Lead
from models.campaign import Campaign, CampaignExecution
from routes.auth import auth_bp
from routes.leads import leads_bp
from routes.campaigns import campaigns_bp
from services.campaign_scheduler import init_campaign_scheduler

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Database configuration
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        # Railway provides DATABASE_URL, but we need to handle postgres:// vs postgresql://
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        # Fallback for local development
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///leed_io.db'
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # CORS configuration
    cors_origins = os.getenv('CORS_ORIGINS', 'http://localhost:5173,http://localhost:3000').split(',')
    CORS(app, origins=cors_origins, supports_credentials=True)
    
    # Initialize database
    client_db.init_app(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(leads_bp, url_prefix='/api')
    app.register_blueprint(campaigns_bp, url_prefix='/api')
    
    # Initialize campaign scheduler
    try:
        init_campaign_scheduler(app)
    except Exception as e:
        app.logger.warning(f"Campaign scheduler initialization failed: {e}")
    
    # Health check endpoint
    @app.route('/api/health')
    def health_check():
        """Health check endpoint for Railway deployment"""
        try:
            # Test database connection
            client_db.session.execute('SELECT 1')
            db_status = "healthy"
        except Exception as e:
            db_status = f"unhealthy: {str(e)}"
            
        return jsonify({
            "status": "healthy",
            "service": "LEED.io Lead Generation API",
            "version": "1.0.0",
            "database": db_status,
            "environment": os.getenv('FLASK_ENV', 'development')
        })
    
    # Root endpoint
    @app.route('/')
    def root():
        """Root endpoint"""
        return jsonify({
            "message": "LEED.io Lead Generation API",
            "version": "1.0.0",
            "status": "running",
            "endpoints": {
                "health": "/api/health",
                "auth": "/api/auth/*",
                "leads": "/api/leads/*",
                "campaigns": "/api/campaigns/*"
            }
        })
    
    # Create tables
    with app.app_context():
        try:
            client_db.create_all()
            app.logger.info("Database tables created successfully")
        except Exception as e:
            app.logger.error(f"Database initialization failed: {e}")
    
    return app

# Create the app instance
app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)

