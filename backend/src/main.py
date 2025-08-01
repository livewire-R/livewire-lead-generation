import os
import sys
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect

# Add the src directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Configuration
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "leed-io-production-secret-2025-change-this")
    
    # Database configuration
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        # Railway provides DATABASE_URL, but we need to handle postgres:// vs postgresql://
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        app.config["SQLALCHEMY_DATABASE_URI"] = database_url
        logger.info("Using PostgreSQL database from Railway")
    else:
        # Fallback for local development
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///leed_io.db"
        logger.info("Using SQLite database for local development")
    
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_timeout": 20,
        "max_overflow": 0
    }
    
    # CORS configuration
    cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000" ).split(",")
    CORS(app, origins=cors_origins, supports_credentials=True)
    
    # Initialize database
    from models.client import db
    db.init_app(app)
    
    # Import and register blueprints
    try:
        from src.routes.auth import auth_bp
        from src.routes.leads import leads_bp
        from src.routes.campaigns import campaigns_bp
        
        app.register_blueprint(auth_bp, url_prefix="/api")
        app.register_blueprint(leads_bp, url_prefix="/api")
        app.register_blueprint(campaigns_bp, url_prefix="/api")
        logger.info("Blueprints registered successfully")
    except ImportError as e:
        logger.warning(f"Could not import blueprints: {e}")
    
    # Initialize campaign scheduler
    try:
        from src.services.campaign_scheduler import init_campaign_scheduler
        init_campaign_scheduler(app)
        logger.info("Campaign scheduler initialized")
    except Exception as e:
        logger.warning(f"Campaign scheduler initialization failed: {e}")
    
    # Health check endpoint
    @app.route("/api/health")
    def health_check():
        """Health check endpoint for Railway deployment"""
        try:
            # Test database connection only if DATABASE_URL exists
            if os.getenv("DATABASE_URL"):
                db.session.execute("SELECT 1")
                db_status = "healthy"
            else:
                db_status = "no database configured"
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            db_status = f"unhealthy: {str(e)}"
            
        return jsonify({
            "status": "healthy",
            "service": "LEED.io Lead Generation API",
            "version": "1.0.0",
            "database": db_status,
            "environment": os.getenv("FLASK_ENV", "development"),
            "port": os.getenv("PORT", "not set")
        })
    
    # Root endpoint
    @app.route("/")
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
    
    # Debug endpoint (remove in production)
    @app.route("/api/debug")
    def debug_info():
        """Debug endpoint to check environment"""
        return jsonify({
            "environment_variables": {
                "DATABASE_URL": "***" if os.getenv("DATABASE_URL") else "MISSING",
                "SECRET_KEY": "***" if os.getenv("SECRET_KEY") else "MISSING",
                "PORT": os.getenv("PORT", "MISSING"),
                "FLASK_ENV": os.getenv("FLASK_ENV", "MISSING"),
                "PYTHONPATH": os.getenv("PYTHONPATH", "MISSING")
            },
            "python_path": sys.path[:3],  # First 3 entries
            "working_directory": os.getcwd(),
            "app_config": {
                "SECRET_KEY": "***" if app.config.get("SECRET_KEY") else "MISSING",
                "SQLALCHEMY_DATABASE_URI": "***" if app.config.get("SQLALCHEMY_DATABASE_URI") else "MISSING"
            }
        })
    
    # Create tables
    with app.app_context():
        try:
              # Check if tables already exist before creating
            if not inspect(db.engine).has_table("clients"):
                db.create_all()
                logger.info("Database tables created successfully")
            else:
                logger.info("Database tables already exist, skipping creation")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
    
    return app

# Create the app instance
app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_ENV") == "development"
    logger.info(f"Starting LEED.io API on port {port}")
    app.run(host="0.0.0.0", port=port, debug=debug)
