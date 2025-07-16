from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Client(db.Model):
    """Client model for multi-tenant lead generation platform"""
    
    __tablename__ = 'clients'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    company_name = db.Column(db.String(255), nullable=False)
    contact_name = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(50))
    industry = db.Column(db.String(100))
    
    # Subscription details
    plan = db.Column(db.String(50), default='starter')  # starter, professional, enterprise
    status = db.Column(db.String(20), default='active')  # active, suspended, cancelled
    
    # API usage tracking
    api_quota_monthly = db.Column(db.Integer, default=1000)
    api_usage_current = db.Column(db.Integer, default=0)
    api_usage_reset_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    leads = db.relationship('Lead', backref='client', lazy=True, cascade='all, delete-orphan')
    campaigns = db.relationship('Campaign', backref='client', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def can_generate_leads(self, count=1):
        """Check if client can generate more leads based on quota"""
        return (self.api_usage_current + count) <= self.api_quota_monthly
    
    def increment_api_usage(self, count=1):
        """Increment API usage counter"""
        self.api_usage_current += count
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def reset_monthly_usage(self):
        """Reset monthly API usage (called by scheduled job)"""
        self.api_usage_current = 0
        self.api_usage_reset_date = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self, include_sensitive=False):
        """Convert to dictionary for JSON serialization"""
        data = {
            'id': self.id,
            'email': self.email,
            'company_name': self.company_name,
            'contact_name': self.contact_name,
            'phone': self.phone,
            'industry': self.industry,
            'plan': self.plan,
            'status': self.status,
            'api_quota_monthly': self.api_quota_monthly,
            'api_usage_current': self.api_usage_current,
            'api_usage_reset_date': self.api_usage_reset_date.isoformat() if self.api_usage_reset_date else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
        
        if not include_sensitive:
            # Remove sensitive information for API responses
            data.pop('password_hash', None)
        
        return data
    
    def __repr__(self):
        return f'<Client {self.email}>'


class AdminUser(db.Model):
    """Admin user model for platform administration"""
    
    __tablename__ = 'admin_users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default='admin')  # admin, super_admin
    is_active = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
    
    def __repr__(self):
        return f'<AdminUser {self.email}>'

