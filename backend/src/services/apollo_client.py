import requests
import time
import logging
from typing import List, Dict, Optional
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class ApolloAPIClient:
    """Apollo.io API client for lead generation and contact search"""
    
    def __init__(self):
        self.api_key = os.getenv('APOLLO_API_KEY')
        if not self.api_key:
            raise ValueError("APOLLO_API_KEY environment variable is required")
        
        self.base_url = "https://api.apollo.io/v1"
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache'
        })
        
        # Rate limiting configuration
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 10 requests per second max
        self.daily_quota = 1000  # Adjust based on your Apollo plan
        self.requests_made_today = 0
        self.quota_reset_date = datetime.now().date()
    
    def _rate_limit(self):
        """Implement rate limiting to avoid API throttling"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            logger.info(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
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
            raise ApolloAPIError(f"Daily quota of {self.daily_quota} requests exceeded")
    
    def _make_request(self, endpoint: str, payload: Dict) -> Dict:
        """Make authenticated request to Apollo API"""
        self._check_quota()
        self._rate_limit()
        
        url = f"{self.base_url}/{endpoint}"
        payload['api_key'] = self.api_key
        
        try:
            logger.info(f"Making Apollo API request to {endpoint}")
            response = self.session.post(url, json=payload, timeout=30)
            
            # Increment request counter
            self.requests_made_today += 1
            
            # Handle rate limiting response
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                logger.warning(f"Rate limited by Apollo API, waiting {retry_after} seconds")
                time.sleep(retry_after)
                return self._make_request(endpoint, payload)
            
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"Apollo API request successful, got {len(data.get('people', []))} results")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Apollo API request failed: {str(e)}")
            raise ApolloAPIError(f"API request failed: {str(e)}")
    
    def search_people(self, criteria: Dict) -> List[Dict]:
        """
        Search for people using Apollo.io API
        
        Args:
            criteria: Search criteria including keywords, locations, titles, etc.
        
        Returns:
            List of processed lead dictionaries
        """
        # Build payload with correct Apollo.io API format
        payload = {
            'page': criteria.get('page', 1),
            'per_page': min(criteria.get('per_page', 25), 100)  # Apollo max is 100
        }
        
        # Add optional search parameters only if they have values
        keywords = criteria.get('keywords', '').strip()
        if keywords:
            payload['q_keywords'] = keywords
        
        locations = criteria.get('locations', [])
        if locations and locations != ['']:
            payload['person_locations'] = locations
        
        titles = criteria.get('titles', [])
        if titles and titles != ['']:
            payload['person_titles'] = titles
        
        company_locations = criteria.get('company_locations', [])
        if company_locations and company_locations != ['']:
            payload['organization_locations'] = company_locations
        
        industries = criteria.get('industries', [])
        if industries and industries != ['']:
            payload['organization_industries'] = industries
        
        company_sizes = criteria.get('company_sizes', [])
        if company_sizes and company_sizes != ['']:
            payload['organization_num_employees_ranges'] = company_sizes
        
        try:
            data = self._make_request('mixed_people/search', payload)
            people = data.get('people', [])
            
            # Process and standardize results
            processed_leads = []
            for person in people:
                lead = self._process_person_data(person)
                if lead:  # Only add valid leads
                    processed_leads.append(lead)
            
            logger.info(f"Processed {len(processed_leads)} valid leads from Apollo")
            return processed_leads
            
        except Exception as e:
            logger.error(f"Apollo people search failed: {str(e)}")
            raise
    
    def _process_person_data(self, person: Dict) -> Optional[Dict]:
        """Process and standardize Apollo.io person data"""
        try:
            # Extract basic information
            first_name = person.get('first_name', '').strip()
            last_name = person.get('last_name', '').strip()
            name = f"{first_name} {last_name}".strip()
            
            # Skip if no name
            if not name:
                return None
            
            email = person.get('email', '').strip()
            # Skip if no email (essential for lead generation)
            if not email:
                return None
            
            # Extract organization data
            organization = person.get('organization', {}) or {}
            
            # Extract phone numbers
            phone_numbers = person.get('phone_numbers', [])
            phone = phone_numbers[0].get('raw_number', '') if phone_numbers else ''
            
            lead = {
                'name': name,
                'email': email,
                'phone': phone,
                'company': organization.get('name', ''),
                'title': person.get('title', ''),
                'industry': organization.get('industry', ''),
                'location': person.get('city', ''),
                'linkedin_url': person.get('linkedin_url', ''),
                'source': 'apollo',
                'raw_data': person  # Store original data for reference
            }
            
            # Add company information
            lead['company_size'] = organization.get('estimated_num_employees', 0)
            lead['company_domain'] = organization.get('primary_domain', '')
            lead['company_location'] = organization.get('primary_phone', {}).get('country', '')
            
            # Calculate initial lead score
            lead['score'] = self._calculate_lead_score(lead)
            
            return lead
            
        except Exception as e:
            logger.warning(f"Failed to process person data: {str(e)}")
            return None
    
    def _calculate_lead_score(self, lead: Dict) -> int:
        """Calculate lead quality score (0-100) based on available data"""
        score = 0
        
        # Email presence and quality (30 points max)
        if lead.get('email'):
            score += 20
            email = lead['email'].lower()
            
            # Bonus for business email domains
            business_domains = ['.com.au', '.org.au', '.net.au', '.gov.au']
            if any(domain in email for domain in business_domains):
                score += 5
            
            # Penalty for generic email providers
            generic_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']
            if not any(domain in email for domain in generic_domains):
                score += 5
        
        # Phone number presence (20 points)
        if lead.get('phone'):
            score += 20
        
        # LinkedIn profile (15 points)
        if lead.get('linkedin_url'):
            score += 15
        
        # Company information (15 points)
        if lead.get('company'):
            score += 10
            
            # Bonus for company size (prefer mid-size companies)
            company_size = lead.get('company_size', 0)
            if 50 <= company_size <= 1000:
                score += 5
        
        # Title information (10 points)
        if lead.get('title'):
            score += 10
        
        # Industry information (5 points)
        if lead.get('industry'):
            score += 5
        
        # Location information (5 points)
        if lead.get('location'):
            score += 5
        
        return min(score, 100)
    
    def get_person_by_email(self, email: str) -> Optional[Dict]:
        """Get person details by email address"""
        payload = {
            'email': email
        }
        
        try:
            data = self._make_request('people/match', payload)
            person = data.get('person')
            
            if person:
                return self._process_person_data(person)
            
            return None
            
        except Exception as e:
            logger.error(f"Apollo person lookup failed for {email}: {str(e)}")
            return None
    
    def enrich_organization(self, domain: str) -> Optional[Dict]:
        """Enrich organization data by domain"""
        payload = {
            'domain': domain
        }
        
        try:
            data = self._make_request('organizations/enrich', payload)
            organization = data.get('organization')
            
            if organization:
                return {
                    'name': organization.get('name', ''),
                    'domain': organization.get('primary_domain', ''),
                    'industry': organization.get('industry', ''),
                    'size': organization.get('estimated_num_employees', 0),
                    'location': organization.get('primary_phone', {}).get('country', ''),
                    'description': organization.get('short_description', ''),
                    'founded_year': organization.get('founded_year'),
                    'technologies': organization.get('technologies', []),
                    'raw_data': organization
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Apollo organization enrichment failed for {domain}: {str(e)}")
            return None
    
    def get_usage_stats(self) -> Dict:
        """Get current API usage statistics"""
        return {
            'requests_made_today': self.requests_made_today,
            'daily_quota': self.daily_quota,
            'quota_remaining': self.daily_quota - self.requests_made_today,
            'quota_reset_date': self.quota_reset_date.isoformat()
        }


class ApolloAPIError(Exception):
    """Custom exception for Apollo API errors"""
    pass


# Global instance for reuse
apollo_client = None

def get_apollo_client() -> ApolloAPIClient:
    """Get or create Apollo API client instance"""
    global apollo_client
    if apollo_client is None:
        apollo_client = ApolloAPIClient()
    return apollo_client

