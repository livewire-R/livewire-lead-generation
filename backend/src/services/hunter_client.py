import requests
import time
import logging
from typing import Dict, List, Optional
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class HunterAPIClient:
    """Hunter.io API client for email verification and domain search"""
    
    def __init__(self):
        self.api_key = os.getenv('HUNTER_API_KEY')
        if not self.api_key:
            raise ValueError("HUNTER_API_KEY environment variable is required")
        
        self.base_url = "https://api.hunter.io/v2"
        self.session = requests.Session()
        
        # Rate limiting configuration
        self.last_request_time = 0
        self.min_request_interval = 0.2  # 5 requests per second max
        self.monthly_quota = 5000  # Adjust based on your Hunter plan
        self.requests_made_this_month = 0
    
    def _rate_limit(self):
        """Implement rate limiting to avoid API throttling"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            logger.info(f"Hunter rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _make_request(self, endpoint: str, params: Dict) -> Dict:
        """Make authenticated request to Hunter API"""
        self._rate_limit()
        
        url = f"{self.base_url}/{endpoint}"
        params['api_key'] = self.api_key
        
        try:
            logger.info(f"Making Hunter API request to {endpoint}")
            response = self.session.get(url, params=params, timeout=15)
            
            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                logger.warning(f"Rate limited by Hunter API, waiting {retry_after} seconds")
                time.sleep(retry_after)
                return self._make_request(endpoint, params)
            
            response.raise_for_status()
            data = response.json()
            
            # Track API usage
            self.requests_made_this_month += 1
            
            logger.info(f"Hunter API request successful")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Hunter API request failed: {str(e)}")
            raise HunterAPIError(f"API request failed: {str(e)}")
    
    def verify_email(self, email: str) -> Dict:
        """
        Verify email address using Hunter.io
        
        Args:
            email: Email address to verify
        
        Returns:
            Dictionary with verification results
        """
        params = {'email': email}
        
        try:
            data = self._make_request('email-verifier', params)
            verification_data = data.get('data', {})
            
            result = {
                'email': email,
                'status': verification_data.get('status'),
                'result': verification_data.get('result'),
                'score': verification_data.get('score', 0),
                'regexp': verification_data.get('regexp'),
                'gibberish': verification_data.get('gibberish'),
                'disposable': verification_data.get('disposable'),
                'webmail': verification_data.get('webmail'),
                'mx_records': verification_data.get('mx_records'),
                'smtp_server': verification_data.get('smtp_server'),
                'smtp_check': verification_data.get('smtp_check'),
                'accept_all': verification_data.get('accept_all'),
                'block': verification_data.get('block'),
                'sources': verification_data.get('sources', []),
                'verified_at': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Email verification for {email}: {result['result']} (score: {result['score']})")
            return result
            
        except Exception as e:
            logger.error(f"Email verification failed for {email}: {str(e)}")
            return {
                'email': email,
                'status': 'error',
                'result': 'unknown',
                'error': str(e),
                'verified_at': datetime.utcnow().isoformat()
            }
    
    def verify_emails_batch(self, emails: List[str]) -> List[Dict]:
        """
        Verify multiple email addresses
        
        Args:
            emails: List of email addresses to verify
        
        Returns:
            List of verification results
        """
        results = []
        
        for email in emails:
            try:
                result = self.verify_email(email)
                results.append(result)
                
                # Small delay between batch requests
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Batch verification failed for {email}: {str(e)}")
                results.append({
                    'email': email,
                    'status': 'error',
                    'result': 'unknown',
                    'error': str(e),
                    'verified_at': datetime.utcnow().isoformat()
                })
        
        logger.info(f"Batch verified {len(results)} emails")
        return results
    
    def find_emails(self, domain: str, limit: int = 10, department: str = None) -> List[Dict]:
        """
        Find email addresses for a domain
        
        Args:
            domain: Domain to search
            limit: Maximum number of emails to return
            department: Filter by department (e.g., 'executive', 'it', 'finance')
        
        Returns:
            List of found email addresses with metadata
        """
        params = {
            'domain': domain,
            'limit': min(limit, 100),  # Hunter max is 100
            'type': 'personal'  # Focus on personal emails, not generic ones
        }
        
        if department:
            params['department'] = department
        
        try:
            data = self._make_request('domain-search', params)
            domain_data = data.get('data', {})
            emails = domain_data.get('emails', [])
            
            processed_emails = []
            for email_data in emails:
                processed_email = {
                    'email': email_data.get('value'),
                    'first_name': email_data.get('first_name'),
                    'last_name': email_data.get('last_name'),
                    'position': email_data.get('position'),
                    'department': email_data.get('department'),
                    'type': email_data.get('type'),
                    'confidence': email_data.get('confidence'),
                    'sources': email_data.get('sources', []),
                    'last_seen_on': email_data.get('last_seen_on'),
                    'domain': domain
                }
                processed_emails.append(processed_email)
            
            # Also include domain metadata
            domain_info = {
                'domain': domain,
                'disposable': domain_data.get('disposable'),
                'webmail': domain_data.get('webmail'),
                'accept_all': domain_data.get('accept_all'),
                'pattern': domain_data.get('pattern'),
                'organization': domain_data.get('organization'),
                'country': domain_data.get('country'),
                'state': domain_data.get('state'),
                'emails_found': len(processed_emails)
            }
            
            logger.info(f"Found {len(processed_emails)} emails for domain {domain}")
            return {
                'emails': processed_emails,
                'domain_info': domain_info
            }
            
        except Exception as e:
            logger.error(f"Domain search failed for {domain}: {str(e)}")
            return {
                'emails': [],
                'domain_info': {'domain': domain, 'error': str(e)},
                'error': str(e)
            }
    
    def get_email_count(self, domain: str) -> Dict:
        """
        Get email count for a domain without retrieving actual emails
        
        Args:
            domain: Domain to check
        
        Returns:
            Dictionary with email count and domain info
        """
        params = {
            'domain': domain,
            'limit': 1  # Minimal limit to get count info
        }
        
        try:
            data = self._make_request('email-count', params)
            count_data = data.get('data', {})
            
            return {
                'domain': domain,
                'total': count_data.get('total', 0),
                'personal_emails': count_data.get('personal_emails', 0),
                'generic_emails': count_data.get('generic_emails', 0),
                'department_breakdown': count_data.get('department', {}),
                'seniority_breakdown': count_data.get('seniority', {}),
                'checked_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Email count failed for {domain}: {str(e)}")
            return {
                'domain': domain,
                'total': 0,
                'error': str(e),
                'checked_at': datetime.utcnow().isoformat()
            }
    
    def suggest_email(self, domain: str, first_name: str, last_name: str) -> Dict:
        """
        Suggest email address based on domain pattern
        
        Args:
            domain: Company domain
            first_name: Person's first name
            last_name: Person's last name
        
        Returns:
            Dictionary with suggested email and confidence
        """
        params = {
            'domain': domain,
            'first_name': first_name,
            'last_name': last_name
        }
        
        try:
            data = self._make_request('email-finder', params)
            finder_data = data.get('data', {})
            
            return {
                'email': finder_data.get('email'),
                'first_name': first_name,
                'last_name': last_name,
                'domain': domain,
                'confidence': finder_data.get('confidence'),
                'sources': finder_data.get('sources', []),
                'suggested_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Email suggestion failed for {first_name} {last_name} at {domain}: {str(e)}")
            return {
                'email': None,
                'first_name': first_name,
                'last_name': last_name,
                'domain': domain,
                'confidence': 0,
                'error': str(e),
                'suggested_at': datetime.utcnow().isoformat()
            }
    
    def get_account_info(self) -> Dict:
        """Get Hunter account information and usage stats"""
        try:
            data = self._make_request('account', {})
            account_data = data.get('data', {})
            
            return {
                'email': account_data.get('email'),
                'plan_name': account_data.get('plan_name'),
                'plan_level': account_data.get('plan_level'),
                'reset_date': account_data.get('reset_date'),
                'calls': {
                    'used': account_data.get('calls', {}).get('used', 0),
                    'available': account_data.get('calls', {}).get('available', 0)
                },
                'requests_made_this_month': self.requests_made_this_month
            }
            
        except Exception as e:
            logger.error(f"Failed to get Hunter account info: {str(e)}")
            return {
                'error': str(e),
                'requests_made_this_month': self.requests_made_this_month
            }
    
    def is_email_deliverable(self, verification_result: Dict) -> bool:
        """
        Check if email is likely deliverable based on verification result
        
        Args:
            verification_result: Result from verify_email()
        
        Returns:
            Boolean indicating if email is likely deliverable
        """
        result = verification_result.get('result', '').lower()
        score = verification_result.get('score', 0)
        
        # Consider deliverable if result is 'deliverable' or score is high
        return result == 'deliverable' or (result == 'risky' and score >= 70)
    
    def get_email_quality_score(self, verification_result: Dict) -> int:
        """
        Get email quality score for lead scoring
        
        Args:
            verification_result: Result from verify_email()
        
        Returns:
            Quality score (0-100)
        """
        result = verification_result.get('result', '').lower()
        score = verification_result.get('score', 0)
        
        if result == 'deliverable':
            return min(score + 20, 100)  # Bonus for deliverable
        elif result == 'risky':
            return max(score - 10, 0)  # Penalty for risky
        elif result == 'undeliverable':
            return 0
        else:
            return score


class HunterAPIError(Exception):
    """Custom exception for Hunter API errors"""
    pass


# Global instance for reuse
hunter_client = None

def get_hunter_client() -> HunterAPIClient:
    """Get or create Hunter API client instance"""
    global hunter_client
    if hunter_client is None:
        hunter_client = HunterAPIClient()
    return hunter_client

