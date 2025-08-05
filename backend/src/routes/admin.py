from flask import Blueprint, request, jsonify, current_app
from flask_cors import cross_origin
import jwt
from datetime import datetime, timedelta
import logging
from functools import wraps

from models.client import Client, AdminUser, db

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    """Decorator to require admin authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'error': 'Authorization token is required'}), 401
        
        try:
            # Remove 'Bearer ' prefix if present
            if token.startswith('Bearer '):
                token = token[7:]
            
            # Decode token
            payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            
            # Check if it's an admin token
            if 'admin_id' not in payload:
                return jsonify({'error': 'Admin access required'}), 403
            
            # Verify admin exists and is active
            admin = AdminUser.query.get(payload['admin_id'])
            if not admin or not admin.is_active:
                return jsonify({'error': 'Invalid admin account'}), 401
            
            # Add admin to request context
            request.admin = admin
            
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        except Exception as e:
            logger.error(f"Admin authentication error: {str(e)}")
            return jsonify({'error': 'Authentication failed'}), 401
        
        return f(*args, **kwargs)
    
    return decorated_function

@admin_bp.route('/admin/clients', methods=['GET'])
@cross_origin()
@admin_required
def get_clients():
    """
    Get all clients with pagination and filtering
    
    Query parameters:
    - page: Page number (default: 1)
    - per_page: Items per page (default: 10, max: 100)
    - status: Filter by status (active, suspended, cancelled)
    - plan: Filter by plan (starter, professional, enterprise)
    - search: Search by company name or email
    """
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 100)
        status_filter = request.args.get('status')
        plan_filter = request.args.get('plan')
        search_query = request.args.get('search', '').strip()
        
        # Build query
        query = Client.query
        
        # Apply filters
        if status_filter:
            query = query.filter(Client.status == status_filter)
        
        if plan_filter:
            query = query.filter(Client.plan == plan_filter)
        
        if search_query:
            query = query.filter(
                db.or_(
                    Client.company_name.ilike(f'%{search_query}%'),
                    Client.email.ilike(f'%{search_query}%'),
                    Client.contact_name.ilike(f'%{search_query}%')
                )
            )
        
        # Order by creation date (newest first)
        query = query.order_by(Client.created_at.desc())
        
        # Paginate
        pagination = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        clients = pagination.items
        
        # Calculate stats
        total_clients = Client.query.count()
        active_clients = Client.query.filter_by(status='active').count()
        total_leads = db.session.query(db.func.sum(Client.api_usage_current)).scalar() or 0
        
        return jsonify({
            'success': True,
            'clients': [client.to_dict() for client in clients],
            'pagination': {
                'page': pagination.page,
                'pages': pagination.pages,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            },
            'stats': {
                'total_clients': total_clients,
                'active_clients': active_clients,
                'total_leads': total_leads
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get clients error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve clients',
            'message': str(e)
        }), 500

@admin_bp.route('/admin/clients', methods=['POST'])
@cross_origin()
@admin_required
def create_client():
    """
    Create a new client account
    
    Expected JSON payload:
    {
        "email": "client@example.com",
        "password": "password123",
        "company_name": "Example Corp",
        "contact_name": "John Doe",
        "phone": "+61 400 000 000",
        "industry": "Technology",
        "plan": "professional",
        "api_quota_monthly": 5000
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['email', 'password', 'company_name', 'contact_name']
        for field in required_fields:
            if not data.get(field, '').strip():
                return jsonify({'error': f'{field.replace("_", " ").title()} is required'}), 400
        
        email = data['email'].strip().lower()
        
        # Check if client already exists
        existing_client = Client.query.filter_by(email=email).first()
        if existing_client:
            return jsonify({'error': 'Email already registered'}), 409
        
        # Validate plan
        valid_plans = ['starter', 'professional', 'enterprise']
        plan = data.get('plan', 'starter').lower()
        if plan not in valid_plans:
            return jsonify({'error': f'Invalid plan. Must be one of: {", ".join(valid_plans)}'}), 400
        
        # Set default API quota based on plan
        quota_defaults = {
            'starter': 1000,
            'professional': 5000,
            'enterprise': 20000
        }
        api_quota = data.get('api_quota_monthly', quota_defaults[plan])
        
        # Create new client
        client = Client(
            email=email,
            company_name=data['company_name'].strip(),
            contact_name=data['contact_name'].strip(),
            phone=data.get('phone', '').strip(),
            industry=data.get('industry', '').strip(),
            plan=plan,
            status='active',
            api_quota_monthly=api_quota
        )
        
        client.set_password(data['password'])
        
        db.session.add(client)
        db.session.commit()
        
        logger.info(f"Admin {request.admin.email} created new client: {email}")
        
        return jsonify({
            'success': True,
            'message': 'Client created successfully',
            'client': client.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Create client error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to create client',
            'message': str(e)
        }), 500

@admin_bp.route('/admin/clients/<client_id>', methods=['GET'])
@cross_origin()
@admin_required
def get_client(client_id):
    """Get a specific client by ID"""
    try:
        client = Client.query.get(client_id)
        
        if not client:
            return jsonify({'error': 'Client not found'}), 404
        
        # Get additional stats for this client
        from models.lead_model import Lead, Campaign
        
        lead_count = Lead.query.filter_by(client_id=client_id).count()
        campaign_count = Campaign.query.filter_by(client_id=client_id).count()
        
        client_data = client.to_dict()
        client_data['stats'] = {
            'total_leads': lead_count,
            'total_campaigns': campaign_count
        }
        
        return jsonify({
            'success': True,
            'client': client_data
        }), 200
        
    except Exception as e:
        logger.error(f"Get client error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve client',
            'message': str(e)
        }), 500

