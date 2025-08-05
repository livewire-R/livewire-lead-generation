"""
Database initialization routes for SalesFuel.au platform
"""

from flask import Blueprint, jsonify, request
from models.client import db, Client, AdminUser
from models.lead_model import Lead
from models.campaign import Campaign
from sqlalchemy import inspect
import logging

logger = logging.getLogger(__name__)

database_bp = Blueprint('database', __name__)

@database_bp.route('/admin/init-database', methods=['POST'])
def initialize_database():
    """Initialize database tables - Admin only endpoint"""
    try:
        # Check if admin is authenticated (basic check)
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({
                'error': 'Authentication required',
                'success': False
            }), 401
        
        # Create all tables
        db.create_all()
        
        # Verify tables were created
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        # Check for required tables
        required_tables = ['clients', 'admins', 'leads', 'campaigns']
        missing_tables = [table for table in required_tables if table not in tables]
        
        if missing_tables:
            return jsonify({
                'error': f'Failed to create tables: {missing_tables}',
                'created_tables': tables,
                'success': False
            }), 500
        
        logger.info(f"Database tables initialized successfully: {tables}")
        
        return jsonify({
            'message': 'Database tables initialized successfully',
            'created_tables': tables,
            'required_tables': required_tables,
            'success': True
        }), 200
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return jsonify({
            'error': 'Database initialization failed',
            'message': str(e),
            'success': False
        }), 500

@database_bp.route('/admin/database-status', methods=['GET'])
def database_status():
    """Check database status and table existence"""
    try:
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        required_tables = ['clients', 'admins', 'leads', 'campaigns']
        table_status = {}
        
        for table in required_tables:
            table_status[table] = {
                'exists': table in tables,
                'columns': inspector.get_columns(table) if table in tables else []
            }
        
        return jsonify({
            'database_status': 'connected',
            'all_tables': tables,
            'table_status': table_status,
            'success': True
        }), 200
        
    except Exception as e:
        logger.error(f"Database status check failed: {e}")
        return jsonify({
            'error': 'Database status check failed',
            'message': str(e),
            'success': False
        }), 500

