import logging
from typing import Dict, List, Optional
from datetime import datetime
import asyncio
import concurrent.futures
from dataclasses import dataclass

from src.services.apollo_client import get_apollo_client, ApolloAPIError
from src.services.hunter_client import get_hunter_client, HunterAPIError
from src.services.linkedin_client import get_linkedin_client, LinkedInAPIError
from src.models.lead import Lead, Campaign, db
from src.models.client import Client

logger = logging.getLogger(__name__)

@dataclass
class LeadCriteria:
    """Data class for lead generation criteria"""
    keywords: str = ""
    industries: List[str] = None
    locations: List[str] = None
    titles: List[str] = None
    company_sizes: List[str] = None
    min_score: int = 60
    max_results: int = 100
    verify_emails: bool = True
    enrich_linkedin: bool = True

class LeadGenerationService:
    """
    Main service for generating leads according to project brief requirements:
    - Lead sourcing only (Beta version)
    - Customizable lead criteria
    - AI-powered scoring
    - Australian B2B focus
    """
    
    def __init__(self):
        self.apollo_client = get_apollo_client()
        self.hunter_client = get_hunter_client()
        self.linkedin_client = get_linkedin_client()
    
    def generate_leads(self, client_id: str, criteria: LeadCriteria, campaign_id: str = None) -> Dict:
        """
        Generate leads based on criteria for Australian B2B consultants
        
        Args:
            client_id: Client requesting leads
            criteria: Lead generation criteria
            campaign_id: Optional campaign to associate leads with
        
        Returns:
            Dictionary with generation results
        """
        logger.info(f"Starting lead generation for client {client_id}")
        
        try:
            # Validate client can generate leads
            client = Client.query.get(client_id)
            if not client:
                raise ValueError(f"Client {client_id} not found")
            
            if not client.can_generate_leads(criteria.max_results):
                raise ValueError(f"Client has insufficient quota. Current usage: {client.api_usage_current}/{client.api_quota_monthly}")
            
            # Step 1: Search Apollo.io for leads
            apollo_criteria = self._prepare_apollo_criteria(criteria)
            raw_leads = self.apollo_client.search_people(apollo_criteria)
            
            logger.info(f"Found {len(raw_leads)} raw leads from Apollo.io")
            
            # Step 2: Filter and deduplicate leads
            filtered_leads = self._filter_and_deduplicate(client_id, raw_leads)
            
            logger.info(f"After filtering: {len(filtered_leads)} unique leads")
            
            # Step 3: Enhance leads with email verification and LinkedIn data
            enhanced_leads = self._enhance_leads(filtered_leads, criteria)
            
            logger.info(f"Enhanced {len(enhanced_leads)} leads")
            
            # Step 4: Apply AI scoring for Australian B2B context
            scored_leads = self._apply_ai_scoring(enhanced_leads, criteria)
            
            # Step 5: Filter by minimum score and limit results
            qualified_leads = [lead for lead in scored_leads if lead['score'] >= criteria.min_score]
            qualified_leads.sort(key=lambda x: x['score'], reverse=True)
            final_leads = qualified_leads[:criteria.max_results]
            
            logger.info(f"Final result: {len(final_leads)} qualified leads")
            
            # Step 6: Save leads to database
            saved_leads = self._save_leads_to_database(client_id, final_leads, campaign_id)
            
            # Step 7: Update client API usage
            client.increment_api_usage(len(saved_leads))
            
            # Step 8: Update campaign statistics if applicable
            if campaign_id:
                campaign = Campaign.query.get(campaign_id)
                if campaign:
                    campaign.update_stats()
            
            return {
                'success': True,
                'leads_generated': len(saved_leads),
                'leads_qualified': len([l for l in saved_leads if l.score >= criteria.min_score]),
                'average_score': sum(l.score for l in saved_leads) / len(saved_leads) if saved_leads else 0,
                'api_usage_remaining': client.api_quota_monthly - client.api_usage_current,
                'leads': [lead.to_dict() for lead in saved_leads],
                'generation_summary': {
                    'apollo_results': len(raw_leads),
                    'after_filtering': len(filtered_leads),
                    'after_enhancement': len(enhanced_leads),
                    'qualified_leads': len(qualified_leads),
                    'final_leads': len(final_leads)
                }
            }
            
        except Exception as e:
            logger.error(f"Lead generation failed for client {client_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'leads_generated': 0
            }
    
    def _prepare_apollo_criteria(self, criteria: LeadCriteria) -> Dict:
        """Prepare search criteria for Apollo.io API"""
        apollo_criteria = {
            'keywords': criteria.keywords,
            'locations': criteria.locations or ['Australia'],  # Default to Australia as per project brief
            'titles': criteria.titles or [],
            'industries': criteria.industries or [],
            'per_page': min(criteria.max_results * 2, 100)  # Get more than needed for filtering
        }
        
        # Map company sizes to Apollo format
        if criteria.company_sizes:
            size_mapping = {
                'startup': '1,10',
                'small': '11,50', 
                'medium': '51,200',
                'large': '201,500',
                'enterprise': '501,1000',
                'very_large': '1001+'
            }
            apollo_criteria['company_sizes'] = [size_mapping.get(size, size) for size in criteria.company_sizes]
        
        return apollo_criteria
    
    def _filter_and_deduplicate(self, client_id: str, leads: List[Dict]) -> List[Dict]:
        """Filter out duplicates and low-quality leads"""
        # Get existing lead emails for this client
        existing_leads = Lead.query.filter_by(client_id=client_id).with_entities(Lead.email).all()
        existing_emails = {lead.email.lower() for lead in existing_leads}
        
        seen_emails = set()
        filtered_leads = []
        
        for lead in leads:
            email = lead.get('email', '').lower().strip()
            
            # Skip if no email
            if not email:
                continue
            
            # Skip if duplicate in current batch
            if email in seen_emails:
                continue
            
            # Skip if already exists for this client
            if email in existing_emails:
                continue
            
            # Skip if email format is invalid
            if not self._is_valid_email_format(email):
                continue
            
            # Skip if company is too small (less than 10 employees) for B2B consulting
            company_size = lead.get('company_size', 0)
            if company_size > 0 and company_size < 10:
                continue
            
            seen_emails.add(email)
            filtered_leads.append(lead)
        
        return filtered_leads
    
    def _enhance_leads(self, leads: List[Dict], criteria: LeadCriteria) -> List[Dict]:
        """Enhance leads with email verification and LinkedIn data"""
        enhanced_leads = []
        
        for lead in leads:
            try:
                # Email verification with Hunter.io
                if criteria.verify_emails and lead.get('email'):
                    verification = self.hunter_client.verify_email(lead['email'])
                    lead['email_verification'] = verification
                    lead['email_verified'] = self.hunter_client.is_email_deliverable(verification)
                
                # LinkedIn profile validation
                if criteria.enrich_linkedin and lead.get('linkedin_url'):
                    linkedin_validation = self.linkedin_client.validate_profile_url(lead['linkedin_url'])
                    lead['linkedin_validation'] = linkedin_validation
                
                enhanced_leads.append(lead)
                
            except Exception as e:
                logger.warning(f"Failed to enhance lead {lead.get('email', 'unknown')}: {str(e)}")
                # Still include the lead even if enhancement fails
                enhanced_leads.append(lead)
        
        return enhanced_leads
    
    def _apply_ai_scoring(self, leads: List[Dict], criteria: LeadCriteria) -> List[Dict]:
        """Apply AI-powered scoring optimized for Australian B2B consultants"""
        scored_leads = []
        
        for lead in leads:
            score = self._calculate_lead_score(lead, criteria)
            lead['score'] = score
            lead['score_breakdown'] = self._get_score_breakdown(lead, criteria)
            scored_leads.append(lead)
        
        return scored_leads
    
    def _calculate_lead_score(self, lead: Dict, criteria: LeadCriteria) -> int:
        """
        Calculate lead score (0-100) optimized for Australian B2B consulting market
        """
        score = 0
        
        # Email quality (25 points max)
        if lead.get('email'):
            score += 15  # Base points for having email
            
            email_verification = lead.get('email_verification', {})
            if email_verification.get('result') == 'deliverable':
                score += 10  # Bonus for verified email
            elif email_verification.get('result') == 'risky':
                score += 5   # Partial bonus for risky but potentially valid
            
            # Australian business email domains get bonus
            email = lead['email'].lower()
            if any(domain in email for domain in ['.com.au', '.org.au', '.net.au', '.gov.au']):
                score += 5
        
        # Phone number (15 points)
        if lead.get('phone'):
            score += 15
        
        # LinkedIn profile (15 points)
        if lead.get('linkedin_url'):
            score += 10
            linkedin_validation = lead.get('linkedin_validation', {})
            if linkedin_validation.get('is_valid'):
                score += 5
        
        # Company information (20 points max)
        if lead.get('company'):
            score += 10
            
            # Company size optimization for B2B consulting
            company_size = lead.get('company_size', 0)
            if 50 <= company_size <= 500:  # Sweet spot for B2B consulting
                score += 10
            elif 20 <= company_size <= 1000:  # Still good
                score += 5
        
        # Title relevance for Australian B2B market (15 points max)
        title = lead.get('title', '').lower()
        if title:
            score += 5  # Base points for having title
            
            # High-value titles for B2B consulting
            high_value_titles = [
                'ceo', 'chief executive', 'managing director', 'general manager',
                'director', 'head of', 'manager', 'leader', 'principal',
                'founder', 'owner', 'president', 'vice president', 'vp'
            ]
            
            if any(hvt in title for hvt in high_value_titles):
                score += 10
        
        # Industry relevance (10 points max)
        industry = lead.get('industry', '').lower()
        if industry:
            score += 3  # Base points for having industry
            
            # High-value industries for Australian B2B consulting
            target_industries = [
                'consulting', 'professional services', 'management',
                'healthcare', 'education', 'finance', 'technology',
                'manufacturing', 'construction', 'government'
            ]
            
            if any(ti in industry for ti in target_industries):
                score += 7
        
        # Location bonus for Australian focus
        location = lead.get('location', '').lower()
        if location:
            australian_cities = [
                'sydney', 'melbourne', 'brisbane', 'perth', 'adelaide',
                'canberra', 'darwin', 'hobart', 'australia'
            ]
            if any(city in location for city in australian_cities):
                score += 5
        
        return min(score, 100)
    
    def _get_score_breakdown(self, lead: Dict, criteria: LeadCriteria) -> Dict:
        """Get detailed breakdown of how the score was calculated"""
        breakdown = {}
        
        # Email scoring
        if lead.get('email'):
            breakdown['email_present'] = 15
            email_verification = lead.get('email_verification', {})
            if email_verification.get('result') == 'deliverable':
                breakdown['email_verified'] = 10
            elif email_verification.get('result') == 'risky':
                breakdown['email_risky'] = 5
            
            if any(domain in lead['email'].lower() for domain in ['.com.au', '.org.au']):
                breakdown['australian_email'] = 5
        
        # Other scoring components
        if lead.get('phone'):
            breakdown['phone_present'] = 15
        
        if lead.get('linkedin_url'):
            breakdown['linkedin_present'] = 10
            if lead.get('linkedin_validation', {}).get('is_valid'):
                breakdown['linkedin_valid'] = 5
        
        if lead.get('company'):
            breakdown['company_present'] = 10
            company_size = lead.get('company_size', 0)
            if 50 <= company_size <= 500:
                breakdown['optimal_company_size'] = 10
            elif 20 <= company_size <= 1000:
                breakdown['good_company_size'] = 5
        
        return breakdown
    
    def _save_leads_to_database(self, client_id: str, leads: List[Dict], campaign_id: str = None) -> List[Lead]:
        """Save generated leads to database"""
        saved_leads = []
        
        for lead_data in leads:
            try:
                lead = Lead(
                    client_id=client_id,
                    campaign_id=campaign_id,
                    name=lead_data.get('name', ''),
                    email=lead_data.get('email', ''),
                    phone=lead_data.get('phone', ''),
                    company=lead_data.get('company', ''),
                    title=lead_data.get('title', ''),
                    industry=lead_data.get('industry', ''),
                    location=lead_data.get('location', ''),
                    linkedin_url=lead_data.get('linkedin_url', ''),
                    score=lead_data.get('score', 0),
                    source='apollo',
                    email_verified=lead_data.get('email_verified', False)
                )
                
                # Set JSON data
                lead.set_score_breakdown(lead_data.get('score_breakdown', {}))
                lead.set_email_verification_data(lead_data.get('email_verification', {}))
                lead.set_raw_data(lead_data.get('raw_data', {}))
                
                db.session.add(lead)
                saved_leads.append(lead)
                
            except Exception as e:
                logger.error(f"Failed to save lead {lead_data.get('email', 'unknown')}: {str(e)}")
        
        try:
            db.session.commit()
            logger.info(f"Successfully saved {len(saved_leads)} leads to database")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to commit leads to database: {str(e)}")
            raise
        
        return saved_leads
    
    def _is_valid_email_format(self, email: str) -> bool:
        """Basic email format validation"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def get_lead_suggestions(self, client_id: str, criteria: LeadCriteria) -> Dict:
        """
        Get lead suggestions without generating actual leads (for preview)
        """
        try:
            # Use a smaller sample for suggestions
            preview_criteria = LeadCriteria(
                keywords=criteria.keywords,
                industries=criteria.industries,
                locations=criteria.locations,
                titles=criteria.titles,
                company_sizes=criteria.company_sizes,
                max_results=10,  # Small sample
                verify_emails=False,  # Skip verification for preview
                enrich_linkedin=False  # Skip LinkedIn for preview
            )
            
            apollo_criteria = self._prepare_apollo_criteria(preview_criteria)
            raw_leads = self.apollo_client.search_people(apollo_criteria)
            
            # Quick scoring without full enhancement
            suggestions = []
            for lead in raw_leads[:5]:  # Just first 5 for preview
                score = self._calculate_lead_score(lead, criteria)
                suggestions.append({
                    'name': lead.get('name', ''),
                    'company': lead.get('company', ''),
                    'title': lead.get('title', ''),
                    'location': lead.get('location', ''),
                    'score': score,
                    'email_domain': lead.get('email', '').split('@')[-1] if lead.get('email') else ''
                })
            
            return {
                'success': True,
                'suggestions': suggestions,
                'estimated_total': len(raw_leads),
                'criteria_used': apollo_criteria
            }
            
        except Exception as e:
            logger.error(f"Failed to get lead suggestions: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'suggestions': []
            }


# Global service instance
lead_generation_service = None

def get_lead_generation_service() -> LeadGenerationService:
    """Get or create lead generation service instance"""
    global lead_generation_service
    if lead_generation_service is None:

# Alias for backward compatibility with existing imports
    return lead_generation_service
    return lead_generation_service

