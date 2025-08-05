from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import json
import uuid

from .client import db

class Campaign(db.Model):
    """Campaign model for automated lead generation"""
    __tablename__ = 'campaigns'
    
    # Primary key
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Foreign keys
    client_id = db.Column(db.String(36), db.ForeignKey('clients.id'), nullable=False, index=True)
    
    # Campaign details
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='active')  # active, paused, completed, cancelled
    
    # Lead generation criteria (stored as JSON)
    criteria = db.Column(db.Text, nullable=False)  # JSON string with LeadCriteria
    
    # Scheduling configuration
    frequency = db.Column(db.String(20), nullable=False)  # daily, weekly, monthly, custom
    frequency_value = db.Column(db.Integer, default=1)  # e.g., 3 for "3x per week"
    frequency_unit = db.Column(db.String(10), default='day')  # day, week, month
    
    # Time preferences
    preferred_time = db.Column(db.Time)  # Preferred time to run campaigns
    timezone = db.Column(db.String(50), default='Australia/Sydney')
    
    # Campaign limits
    max_leads_per_run = db.Column(db.Integer, default=50)
    max_leads_total = db.Column(db.Integer)  # Optional total limit
    
    # Status tracking
    total_leads_generated = db.Column(db.Integer, default=0)
    last_run_at = db.Column(db.DateTime)
    next_run_at = db.Column(db.DateTime, index=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships - backref is defined in Client model
    # client relationship is defined via backref in Client model
    executions = db.relationship('CampaignExecution', backref='campaign', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Campaign {self.name} ({self.status})>'
    
    def set_criteria(self, criteria_dict):
        """Set campaign criteria as JSON"""
        self.criteria = json.dumps(criteria_dict)
    
    def get_criteria(self):
        """Get campaign criteria from JSON"""
        return json.loads(self.criteria) if self.criteria else {}
    
    def calculate_next_run(self):
        """Calculate the next run time based on frequency settings"""
        if not self.last_run_at:
            # First run - schedule for preferred time today or tomorrow
            base_time = datetime.now()
            if self.preferred_time:
                next_run = datetime.combine(base_time.date(), self.preferred_time)
                if next_run <= base_time:
                    next_run += timedelta(days=1)
            else:
                next_run = base_time + timedelta(minutes=5)  # Default: 5 minutes from now
        else:
            # Calculate based on frequency
            if self.frequency == 'daily':
                next_run = self.last_run_at + timedelta(days=1)
            elif self.frequency == 'weekly':
                next_run = self.last_run_at + timedelta(weeks=1)
            elif self.frequency == 'monthly':
                next_run = self.last_run_at + timedelta(days=30)
            elif self.frequency == 'custom':
                if self.frequency_unit == 'day':
                    next_run = self.last_run_at + timedelta(days=self.frequency_value)
                elif self.frequency_unit == 'week':
                    next_run = self.last_run_at + timedelta(weeks=self.frequency_value)
                elif self.frequency_unit == 'hour':
                    next_run = self.last_run_at + timedelta(hours=self.frequency_value)
                else:
                    next_run = self.last_run_at + timedelta(days=1)  # Default fallback
            else:
                next_run = self.last_run_at + timedelta(days=1)  # Default fallback
        
        self.next_run_at = next_run
        return next_run
    
    def is_ready_to_run(self):
        """Check if campaign is ready to run"""
        if self.status != 'active':
            return False
        
        if not self.next_run_at:
            return True  # First run
        
        return datetime.utcnow() >= self.next_run_at
    
    def has_reached_total_limit(self):
        """Check if campaign has reached total lead limit"""
        if not self.max_leads_total:
            return False
        
        return self.total_leads_generated >= self.max_leads_total
    
    def update_after_run(self, leads_generated):
        """Update campaign status after execution"""
        self.last_run_at = datetime.utcnow()
        self.total_leads_generated += leads_generated
        self.calculate_next_run()
        
        # Check if we should pause due to limits
        if self.has_reached_total_limit():
            self.status = 'completed'
    
    def to_dict(self):
        """Convert campaign to dictionary"""
        return {
            'id': self.id,
            'client_id': self.client_id,
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'criteria': self.get_criteria(),
            'frequency': self.frequency,
            'frequency_value': self.frequency_value,
            'frequency_unit': self.frequency_unit,
            'preferred_time': self.preferred_time.strftime('%H:%M') if self.preferred_time else None,
            'timezone': self.timezone,
            'max_leads_per_run': self.max_leads_per_run,
            'max_leads_total': self.max_leads_total,
            'total_leads_generated': self.total_leads_generated,
            'last_run_at': self.last_run_at.isoformat() if self.last_run_at else None,
            'next_run_at': self.next_run_at.isoformat() if self.next_run_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class CampaignExecution(db.Model):
    """Campaign execution log for tracking automated runs"""
    __tablename__ = 'campaign_executions'
    
    # Primary key
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Foreign keys
    campaign_id = db.Column(db.String(36), db.ForeignKey('campaigns.id'), nullable=False, index=True)
    
    # Execution details
    status = db.Column(db.String(20), nullable=False)  # running, completed, failed, cancelled
    leads_generated = db.Column(db.Integer, default=0)
    leads_processed = db.Column(db.Integer, default=0)
    
    # Execution metadata
    started_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    completed_at = db.Column(db.DateTime)
    duration_seconds = db.Column(db.Integer)
    
    # Results and errors
    result_summary = db.Column(db.Text)  # JSON string with execution results
    error_message = db.Column(db.Text)
    
    # API usage tracking
    apollo_calls = db.Column(db.Integer, default=0)
    hunter_calls = db.Column(db.Integer, default=0)
    linkedin_calls = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f'<CampaignExecution {self.id} ({self.status})>'
    
    def set_result_summary(self, summary_dict):
        """Set execution result summary as JSON"""
        self.result_summary = json.dumps(summary_dict)
    
    def get_result_summary(self):
        """Get execution result summary from JSON"""
        return json.loads(self.result_summary) if self.result_summary else {}
    
    def mark_completed(self, leads_generated, summary=None):
        """Mark execution as completed"""
        self.status = 'completed'
        self.completed_at = datetime.utcnow()
        self.leads_generated = leads_generated
        self.duration_seconds = int((self.completed_at - self.started_at).total_seconds())
        
        if summary:
            self.set_result_summary(summary)
    
    def mark_failed(self, error_message):
        """Mark execution as failed"""
        self.status = 'failed'
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
        self.duration_seconds = int((self.completed_at - self.started_at).total_seconds())
    
    def to_dict(self):
        """Convert execution to dictionary"""
        return {
            'id': self.id,
            'campaign_id': self.campaign_id,
            'status': self.status,
            'leads_generated': self.leads_generated,
            'leads_processed': self.leads_processed,
            'started_at': self.started_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration_seconds': self.duration_seconds,
            'result_summary': self.get_result_summary(),
            'error_message': self.error_message,
            'api_usage': {
                'apollo_calls': self.apollo_calls,
                'hunter_calls': self.hunter_calls,
                'linkedin_calls': self.linkedin_calls
            }
        }


class CampaignScheduler:
    """Service class for managing campaign scheduling"""
    
    @staticmethod
    def get_due_campaigns():
        """Get all campaigns that are due to run"""
        return Campaign.query.filter(
            Campaign.status == 'active',
            db.or_(
                Campaign.next_run_at.is_(None),
                Campaign.next_run_at <= datetime.utcnow()
            )
        ).all()
    
    @staticmethod
    def create_campaign_from_onboarding(client_id, onboarding_data):
        """Create a campaign from onboarding data"""
        # Extract frequency settings
        frequency_map = {
            '1x_day': {'frequency': 'daily', 'value': 1, 'unit': 'day'},
            '2x_day': {'frequency': 'custom', 'value': 12, 'unit': 'hour'},
            '3x_week': {'frequency': 'custom', 'value': 2, 'unit': 'day'},
            '1x_week': {'frequency': 'weekly', 'value': 1, 'unit': 'week'},
            '2x_month': {'frequency': 'custom', 'value': 15, 'unit': 'day'},
            '1x_month': {'frequency': 'monthly', 'value': 1, 'unit': 'month'}
        }
        
        frequency_setting = onboarding_data.get('prospecting_frequency', '1x_day')
        freq_config = frequency_map.get(frequency_setting, frequency_map['1x_day'])
        
        # Create campaign
        campaign = Campaign(
            client_id=client_id,
            name=f"Automated Lead Generation - {onboarding_data.get('business_type', 'General')}",
            description=f"Automated campaign based on onboarding preferences",
            frequency=freq_config['frequency'],
            frequency_value=freq_config['value'],
            frequency_unit=freq_config['unit'],
            preferred_time=datetime.strptime(onboarding_data.get('preferred_time', '09:00'), '%H:%M').time(),
            max_leads_per_run=onboarding_data.get('leads_per_run', 50),
            max_leads_total=onboarding_data.get('total_leads_limit')
        )
        
        # Set criteria from onboarding
        criteria = {
            'keywords': onboarding_data.get('target_keywords', ''),
            'industries': onboarding_data.get('target_industries', []),
            'locations': onboarding_data.get('target_locations', ['Australia']),
            'titles': onboarding_data.get('target_titles', []),
            'company_sizes': onboarding_data.get('company_sizes', []),
            'min_score': onboarding_data.get('min_lead_score', 70),
            'max_results': campaign.max_leads_per_run,
            'verify_emails': True,
            'enrich_linkedin': True
        }
        
        campaign.set_criteria(criteria)
        campaign.calculate_next_run()
        
        return campaign
    
    @staticmethod
    def pause_campaign(campaign_id):
        """Pause a campaign"""
        campaign = Campaign.query.get(campaign_id)
        if campaign:
            campaign.status = 'paused'
            campaign.next_run_at = None
            return True
        return False
    
    @staticmethod
    def resume_campaign(campaign_id):
        """Resume a paused campaign"""
        campaign = Campaign.query.get(campaign_id)
        if campaign and campaign.status == 'paused':
            campaign.status = 'active'
            campaign.calculate_next_run()
            return True
        return False
    
    @staticmethod
    def get_campaign_stats(campaign_id):
        """Get campaign statistics"""
        campaign = Campaign.query.get(campaign_id)
        if not campaign:
            return None
        
        executions = CampaignExecution.query.filter_by(campaign_id=campaign_id).all()
        
        total_executions = len(executions)
        successful_executions = len([e for e in executions if e.status == 'completed'])
        failed_executions = len([e for e in executions if e.status == 'failed'])
        
        avg_leads_per_run = 0
        if successful_executions > 0:
            avg_leads_per_run = sum(e.leads_generated for e in executions if e.status == 'completed') / successful_executions
        
        return {
            'campaign': campaign.to_dict(),
            'stats': {
                'total_executions': total_executions,
                'successful_executions': successful_executions,
                'failed_executions': failed_executions,
                'success_rate': (successful_executions / total_executions * 100) if total_executions > 0 else 0,
                'avg_leads_per_run': round(avg_leads_per_run, 1),
                'total_leads_generated': campaign.total_leads_generated
            },
            'recent_executions': [e.to_dict() for e in executions[-10:]]  # Last 10 executions
        }

