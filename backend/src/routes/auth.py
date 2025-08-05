from flask import Blueprint, request, jsonify, current_app
from flask_cors import cross_origin
import jwt
from datetime import datetime, timedelta
import logging

from models.client import Client, AdminUser, db

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
@cross_origin()
def login():
    """
    Client login endpoint
    
    Expected JSON payload:
    {
        "email": "client@example.com",
        "password": "password123"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Find client by email
        client = Client.query.filter_by(email=email).first()
        
        if not client or not client.check_password(password):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        if client.status != 'active':
            return jsonify({'error': 'Account is not active'}), 401
        
        # Update last login
        client.last_login = datetime.utcnow()
        db.session.commit()
        
        # Generate JWT token
        token_payload = {
            'client_id': client.id,
            'email': client.email,
            'exp': datetime.utcnow() + timedelta(hours=24),
            'iat': datetime.utcnow()
        }
        
        token = jwt.encode(token_payload, current_app.config['SECRET_KEY'], algorithm='HS256')
        
        logger.info(f"Client {email} logged in successfully")
        
        return jsonify({
            'success': True,
            'token': token,
            'client': client.to_dict(),
            'expires_in': 24 * 3600  # 24 hours in seconds
        }), 200
        
    except Exception as e:
        logger.error(f"Login endpoint error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@auth_bp.route('/admin/login', methods=['POST'])
@cross_origin()
def admin_login():
    """
    Admin login endpoint
    
    Expected JSON payload:
    {
        "email": "admin@livewire.com",
        "password": "admin123"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Find admin by email
        admin = AdminUser.query.filter_by(email=email).first()
        
        if not admin or not admin.check_password(password):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        if not admin.is_active:
            return jsonify({'error': 'Admin account is not active'}), 401
        
        # Update last login
        admin.last_login = datetime.utcnow()
        db.session.commit()
        
        # Generate JWT token
        token_payload = {
            'admin_id': admin.id,
            'email': admin.email,
            'role': admin.role,
            'exp': datetime.utcnow() + timedelta(hours=8),  # Shorter expiry for admin
            'iat': datetime.utcnow()
        }
        
        token = jwt.encode(token_payload, current_app.config['SECRET_KEY'], algorithm='HS256')
        
        logger.info(f"Admin {email} logged in successfully")
        
        return jsonify({
            'success': True,
            'token': token,
            'admin': admin.to_dict(),
            'expires_in': 8 * 3600  # 8 hours in seconds
        }), 200
        
    except Exception as e:
        logger.error(f"Admin login endpoint error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@auth_bp.route('/register', methods=['POST'])
@cross_origin()
def register():
    """
    Client registration endpoint (for demo purposes)
    
    Expected JSON payload:
    {
        "email": "client@example.com",
        "password": "password123",
        "company_name": "Example Corp",
        "contact_name": "John Doe",
        "phone": "+61 400 000 000",
        "industry": "Technology"
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
        
        # Create new client
        client = Client(
            email=email,
            company_name=data['company_name'].strip(),
            contact_name=data['contact_name'].strip(),
            phone=data.get('phone', '').strip(),
            industry=data.get('industry', '').strip(),
            plan='starter',  # Default plan
            status='active'
        )
        
        client.set_password(data['password'])
        
        db.session.add(client)
        db.session.commit()
        
        logger.info(f"New client registered: {email}")
        
        # Generate JWT token for immediate login
        token_payload = {
            'client_id': client.id,
            'email': client.email,
            'exp': datetime.utcnow() + timedelta(hours=24),
            'iat': datetime.utcnow()
        }
        
        token = jwt.encode(token_payload, current_app.config['SECRET_KEY'], algorithm='HS256')
        
        return jsonify({
            'success': True,
            'message': 'Registration successful',
            'token': token,
            'client': client.to_dict(),
            'expires_in': 24 * 3600
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Registration endpoint error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@auth_bp.route('/verify-token', methods=['POST'])
@cross_origin()
def verify_token():
    """
    Verify JWT token validity
    
    Expected JSON payload:
    {
        "token": "jwt_token_here"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'token' not in data:
            return jsonify({'error': 'Token is required'}), 400
        
        token = data['token']
        
        try:
            # Decode token
            payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            
            # Check if it's a client or admin token
            if 'client_id' in payload:
                client = Client.query.get(payload['client_id'])
                if not client or client.status != 'active':
                    return jsonify({'error': 'Invalid client'}), 401
                
                return jsonify({
                    'success': True,
                    'valid': True,
                    'type': 'client',
                    'client': client.to_dict(),
                    'expires_at': payload['exp']
                }), 200
            
            elif 'admin_id' in payload:
                admin = AdminUser.query.get(payload['admin_id'])
                if not admin or not admin.is_active:
                    return jsonify({'error': 'Invalid admin'}), 401
                
                return jsonify({
                    'success': True,
                    'valid': True,
                    'type': 'admin',
                    'admin': admin.to_dict(),
                    'expires_at': payload['exp']
                }), 200
            
            else:
                return jsonify({'error': 'Invalid token format'}), 401
                
        except jwt.ExpiredSignatureError:
            return jsonify({
                'success': True,
                'valid': False,
                'error': 'Token has expired'
            }), 200
            
        except jwt.InvalidTokenError:
            return jsonify({
                'success': True,
                'valid': False,
                'error': 'Invalid token'
            }), 200
        
    except Exception as e:
        logger.error(f"Verify token endpoint error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@auth_bp.route('/refresh-token', methods=['POST'])
@cross_origin()
def refresh_token():
    """
    Refresh JWT token
    
    Expected JSON payload:
    {
        "token": "current_jwt_token"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'token' not in data:
            return jsonify({'error': 'Token is required'}), 400
        
        token = data['token']
        
        try:
            # Decode token (allow expired tokens for refresh)
            payload = jwt.decode(
                token, 
                current_app.config['SECRET_KEY'], 
                algorithms=['HS256'],
                options={"verify_exp": False}  # Allow expired tokens
            )
            
            # Check if token is not too old (max 7 days)
            issued_at = datetime.fromtimestamp(payload['iat'])
            if datetime.utcnow() - issued_at > timedelta(days=7):
                return jsonify({'error': 'Token is too old to refresh'}), 401
            
            # Generate new token
            if 'client_id' in payload:
                client = Client.query.get(payload['client_id'])
                if not client or client.status != 'active':
                    return jsonify({'error': 'Invalid client'}), 401
                
                new_token_payload = {
                    'client_id': client.id,
                    'email': client.email,
                    'exp': datetime.utcnow() + timedelta(hours=24),
                    'iat': datetime.utcnow()
                }
                
                new_token = jwt.encode(new_token_payload, current_app.config['SECRET_KEY'], algorithm='HS256')
                
                return jsonify({
                    'success': True,
                    'token': new_token,
                    'client': client.to_dict(),
                    'expires_in': 24 * 3600
                }), 200
            
            elif 'admin_id' in payload:
                admin = AdminUser.query.get(payload['admin_id'])
                if not admin or not admin.is_active:
                    return jsonify({'error': 'Invalid admin'}), 401
                
                new_token_payload = {
                    'admin_id': admin.id,
                    'email': admin.email,
                    'role': admin.role,
                    'exp': datetime.utcnow() + timedelta(hours=8),
                    'iat': datetime.utcnow()
                }
                
                new_token = jwt.encode(new_token_payload, current_app.config['SECRET_KEY'], algorithm='HS256')
                
                return jsonify({
                    'success': True,
                    'token': new_token,
                    'admin': admin.to_dict(),
                    'expires_in': 8 * 3600
                }), 200
            
            else:
                return jsonify({'error': 'Invalid token format'}), 401
                
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        
    except Exception as e:
        logger.error(f"Refresh token endpoint error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@auth_bp.route('/logout', methods=['POST'])
@cross_origin()
def logout():
    """
    Logout endpoint (client-side token removal)
    """
    # In a stateless JWT system, logout is handled client-side by removing the token
    # For enhanced security, you could implement a token blacklist here
    
    return jsonify({
        'success': True,
        'message': 'Logged out successfully'
    }), 200

