from datetime import datetime
from .client import db

class Lead(db.Model):
    """Lead model for storing generated lead information"""
    __tablename__ = 'leads'
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.String(36), db.ForeignKey('clients.id'), nullable=False)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.id'), nullable=True)
    
    # Lead information
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(50), nullable=True)
    company = db.Column(db.String(255), nullable=True)
    title = db.Column(db.String(255), nullable=True)
    industry = db.Column(db.String(100), nullable=True)
    location = db.Column(db.String(255), nullable=True)
    
    # Lead scoring and verification
    score = db.Column(db.Integer, default=0)
    email_verified = db.Column(db.Boolean, default=False)
    linkedin_url = db.Column(db.String(500), nullable=True)
    
    # Metadata
    source = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(50), default='new')
    notes = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships - backref is defined in Client model
    # client relationship is defined via backref in Client model
    campaign = db.relationship('Campaign', backref='leads')
    
    def __repr__(self):
        return f'<Lead {self.first_name} {self.last_name} - {self.email}>'
    
    def to_dict(self):
        """Convert lead to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'client_id': self.client_id,
            'campaign_id': self.campaign_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'phone': self.phone,
            'company': self.company,
            'title': self.title,
            'industry': self.industry,
            'location': self.location,
            'score': self.score,
            'email_verified': self.email_verified,
            'linkedin_url': self.linkedin_url,
            'source': self.source,
            'status': self.status,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