@admin_bp.route('/admin/clients/<client_id>', methods=['PUT'])
@cross_origin()
@admin_required
def update_client(client_id):
    """
    Update a client account
    
    Expected JSON payload:
    {
        "company_name": "Updated Corp",
        "contact_name": "Jane Doe",
        "phone": "+61 400 000 001",
        "industry": "Healthcare",
        "plan": "enterprise",
        "status": "active",
        "api_quota_monthly": 10000
    }
    """
    try:
        client = Client.query.get(client_id)
        
        if not client:
            return jsonify({'error': 'Client not found'}), 404
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update allowed fields
        updatable_fields = [
            'company_name', 'contact_name', 'phone', 'industry', 
            'plan', 'status', 'api_quota_monthly'
        ]
        
        for field in updatable_fields:
            if field in data:
                if field == 'plan':
                    valid_plans = ['starter', 'professional', 'enterprise']
                    if data[field].lower() not in valid_plans:
                        return jsonify({'error': f'Invalid plan. Must be one of: {", ".join(valid_plans)}'}), 400
                    setattr(client, field, data[field].lower())
                elif field == 'status':
                    valid_statuses = ['active', 'suspended', 'cancelled']
                    if data[field].lower() not in valid_statuses:
                        return jsonify({'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'}), 400
                    setattr(client, field, data[field].lower())
                else:
                    setattr(client, field, data[field])
        
        client.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"Admin {request.admin.email} updated client: {client.email}")
        
        return jsonify({
            'success': True,
            'message': 'Client updated successfully',
            'client': client.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Update client error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to update client',
            'message': str(e)
        }), 500

@admin_bp.route('/admin/clients/<client_id>', methods=['DELETE'])
@cross_origin()
@admin_required
def delete_client(client_id):
    """Delete a client account (soft delete by setting status to cancelled)"""
    try:
        client = Client.query.get(client_id)
        
        if not client:
            return jsonify({'error': 'Client not found'}), 404
        
        # Soft delete by setting status to cancelled
        client.status = 'cancelled'
        client.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"Admin {request.admin.email} deleted client: {client.email}")
        
        return jsonify({
            'success': True,
            'message': 'Client deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Delete client error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to delete client',
            'message': str(e)
        }), 500

