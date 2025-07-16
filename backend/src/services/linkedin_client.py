import requests
import time
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import os
import base64

logger = logging.getLogger(__name__)

class LinkedInAPIClient:
    """LinkedIn API client for profile enrichment and company data"""
    
    def __init__(self):
        self.client_id = os.getenv('LINKEDIN_CLIENT_ID')
        self.client_secret = os.getenv('LINKEDIN_CLIENT_SECRET')
        self.redirect_uri = os.getenv('LINKEDIN_REDIRECT_URI', 'http://localhost:5000/auth/linkedin/callback')
        
        if not self.client_id or not self.client_secret:
            raise ValueError("LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET environment variables are required")
        
        self.base_url = "https://api.linkedin.com/v2"
        self.session = requests.Session()
        
        # Rate limiting configuration
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 10 requests per second max
        self.daily_quota = 500  # Adjust based on your LinkedIn app limits
        self.requests_made_today = 0
        self.quota_reset_date = datetime.now().date()
        
        # Token storage (in production, use database)
        self.access_token = None
        self.token_expires_at = None
    
    def get_authorization_url(self, state: str = None) -> str:
        """
        Generate LinkedIn OAuth authorization URL
        
        Args:
            state: Optional state parameter for CSRF protection
        
        Returns:
            Authorization URL for user to visit
        """
        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': 'r_liteprofile r_emailaddress w_member_social',
            'state': state or 'random_state_string'
        }
        
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"https://www.linkedin.com/oauth/v2/authorization?{query_string}"
    
    def exchange_code_for_token(self, code: str) -> Dict:
        """
        Exchange authorization code for access token
        
        Args:
            code: Authorization code from LinkedIn callback
        
        Returns:
            Token information dictionary
        """
        url = "https://www.linkedin.com/oauth/v2/accessToken"
        
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': self.redirect_uri,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        try:
            response = requests.post(url, data=data, timeout=30)
            response.raise_for_status()
            
            token_data = response.json()
            
            # Store token information
            self.access_token = token_data.get('access_token')
            expires_in = token_data.get('expires_in', 3600)
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            logger.info("Successfully obtained LinkedIn access token")
            return token_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to exchange code for token: {str(e)}")
            raise LinkedInAPIError(f"Token exchange failed: {str(e)}")
    
    def _is_token_valid(self) -> bool:
        """Check if current access token is valid"""
        return (self.access_token and 
                self.token_expires_at and 
                datetime.now() < self.token_expires_at)
    
    def _rate_limit(self):
        """Implement rate limiting to avoid API throttling"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            logger.info(f"LinkedIn rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _check_quota(self):
        """Check if we're within daily quota limits"""
        current_date = datetime.now().date()
        
        # Reset quota if it's a new day
        if current_date > self.quota_reset_date:
            self.requests_made_today = 0
            self.quota_reset_date = current_date
        
        if self.requests_made_today >= self.daily_quota:
            raise LinkedInAPIError(f"Daily quota of {self.daily_quota} requests exceeded")
    
    def _make_authenticated_request(self, endpoint: str, params: Dict = None) -> Dict:
        """
        Make authenticated request to LinkedIn API
        
        Args:
            endpoint: API endpoint (without base URL)
            params: Query parameters
        
        Returns:
            API response data
        """
        if not self._is_token_valid():
            raise LinkedInAPIError("No valid access token available")
        
        self._check_quota()
        self._rate_limit()
        
        url = f"{self.base_url}/{endpoint}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            logger.info(f"Making LinkedIn API request to {endpoint}")
            response = self.session.get(url, headers=headers, params=params or {}, timeout=30)
            
            # Increment request counter
            self.requests_made_today += 1
            
            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                logger.warning(f"Rate limited by LinkedIn API, waiting {retry_after} seconds")
                time.sleep(retry_after)
                return self._make_authenticated_request(endpoint, params)
            
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"LinkedIn API request successful")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"LinkedIn API request failed: {str(e)}")
            raise LinkedInAPIError(f"API request failed: {str(e)}")
    
    def get_profile_info(self) -> Dict:
        """
        Get current user's LinkedIn profile information
        
        Returns:
            Profile information dictionary
        """
        try:
            # Get basic profile info
            profile_data = self._make_authenticated_request('people/~')
            
            # Get email address (requires separate permission)
            try:
                email_data = self._make_authenticated_request('emailAddress?q=members&projection=(elements*(handle~))')
                email = email_data.get('elements', [{}])[0].get('handle~', {}).get('emailAddress', '')
            except:
                email = ''
            
            # Process profile data
            profile = {
                'id': profile_data.get('id'),
                'first_name': profile_data.get('firstName', {}).get('localized', {}).get('en_US', ''),
                'last_name': profile_data.get('lastName', {}).get('localized', {}).get('en_US', ''),
                'email': email,
                'headline': profile_data.get('headline', {}).get('localized', {}).get('en_US', ''),
                'location': profile_data.get('location', {}).get('name', ''),
                'industry': profile_data.get('industry', {}).get('localized', {}).get('en_US', ''),
                'profile_picture': profile_data.get('profilePicture', {}).get('displayImage~', {}).get('elements', [{}])[-1].get('identifiers', [{}])[0].get('identifier', ''),
                'raw_data': profile_data
            }
            
            logger.info(f"Retrieved LinkedIn profile for {profile['first_name']} {profile['last_name']}")
            return profile
            
        except Exception as e:
            logger.error(f"Failed to get LinkedIn profile: {str(e)}")
            raise
    
    def search_people_by_company(self, company_name: str, keywords: str = None) -> List[Dict]:
        """
        Search for people by company name (Note: This requires LinkedIn Sales Navigator API)
        
        Args:
            company_name: Company name to search
            keywords: Optional keywords for filtering
        
        Returns:
            List of people profiles
        """
        # Note: This is a simplified version. Full implementation requires Sales Navigator API
        logger.warning("LinkedIn people search requires Sales Navigator API access")
        
        # For now, return empty list with explanation
        return {
            'people': [],
            'message': 'LinkedIn people search requires Sales Navigator API access',
            'alternative': 'Use Apollo.io for people search, then enrich with LinkedIn profile URLs'
        }
    
    def enrich_profile_from_url(self, linkedin_url: str) -> Dict:
        """
        Enrich profile data from LinkedIn URL (requires web scraping or third-party service)
        
        Args:
            linkedin_url: LinkedIn profile URL
        
        Returns:
            Enriched profile data
        """
        # Note: Direct LinkedIn profile scraping violates ToS
        # This would typically use a third-party service like Proxycurl or similar
        
        logger.info(f"Profile enrichment requested for {linkedin_url}")
        
        # Extract LinkedIn ID from URL
        linkedin_id = self._extract_linkedin_id_from_url(linkedin_url)
        
        return {
            'linkedin_url': linkedin_url,
            'linkedin_id': linkedin_id,
            'enrichment_status': 'requires_third_party_service',
            'message': 'Direct LinkedIn profile enrichment requires third-party service like Proxycurl',
            'extracted_at': datetime.utcnow().isoformat()
        }
    
    def _extract_linkedin_id_from_url(self, linkedin_url: str) -> str:
        """Extract LinkedIn ID from profile URL"""
        try:
            # Extract ID from URL patterns like:
            # https://www.linkedin.com/in/john-doe-123456/
            # https://linkedin.com/in/john-doe/
            
            if '/in/' in linkedin_url:
                parts = linkedin_url.split('/in/')
                if len(parts) > 1:
                    return parts[1].rstrip('/').split('/')[0]
            
            return ''
            
        except Exception as e:
            logger.warning(f"Failed to extract LinkedIn ID from {linkedin_url}: {str(e)}")
            return ''
    
    def get_company_info(self, company_id: str) -> Dict:
        """
        Get company information by LinkedIn company ID
        
        Args:
            company_id: LinkedIn company ID
        
        Returns:
            Company information dictionary
        """
        try:
            endpoint = f"organizations/{company_id}"
            company_data = self._make_authenticated_request(endpoint)
            
            company = {
                'id': company_data.get('id'),
                'name': company_data.get('name', {}).get('localized', {}).get('en_US', ''),
                'description': company_data.get('description', {}).get('localized', {}).get('en_US', ''),
                'industry': company_data.get('industries', [{}])[0].get('localized', {}).get('en_US', ''),
                'company_size': company_data.get('staffCount', {}).get('localized', {}).get('en_US', ''),
                'headquarters': company_data.get('locations', [{}])[0].get('description', {}).get('localized', {}).get('en_US', ''),
                'website': company_data.get('website', {}).get('localized', {}).get('en_US', ''),
                'logo': company_data.get('logo', {}).get('original~', {}).get('elements', [{}])[-1].get('identifiers', [{}])[0].get('identifier', ''),
                'founded_year': company_data.get('foundedOn', {}).get('year'),
                'raw_data': company_data
            }
            
            logger.info(f"Retrieved LinkedIn company info for {company['name']}")
            return company
            
        except Exception as e:
            logger.error(f"Failed to get LinkedIn company info: {str(e)}")
            raise
    
    def validate_profile_url(self, linkedin_url: str) -> Dict:
        """
        Validate LinkedIn profile URL format
        
        Args:
            linkedin_url: LinkedIn profile URL to validate
        
        Returns:
            Validation result dictionary
        """
        validation = {
            'url': linkedin_url,
            'is_valid': False,
            'profile_type': None,
            'extracted_id': None,
            'issues': []
        }
        
        if not linkedin_url:
            validation['issues'].append('URL is empty')
            return validation
        
        # Check if it's a LinkedIn URL
        if 'linkedin.com' not in linkedin_url.lower():
            validation['issues'].append('Not a LinkedIn URL')
            return validation
        
        # Check for profile URL pattern
        if '/in/' in linkedin_url:
            validation['profile_type'] = 'personal'
            validation['extracted_id'] = self._extract_linkedin_id_from_url(linkedin_url)
            
            if validation['extracted_id']:
                validation['is_valid'] = True
            else:
                validation['issues'].append('Could not extract profile ID')
        
        elif '/company/' in linkedin_url:
            validation['profile_type'] = 'company'
            validation['issues'].append('Company URLs not supported for profile enrichment')
        
        else:
            validation['issues'].append('Unrecognized LinkedIn URL format')
        
        return validation
    
    def get_usage_stats(self) -> Dict:
        """Get current API usage statistics"""
        return {
            'requests_made_today': self.requests_made_today,
            'daily_quota': self.daily_quota,
            'quota_remaining': self.daily_quota - self.requests_made_today,
            'quota_reset_date': self.quota_reset_date.isoformat(),
            'token_valid': self._is_token_valid(),
            'token_expires_at': self.token_expires_at.isoformat() if self.token_expires_at else None
        }


class LinkedInAPIError(Exception):
    """Custom exception for LinkedIn API errors"""
    pass


# Global instance for reuse
linkedin_client = None

def get_linkedin_client() -> LinkedInAPIClient:
    """Get or create LinkedIn API client instance"""
    global linkedin_client
    if linkedin_client is None:
        linkedin_client = LinkedInAPIClient()
    return linkedin_client

