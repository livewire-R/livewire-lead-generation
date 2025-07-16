from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, time
import logging

from ..models.client import Client
from ..models.campaign import Campaign, CampaignExecution, CampaignScheduler, db
from ..services.lead_generator import LeadGenerator

campaigns_bp = Blueprint('campaigns', __name__)
logger = logging.getLogger(__name__)

@campaigns_bp.route('/campaigns', methods=['GET'])
@jwt_required()
def get_campaigns():
    """Get all campaigns for the authenticated client"""
    try:
        client_id = get_jwt_identity()
        campaigns = Campaign.query.filter_by(client_id=client_id).order_by(Campaign.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'campaigns': [campaign.to_dict() for campaign in campaigns]
        })
    
    except Exception as e:
        logger.error(f"Error getting campaigns: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to retrieve campaigns'}), 500

@campaigns_bp.route('/campaigns', methods=['POST'])
@jwt_required()
def create_campaign():
    """Create a new campaign"""
    try:
        client_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'criteria', 'frequency']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        # Create campaign
        campaign = Campaign(
            client_id=client_id,
            name=data['name'],
            description=data.get('description', ''),
            frequency=data['frequency'],
            frequency_value=data.get('frequency_value', 1),
            frequency_unit=data.get('frequency_unit', 'day'),
            max_leads_per_run=data.get('max_leads_per_run', 50),
            max_leads_total=data.get('max_leads_total'),
            timezone=data.get('timezone', 'Australia/Sydney')
        )
        
        # Set preferred time if provided
        if 'preferred_time' in data:
            try:
                campaign.preferred_time = datetime.strptime(data['preferred_time'], '%H:%M').time()
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid time format. Use HH:MM'}), 400
        
        # Set criteria
        campaign.set_criteria(data['criteria'])
        
        # Calculate next run time
        campaign.calculate_next_run()
        
        # Save to database
        db.session.add(campaign)
        db.session.commit()
        
        logger.info(f"Created campaign {campaign.id} for client {client_id}")
        
        return jsonify({
            'success': True,
            'campaign': campaign.to_dict()
        }), 201
    
    except Exception as e:
        logger.error(f"Error creating campaign: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to create campaign'}), 500

@campaigns_bp.route('/campaigns/<campaign_id>', methods=['GET'])
@jwt_required()
def get_campaign(campaign_id):
    """Get a specific campaign with statistics"""
    try:
        client_id = get_jwt_identity()
        campaign = Campaign.query.filter_by(id=campaign_id, client_id=client_id).first()
        
        if not campaign:
            return jsonify({'success': False, 'error': 'Campaign not found'}), 404
        
        # Get campaign statistics
        stats = CampaignScheduler.get_campaign_stats(campaign_id)
        
        return jsonify({
            'success': True,
            'campaign': stats
        })
    
    except Exception as e:
        logger.error(f"Error getting campaign {campaign_id}: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to retrieve campaign'}), 500

@campaigns_bp.route('/campaigns/<campaign_id>', methods=['PUT'])
@jwt_required()
def update_campaign(campaign_id):
    """Update a campaign"""
    try:
        client_id = get_jwt_identity()
        campaign = Campaign.query.filter_by(id=campaign_id, client_id=client_id).first()
        
        if not campaign:
            return jsonify({'success': False, 'error': 'Campaign not found'}), 404
        
        data = request.get_json()
        
        # Update allowed fields
        if 'name' in data:
            campaign.name = data['name']
        if 'description' in data:
            campaign.description = data['description']
        if 'frequency' in data:
            campaign.frequency = data['frequency']
        if 'frequency_value' in data:
            campaign.frequency_value = data['frequency_value']
        if 'frequency_unit' in data:
            campaign.frequency_unit = data['frequency_unit']
        if 'max_leads_per_run' in data:
            campaign.max_leads_per_run = data['max_leads_per_run']
        if 'max_leads_total' in data:
            campaign.max_leads_total = data['max_leads_total']
        if 'preferred_time' in data:
            try:
                campaign.preferred_time = datetime.strptime(data['preferred_time'], '%H:%M').time()
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid time format. Use HH:MM'}), 400
        if 'criteria' in data:
            campaign.set_criteria(data['criteria'])
        
        # Recalculate next run if frequency changed
        if any(field in data for field in ['frequency', 'frequency_value', 'frequency_unit', 'preferred_time']):
            campaign.calculate_next_run()
        
        campaign.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"Updated campaign {campaign_id}")
        
        return jsonify({
            'success': True,
            'campaign': campaign.to_dict()
        })
    
    except Exception as e:
        logger.error(f"Error updating campaign {campaign_id}: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to update campaign'}), 500

@campaigns_bp.route('/campaigns/<campaign_id>', methods=['DELETE'])
@jwt_required()
def delete_campaign(campaign_id):
    """Delete a campaign"""
    try:
        client_id = get_jwt_identity()
        campaign = Campaign.query.filter_by(id=campaign_id, client_id=client_id).first()
        
        if not campaign:
            return jsonify({'success': False, 'error': 'Campaign not found'}), 404
        
        db.session.delete(campaign)
        db.session.commit()
        
        logger.info(f"Deleted campaign {campaign_id}")
        
        return jsonify({'success': True, 'message': 'Campaign deleted successfully'})
    
    except Exception as e:
        logger.error(f"Error deleting campaign {campaign_id}: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to delete campaign'}), 500

@campaigns_bp.route('/campaigns/<campaign_id>/pause', methods=['POST'])
@jwt_required()
def pause_campaign(campaign_id):
    """Pause a campaign"""
    try:
        client_id = get_jwt_identity()
        campaign = Campaign.query.filter_by(id=campaign_id, client_id=client_id).first()
        
        if not campaign:
            return jsonify({'success': False, 'error': 'Campaign not found'}), 404
        
        if CampaignScheduler.pause_campaign(campaign_id):
            db.session.commit()
            logger.info(f"Paused campaign {campaign_id}")
            return jsonify({'success': True, 'message': 'Campaign paused successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to pause campaign'}), 500
    
    except Exception as e:
        logger.error(f"Error pausing campaign {campaign_id}: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to pause campaign'}), 500

@campaigns_bp.route('/campaigns/<campaign_id>/resume', methods=['POST'])
@jwt_required()
def resume_campaign(campaign_id):
    """Resume a paused campaign"""
    try:
        client_id = get_jwt_identity()
        campaign = Campaign.query.filter_by(id=campaign_id, client_id=client_id).first()
        
        if not campaign:
            return jsonify({'success': False, 'error': 'Campaign not found'}), 404
        
        if CampaignScheduler.resume_campaign(campaign_id):
            db.session.commit()
            logger.info(f"Resumed campaign {campaign_id}")
            return jsonify({'success': True, 'message': 'Campaign resumed successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to resume campaign'}), 500
    
    except Exception as e:
        logger.error(f"Error resuming campaign {campaign_id}: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to resume campaign'}), 500

@campaigns_bp.route('/campaigns/<campaign_id>/run', methods=['POST'])
@jwt_required()
def run_campaign_now(campaign_id):
    """Manually trigger a campaign run"""
    try:
        client_id = get_jwt_identity()
        campaign = Campaign.query.filter_by(id=campaign_id, client_id=client_id).first()
        
        if not campaign:
            return jsonify({'success': False, 'error': 'Campaign not found'}), 404
        
        if campaign.status != 'active':
            return jsonify({'success': False, 'error': 'Campaign is not active'}), 400
        
        # Create execution record
        execution = CampaignExecution(
            campaign_id=campaign_id,
            status='running'
        )
        db.session.add(execution)
        db.session.commit()
        
        try:
            # Run lead generation
            lead_generator = LeadGenerator()
            criteria = campaign.get_criteria()
            
            # Generate leads
            results = lead_generator.generate_leads(
                client_id=client_id,
                criteria=criteria,
                max_results=campaign.max_leads_per_run
            )
            
            # Update execution
            execution.mark_completed(
                leads_generated=len(results.get('leads', [])),
                summary=results
            )
            
            # Update campaign
            campaign.update_after_run(len(results.get('leads', [])))
            
            db.session.commit()
            
            logger.info(f"Manual campaign run completed for {campaign_id}: {len(results.get('leads', []))} leads generated")
            
            return jsonify({
                'success': True,
                'execution': execution.to_dict(),
                'results': results
            })
        
        except Exception as e:
            # Mark execution as failed
            execution.mark_failed(str(e))
            db.session.commit()
            raise e
    
    except Exception as e:
        logger.error(f"Error running campaign {campaign_id}: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to run campaign'}), 500

@campaigns_bp.route('/campaigns/<campaign_id>/executions', methods=['GET'])
@jwt_required()
def get_campaign_executions(campaign_id):
    """Get execution history for a campaign"""
    try:
        client_id = get_jwt_identity()
        campaign = Campaign.query.filter_by(id=campaign_id, client_id=client_id).first()
        
        if not campaign:
            return jsonify({'success': False, 'error': 'Campaign not found'}), 404
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        executions = CampaignExecution.query.filter_by(campaign_id=campaign_id)\
            .order_by(CampaignExecution.started_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'success': True,
            'executions': [execution.to_dict() for execution in executions.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': executions.total,
                'pages': executions.pages,
                'has_next': executions.has_next,
                'has_prev': executions.has_prev
            }
        })
    
    except Exception as e:
        logger.error(f"Error getting executions for campaign {campaign_id}: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to retrieve executions'}), 500

@campaigns_bp.route('/onboarding/campaign', methods=['POST'])
@jwt_required()
def create_onboarding_campaign():
    """Create a campaign from onboarding data"""
    try:
        client_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate onboarding data
        required_fields = ['prospecting_frequency', 'target_industries', 'business_type']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        # Create campaign from onboarding
        campaign = CampaignScheduler.create_campaign_from_onboarding(client_id, data)
        
        # Save to database
        db.session.add(campaign)
        db.session.commit()
        
        logger.info(f"Created onboarding campaign {campaign.id} for client {client_id}")
        
        return jsonify({
            'success': True,
            'campaign': campaign.to_dict(),
            'message': 'Automated campaign created successfully! Lead generation will begin according to your schedule.'
        }), 201
    
    except Exception as e:
        logger.error(f"Error creating onboarding campaign: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to create campaign from onboarding'}), 500

@campaigns_bp.route('/scheduler/due', methods=['GET'])
def get_due_campaigns():
    """Get campaigns that are due to run (internal endpoint for scheduler)"""
    try:
        # This endpoint should be protected in production (API key, internal network, etc.)
        due_campaigns = CampaignScheduler.get_due_campaigns()
        
        return jsonify({
            'success': True,
            'campaigns': [campaign.to_dict() for campaign in due_campaigns],
            'count': len(due_campaigns)
        })
    
    except Exception as e:
        logger.error(f"Error getting due campaigns: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to retrieve due campaigns'}), 500