@admin_bp.route('/admin/clients/<client_id>/reset-password', methods=['POST'])
@cross_origin()
@admin_required
def reset_client_password(client_id):
    """
    Reset a client's password
    
    Expected JSON payload:
    {
        "new_password": "newpassword123"
    }
    """
    try:
        client = Client.query.get(client_id)
        
        if not client:
            return jsonify({'error': 'Client not found'}), 404
        
        data = request.get_json()
        
        if not data or not data.get('new_password'):
            return jsonify({'error': 'New password is required'}), 400
        
        new_password = data['new_password'].strip()
        
        if len(new_password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters long'}), 400
        
        client.set_password(new_password)
        client.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"Admin {request.admin.email} reset password for client: {client.email}")
        
        return jsonify({
            'success': True,
            'message': 'Password reset successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Reset password error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to reset password',
            'message': str(e)
        }), 500

@admin_bp.route('/admin/stats', methods=['GET'])
@cross_origin()
@admin_required
def get_admin_stats():
    """Get comprehensive admin dashboard statistics"""
    try:
        # Client statistics
        total_clients = Client.query.count()
        active_clients = Client.query.filter_by(status='active').count()
        suspended_clients = Client.query.filter_by(status='suspended').count()
        cancelled_clients = Client.query.filter_by(status='cancelled').count()
        
        # Plan distribution
        starter_clients = Client.query.filter_by(plan='starter').count()
        professional_clients = Client.query.filter_by(plan='professional').count()
        enterprise_clients = Client.query.filter_by(plan='enterprise').count()
        
        # API usage statistics
        total_api_usage = db.session.query(db.func.sum(Client.api_usage_current)).scalar() or 0
        total_api_quota = db.session.query(db.func.sum(Client.api_quota_monthly)).scalar() or 0
        
        # Recent activity (clients created in last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        new_clients_30d = Client.query.filter(Client.created_at >= thirty_days_ago).count()
        
        # Revenue estimation (simplified)
        plan_prices = {'starter': 29, 'professional': 99, 'enterprise': 299}
        estimated_revenue = (
            starter_clients * plan_prices['starter'] +
            professional_clients * plan_prices['professional'] +
            enterprise_clients * plan_prices['enterprise']
        )
        
        return jsonify({
            'success': True,
            'stats': {
                'clients': {
                    'total': total_clients,
                    'active': active_clients,
                    'suspended': suspended_clients,
                    'cancelled': cancelled_clients,
                    'new_30d': new_clients_30d
                },
                'plans': {
                    'starter': starter_clients,
                    'professional': professional_clients,
                    'enterprise': enterprise_clients
                },
                'api_usage': {
                    'total_usage': total_api_usage,
                    'total_quota': total_api_quota,
                    'usage_percentage': round((total_api_usage / total_api_quota * 100) if total_api_quota > 0 else 0, 2)
                },
                'revenue': {
                    'estimated_monthly': estimated_revenue
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get admin stats error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve statistics',
            'message': str(e)
        }), 500

@admin_bp.route('/admin/init', methods=['POST'])
@cross_origin()
def init_admin():
    """
    Initialize the first admin user (only works if no admin users exist)
    
    Expected JSON payload:
    {
        "email": "admin@salesfuel.au",
        "password": "admin123",
        "name": "System Administrator"
    }
    """
    try:
        # Check if any admin users already exist
        existing_admin = AdminUser.query.first()
        if existing_admin:
            return jsonify({'error': 'Admin users already exist. Use regular admin endpoints.'}), 409
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['email', 'password', 'name']
        for field in required_fields:
            if not data.get(field, '').strip():
                return jsonify({'error': f'{field.title()} is required'}), 400
        
        email = data['email'].strip().lower()
        
        # Create first admin user
        admin = AdminUser(
            email=email,
            name=data['name'].strip(),
            role='super_admin',
            is_active=True
        )
        
        admin.set_password(data['password'])
        
        db.session.add(admin)
        db.session.commit()
        
        logger.info(f"First admin user created: {email}")
        
        return jsonify({
            'success': True,
            'message': 'Admin user created successfully',
            'admin': admin.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Init admin error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to create admin user',
            'message': str(e)
        }), 500

