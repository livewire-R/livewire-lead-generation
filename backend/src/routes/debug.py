from flask import Blueprint, request, jsonify, current_app
from flask_cors import cross_origin
import jwt
from functools import wraps
import logging
import requests
import os
from datetime import datetime

logger = logging.getLogger(__name__)

debug_bp = Blueprint('debug', __name__)

def admin_required(f):
    """Decorator to require admin JWT token for debug routes"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            
            # Check if it's an admin token
            if 'admin_id' not in data:
                return jsonify({'error': 'Admin access required'}), 403
            
            return f(*args, **kwargs)
            
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
    
    return decorated

@debug_bp.route('/apollo', methods=['GET'])
@cross_origin()
@admin_required
def debug_apollo():
    """Debug Apollo.io API configuration and connectivity"""
    try:
        api_key = os.getenv('APOLLO_API_KEY')
        
        if not api_key:
            return jsonify({
                'success': False,
                'error': 'APOLLO_API_KEY environment variable not set',
                'api_key_present': False
            }), 500
        
        # Test 1: Basic API connectivity
        base_url = "https://api.apollo.io/v1"
        
        # Test minimal payload
        minimal_payload = {
            "api_key": api_key,
            "per_page": 1
        }
        
        try:
            response = requests.post(f"{base_url}/mixed_people/search", 
                                   json=minimal_payload, timeout=30)
            
            result = {
                'success': True,
                'api_key_present': True,
                'api_key_length': len(api_key),
                'api_key_prefix': api_key[:8] + "..." if len(api_key) > 8 else api_key,
                'test_results': {
                    'minimal_payload': {
                        'status_code': response.status_code,
                        'headers': dict(response.headers),
                        'response_preview': response.text[:500] if response.text else None
                    }
                }
            }
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    result['test_results']['minimal_payload']['people_count'] = len(data.get('people', []))
                    result['test_results']['minimal_payload']['success'] = True
                except:
                    result['test_results']['minimal_payload']['json_parse_error'] = True
            
            # Test 2: With keywords
            keyword_payload = {
                "api_key": api_key,
                "q_keywords": "CEO",
                "per_page": 1
            }
            
            response2 = requests.post(f"{base_url}/mixed_people/search", 
                                    json=keyword_payload, timeout=30)
            
            result['test_results']['with_keywords'] = {
                'status_code': response2.status_code,
                'response_preview': response2.text[:300] if response2.text else None
            }
            
            # Test 3: With location
            location_payload = {
                "api_key": api_key,
                "person_locations": ["Australia"],
                "per_page": 1
            }
            
            response3 = requests.post(f"{base_url}/mixed_people/search", 
                                    json=location_payload, timeout=30)
            
            result['test_results']['with_location'] = {
                'status_code': response3.status_code,
                'response_preview': response3.text[:300] if response3.text else None
            }
            
            return jsonify(result), 200
            
        except requests.exceptions.RequestException as e:
            return jsonify({
                'success': False,
                'error': f'Apollo API request failed: {str(e)}',
                'api_key_present': True,
                'api_key_length': len(api_key)
            }), 500
            
    except Exception as e:
        logger.error(f"Debug Apollo endpoint error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Debug endpoint error: {str(e)}'
        }), 500

@debug_bp.route('/environment', methods=['GET'])
@cross_origin()
@admin_required
def debug_environment():
    """Debug environment variables and configuration"""
    try:
        env_vars = {
            'APOLLO_API_KEY': 'SET' if os.getenv('APOLLO_API_KEY') else 'NOT SET',
            'HUNTER_API_KEY': 'SET' if os.getenv('HUNTER_API_KEY') else 'NOT SET',
            'LINKEDIN_API_KEY': 'SET' if os.getenv('LINKEDIN_API_KEY') else 'NOT SET',
            'DATABASE_URL': 'SET' if os.getenv('DATABASE_URL') else 'NOT SET',
            'SECRET_KEY': 'SET' if os.getenv('SECRET_KEY') else 'NOT SET',
            'CORS_ORIGINS': os.getenv('CORS_ORIGINS', 'NOT SET'),
            'FLASK_ENV': os.getenv('FLASK_ENV', 'NOT SET'),
            'PORT': os.getenv('PORT', 'NOT SET')
        }
        
        # Get API key details without exposing the actual keys
        api_key_details = {}
        for key_name in ['APOLLO_API_KEY', 'HUNTER_API_KEY', 'LINKEDIN_API_KEY']:
            key_value = os.getenv(key_name)
            if key_value:
                api_key_details[key_name] = {
                    'length': len(key_value),
                    'prefix': key_value[:8] + "..." if len(key_value) > 8 else key_value,
                    'has_special_chars': any(c in key_value for c in ['!', '@', '#', '$', '%', '^', '&', '*'])
                }
        
        return jsonify({
            'success': True,
            'environment_variables': env_vars,
            'api_key_details': api_key_details,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Debug environment endpoint error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Debug endpoint error: {str(e)}'
        }), 500

@debug_bp.route('/test-lead-generation', methods=['POST'])
@cross_origin()
@admin_required
def debug_test_lead_generation():
    """Test lead generation with detailed debugging"""
    try:
        data = request.get_json() or {}
        
        # Import here to avoid circular imports
        from services.apollo_client import get_apollo_client
        from services.lead_generator import LeadCriteria
        
        # Create test criteria
        criteria = LeadCriteria(
            keywords=data.get('keywords', ''),
            industries=data.get('industries', []),
            locations=data.get('locations', ['Australia']),
            titles=data.get('titles', []),
            company_sizes=data.get('company_sizes', []),
            min_score=data.get('min_score', 60),
            max_results=data.get('max_results', 1),
            verify_emails=False,  # Skip email verification for debug
            enrich_linkedin=False  # Skip LinkedIn enrichment for debug
        )
        
        # Test Apollo client directly
        apollo_client = get_apollo_client()
        
        # Prepare criteria
        apollo_criteria = {
            'per_page': 1
        }
        
        if criteria.keywords and criteria.keywords.strip():
            apollo_criteria['keywords'] = criteria.keywords.strip()
        
        if criteria.locations:
            apollo_criteria['locations'] = criteria.locations
        
        result = {
            'success': True,
            'test_criteria': {
                'keywords': criteria.keywords,
                'locations': criteria.locations,
                'industries': criteria.industries,
                'titles': criteria.titles
            },
            'apollo_criteria': apollo_criteria
        }
        
        try:
            # Test Apollo search
            leads = apollo_client.search_people(apollo_criteria)
            result['apollo_test'] = {
                'success': True,
                'leads_found': len(leads),
                'sample_lead': leads[0] if leads else None
            }
        except Exception as apollo_error:
            result['apollo_test'] = {
                'success': False,
                'error': str(apollo_error)
            }
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Debug test lead generation error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Debug test error: {str(e)}'
        }), 500

