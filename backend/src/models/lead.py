# Lead model imports and exports
from .lead_model import Lead
from .campaign import Campaign
from .client import db

# Export the models for easy importing
__all__ = ['Lead', 'Campaign', 'db']
