import os
import sys
import logging
from datetime import datetime

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import models and routes
from src.models.client import db as client_db, Client, AdminUser
from src.models.lead import Lead, Campaign
from src.routes.auth import auth_bp
from .routes.campaigns import campaigns_bp
from .services.campaign_scheduler import init_campaign_scheduler_bp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
    
    # Database configuration - PostgreSQL for Railway
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        # Railway provides DATABASE_URL, use it directly
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        # Fallback to SQLite for local development
        app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # CORS configuration
    cors_origins = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://localhost:5173').split(',')
    CORS(app, origins=cors_origins, supports_credentials=True)
    
    # Initialize database
    client_db.init_app(app)
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(leads_bp, url_prefix='/api')
    app.register_blueprint(campaigns_bp, url_prefix='/api')
    
    # Initialize campaign scheduler
    init_campaign_scheduler(app)
    
    # Health check endpoint
    @app.route('/api/health')
    def health_check():
        """Health check endpoint for Railway deployment"""
        try:
            # Test database connection
            client_db.session.execute('SELECT 1')
            db_status = 'healthy'
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            db_status = 'unhealthy'
        
        return jsonify({
            'status': 'healthy' if db_status == 'healthy' else 'unhealthy',
            'service': 'LiveWire Lead Generation API',
            'version': '2.0.0',
            'timestamp': datetime.utcnow().isoformat(),
            'database': db_status,
            'environment': os.getenv('FLASK_ENV', 'production')
        }), 200 if db_status == 'healthy' else 503
    
    # API status endpoint
    @app.route('/api/status')
    def api_status():
        """API status endpoint with service information"""
        return jsonify({
            'success': True,
            'service': 'LiveWire Lead Generation API',
            'version': '2.0.0',
            'description': 'AI-Powered Lead Generation for Australian B2B Consultants',
            'features': {
                'lead_generation': True,
                'apollo_integration': bool(os.getenv('APOLLO_API_KEY')),
                'hunter_integration': bool(os.getenv('HUNTER_API_KEY')),
                'linkedin_integration': bool(os.getenv('LINKEDIN_CLIENT_ID')),
                'email_verification': True,
                'ai_scoring': True,
                'australian_compliance': True
            },
            'endpoints': {
                'auth': '/api/auth',
                'leads': '/api/leads',
                'health': '/api/health'
            }
        }), 200
    
    # Serve React frontend
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_frontend(path):
        """Serve React frontend from static folder"""
        static_folder_path = app.static_folder
        if static_folder_path is None:
            return jsonify({'error': 'Frontend not configured'}), 404

        if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
            return send_from_directory(static_folder_path, path)
        else:
            index_path = os.path.join(static_folder_path, 'index.html')
            if os.path.exists(index_path):
                return send_from_directory(static_folder_path, 'index.html')
            else:
                return jsonify({
                    'message': 'LiveWire Lead Generation API',
                    'version': '2.0.0',
                    'status': 'running',
                    'frontend': 'not_deployed',
                    'api_docs': '/api/status'
                }), 200
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Endpoint not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {str(error)}")
        return jsonify({'error': 'Internal server error'}), 500
    
    # Create database tables and sample data
    with app.app_context():
        try:
            client_db.create_all()
            create_sample_data()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}")
    
    return app

def create_sample_data():
    """Create sample data for demo purposes"""
    try:
        # Check if demo client already exists
        demo_client = Client.query.filter_by(email='demo@livewire.com').first()
        if not demo_client:
            demo_client = Client(
                email='demo@livewire.com',
                company_name='Demo Consulting Pty Ltd',
                contact_name='Demo User',
                phone='+61 400 000 000',
                industry='Business Consulting',
                plan='professional',
                status='active',
                api_quota_monthly=2000,
                api_usage_current=150
            )
            demo_client.set_password('demo123')
            client_db.session.add(demo_client)
        
        # Check if admin user already exists
        admin_user = AdminUser.query.filter_by(email='admin@livewire.com').first()
        if not admin_user:
            admin_user = AdminUser(
                email='admin@livewire.com',
                name='LiveWire Admin',
                role='super_admin',
                is_active=True
            )
            admin_user.set_password('admin123')
            client_db.session.add(admin_user)
        
        client_db.session.commit()
        logger.info("Sample data created successfully")
        
    except Exception as e:
        client_db.session.rollback()
        logger.error(f"Failed to create sample data: {str(e)}")

# Create Flask app
app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    host = os.getenv('HOST', '0.0.0.0')
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting LiveWire API server on {host}:{port}")
    logger.info(f"Debug mode: {debug}")
    logger.info(f"Database: {'PostgreSQL (Railway)' if os.getenv('DATABASE_URL') else 'SQLite (Local)'}")
    
    app.run(host=host, port=port, debug=debug)

