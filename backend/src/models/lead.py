from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid
import json

db = SQLAlchemy()

class Lead(db.Model):
    """Lead model for storing generated lead data"""
    
    __tablename__ = 'leads'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = db.Column(db.String(36), db.ForeignKey('clients.id'), nullable=False, index=True)
    campaign_id = db.Column(db.String(36), db.ForeignKey('campaigns.id'), nullable=True, index=True)
    
    # Lead information
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, index=True)
    phone = db.Column(db.String(50))
    company = db.Column(db.String(255))
    title = db.Column(db.String(255))
    industry = db.Column(db.String(100))
    location = db.Column(db.String(255))
    
    # LinkedIn information
    linkedin_url = db.Column(db.String(500))
    linkedin_profile_data = db.Column(db.Text)  # JSON string
    
    # Lead scoring and quality
    score = db.Column(db.Integer, default=0)  # 0-100 lead quality score
    score_breakdown = db.Column(db.Text)  # JSON string with scoring details
    
    # Email verification (Hunter.io)
    email_verified = db.Column(db.Boolean, default=False)
    email_verification_data = db.Column(db.Text)  # JSON string
    
    # Lead status and tracking
    status = db.Column(db.String(20), default='new')  # new, contacted, qualified, converted, rejected
    source = db.Column(db.String(50), default='apollo')  # apollo, hunter, linkedin, manual
    
    # Metadata and raw data
    raw_data = db.Column(db.Text)  # JSON string with original API response
    lead_metadata = db.Column(db.Text)  # JSON string with additional metadata
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    contacted_at = db.Column(db.DateTime)
    
    # Indexes for efficient querying
    __table_args__ = (
        db.Index('idx_client_created', 'client_id', 'created_at'),
        db.Index('idx_client_score', 'client_id', 'score'),
        db.Index('idx_client_status', 'client_id', 'status'),
        db.Index('idx_email_client', 'email', 'client_id'),
    )
    
    def set_linkedin_profile_data(self, data):
        """Set LinkedIn profile data as JSON"""
        self.linkedin_profile_data = json.dumps(data) if data else None
    
    def get_linkedin_profile_data(self):
        """Get LinkedIn profile data from JSON"""
        return json.loads(self.linkedin_profile_data) if self.linkedin_profile_data else {}
    
    def set_score_breakdown(self, breakdown):
        """Set score breakdown as JSON"""
        self.score_breakdown = json.dumps(breakdown) if breakdown else None
    
    def get_score_breakdown(self):
        """Get score breakdown from JSON"""
        return json.loads(self.score_breakdown) if self.score_breakdown else {}
    
    def set_email_verification_data(self, data):
        """Set email verification data as JSON"""
        self.email_verification_data = json.dumps(data) if data else None
    
    def get_email_verification_data(self):
        """Get email verification data from JSON"""
        return json.loads(self.email_verification_data) if self.email_verification_data else {}
    
    def set_raw_data(self, data):
        """Set raw API data as JSON"""
        self.raw_data = json.dumps(data) if data else None
    
    def get_raw_data(self):
        """Get raw API data from JSON"""
        return json.loads(self.raw_data) if self.raw_data else {}
    
    def set_metadata(self, data):
        """Set metadata as JSON"""
        self.lead_metadata = json.dumps(data) if data else None
    
    def get_metadata(self):
        """Get metadata from JSON"""
        return json.loads(self.lead_metadata) if self.lead_metadata else {}
    
    def update_status(self, new_status, notes=None):
        """Update lead status with optional notes"""
        self.status = new_status
        self.updated_at = datetime.utcnow()
        
        if new_status == 'contacted':
            self.contacted_at = datetime.utcnow()
        
        if notes:
            metadata = self.get_metadata()
            if 'status_history' not in metadata:
                metadata['status_history'] = []
            
            metadata['status_history'].append({
                'status': new_status,
                'timestamp': datetime.utcnow().isoformat(),
                'notes': notes
            })
            
            self.set_metadata(metadata)
        
        db.session.commit()
    
    def calculate_quality_score(self):
        """Calculate and update lead quality score"""
        score = 0
        breakdown = {}
        
        # Email presence and verification
        if self.email:
            score += 20
            breakdown['email_present'] = 20
            
            if self.email_verified:
                score += 15
                breakdown['email_verified'] = 15
        
        # Phone number presence
        if self.phone:
            score += 15
            breakdown['phone_present'] = 15
        
        # LinkedIn profile
        if self.linkedin_url:
            score += 15
            breakdown['linkedin_present'] = 15
        
        # Company information
        if self.company:
            score += 10
            breakdown['company_present'] = 10
        
        # Title information
        if self.title:
            score += 10
            breakdown['title_present'] = 10
        
        # Industry match (if specified in campaign)
        if self.industry:
            score += 5
            breakdown['industry_present'] = 5
        
        # Location information
        if self.location:
            score += 5
            breakdown['location_present'] = 5
        
        # Email verification quality
        email_verification = self.get_email_verification_data()
        if email_verification.get('result') == 'deliverable':
            score += 5
            breakdown['email_deliverable'] = 5
        
        self.score = min(score, 100)
        self.set_score_breakdown(breakdown)
        
        return self.score
    
    def to_dict(self, include_raw_data=False):
        """Convert to dictionary for JSON serialization"""
        data = {
            'id': self.id,
            'client_id': self.client_id,
            'campaign_id': self.campaign_id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'company': self.company,
            'title': self.title,
            'industry': self.industry,
            'location': self.location,
            'linkedin_url': self.linkedin_url,
            'score': self.score,
            'score_breakdown': self.get_score_breakdown(),
            'email_verified': self.email_verified,
            'email_verification_data': self.get_email_verification_data(),
            'status': self.status,
            'source': self.source,
            'metadata': self.get_metadata(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'contacted_at': self.contacted_at.isoformat() if self.contacted_at else None
        }
        
        if include_raw_data:
            data['raw_data'] = self.get_raw_data()
            data['linkedin_profile_data'] = self.get_linkedin_profile_data()
        
        return data
    
    def __repr__(self):
        return f'<Lead {self.name} ({self.email})>'


class Campaign(db.Model):
    """Campaign model for organizing lead generation efforts"""
    
    __tablename__ = 'campaigns'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = db.Column(db.String(36), db.ForeignKey('clients.id'), nullable=False, index=True)
    
    # Campaign details
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    
    # Search criteria
    keywords = db.Column(db.String(500))
    industries = db.Column(db.Text)  # JSON array
    locations = db.Column(db.Text)  # JSON array
    titles = db.Column(db.Text)  # JSON array
    company_sizes = db.Column(db.Text)  # JSON array
    
    # Campaign settings
    target_count = db.Column(db.Integer, default=100)
    min_score = db.Column(db.Integer, default=60)
    
    # Campaign status
    status = db.Column(db.String(20), default='draft')  # draft, active, paused, completed
    
    # Results tracking
    leads_generated = db.Column(db.Integer, default=0)
    leads_qualified = db.Column(db.Integer, default=0)
    leads_contacted = db.Column(db.Integer, default=0)
    leads_converted = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    # Relationships
    leads = db.relationship('Lead', backref='campaign', lazy=True)
    
    def set_industries(self, industries):
        """Set industries as JSON array"""
        self.industries = json.dumps(industries) if industries else None
    
    def get_industries(self):
        """Get industries from JSON"""
        return json.loads(self.industries) if self.industries else []
    
    def set_locations(self, locations):
        """Set locations as JSON array"""
        self.locations = json.dumps(locations) if locations else None
    
    def get_locations(self):
        """Get locations from JSON"""
        return json.loads(self.locations) if self.locations else []
    
    def set_titles(self, titles):
        """Set titles as JSON array"""
        self.titles = json.dumps(titles) if titles else None
    
    def get_titles(self):
        """Get titles from JSON"""
        return json.loads(self.titles) if self.titles else []
    
    def set_company_sizes(self, sizes):
        """Set company sizes as JSON array"""
        self.company_sizes = json.dumps(sizes) if sizes else None
    
    def get_company_sizes(self):
        """Get company sizes from JSON"""
        return json.loads(self.company_sizes) if self.company_sizes else []
    
    def update_stats(self):
        """Update campaign statistics"""
        leads = Lead.query.filter_by(campaign_id=self.id).all()
        
        self.leads_generated = len(leads)
        self.leads_qualified = len([l for l in leads if l.score >= self.min_score])
        self.leads_contacted = len([l for l in leads if l.status == 'contacted'])
        self.leads_converted = len([l for l in leads if l.status == 'converted'])
        
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'client_id': self.client_id,
            'name': self.name,
            'description': self.description,
            'keywords': self.keywords,
            'industries': self.get_industries(),
            'locations': self.get_locations(),
            'titles': self.get_titles(),
            'company_sizes': self.get_company_sizes(),
            'target_count': self.target_count,
            'min_score': self.min_score,
            'status': self.status,
            'leads_generated': self.leads_generated,
            'leads_qualified': self.leads_qualified,
            'leads_contacted': self.leads_contacted,
            'leads_converted': self.leads_converted,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
    
    def __repr__(self):
        return f'<Campaign {self.name}>'

