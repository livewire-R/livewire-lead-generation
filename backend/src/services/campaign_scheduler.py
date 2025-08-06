import time
import threading
import logging
from datetime import datetime, timedelta
from typing import List, Optional
import schedule

from models.campaign import Campaign, CampaignExecution, CampaignScheduler, db
from models.client import Client
from services.lead_generator import LeadGenerator

logger = logging.getLogger(__name__)

class AutomatedCampaignScheduler:
    """Service for running automated campaign scheduling"""
    
    def __init__(self, app=None):
        self.app = app
        self.running = False
        self.scheduler_thread = None
        self.lead_generator = LeadGenerator()
        
    def init_app(self, app):
        """Initialize with Flask app"""
        self.app = app
        
    def start_scheduler(self):
        """Start the campaign scheduler in a background thread"""
        if self.running:
            logger.warning("Campaign scheduler is already running")
            return
            
        self.running = True
        
        # Schedule the campaign check to run every minute
        schedule.every(1).minutes.do(self._check_and_run_campaigns)
        
        # Start scheduler thread
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("Campaign scheduler started")
        
    def stop_scheduler(self):
        """Stop the campaign scheduler"""
        self.running = False
        schedule.clear()
        
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
            
        logger.info("Campaign scheduler stopped")
        
    def _run_scheduler(self):
        """Main scheduler loop"""
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error in scheduler loop: {str(e)}")
                time.sleep(5)  # Wait before retrying
                
    def _check_and_run_campaigns(self):
        """Check for due campaigns and execute them"""
        if not self.app:
            logger.error("Flask app not initialized")
            return
            
        with self.app.app_context():
            try:
                # Get campaigns that are due to run
                due_campaigns = CampaignScheduler.get_due_campaigns()
                
                if not due_campaigns:
                    logger.debug("No campaigns due to run")
                    return
                    
                logger.info(f"Found {len(due_campaigns)} campaigns due to run")
                
                for campaign in due_campaigns:
                    try:
                        self._execute_campaign(campaign)
                    except Exception as e:
                        logger.error(f"Error executing campaign {campaign.id}: {str(e)}")
                        
            except Exception as e:
                logger.error(f"Error checking due campaigns: {str(e)}")
                
    def _execute_campaign(self, campaign: Campaign):
        """Execute a single campaign"""
        logger.info(f"Executing campaign {campaign.id} ({campaign.name}) for client {campaign.client_id}")
        
        # Check if campaign has reached limits
        if campaign.has_reached_total_limit():
            logger.info(f"Campaign {campaign.id} has reached total lead limit, marking as completed")
            campaign.status = 'completed'
            db.session.commit()
            return
            
        # Create execution record
        execution = CampaignExecution(
            campaign_id=campaign.id,
            status='running'
        )
        db.session.add(execution)
        db.session.commit()
        
        try:
            # Get campaign criteria
            criteria = campaign.get_criteria()
            
            # Ensure max_results doesn't exceed campaign limit
            max_results = min(
                campaign.max_leads_per_run,
                (campaign.max_leads_total - campaign.total_leads_generated) if campaign.max_leads_total else campaign.max_leads_per_run
            )
            
            if max_results <= 0:
                logger.info(f"Campaign {campaign.id} has reached total limit")
                execution.mark_completed(0, {'message': 'Total lead limit reached'})
                campaign.status = 'completed'
                db.session.commit()
                return
                
            criteria['max_results'] = max_results
            
            # Generate leads
            logger.info(f"Generating {max_results} leads for campaign {campaign.id}")
            results = self.lead_generator.generate_leads(
                client_id=campaign.client_id,
                criteria=criteria,
                max_results=max_results
            )
            
            leads_generated = len(results.get('leads', []))
            
            # Update execution record
            execution.mark_completed(leads_generated, results)
            
            # Update API usage tracking
            if 'api_usage' in results:
                api_usage = results['api_usage']
                execution.apollo_calls = api_usage.get('apollo_calls', 0)
                execution.hunter_calls = api_usage.get('hunter_calls', 0)
                execution.linkedin_calls = api_usage.get('linkedin_calls', 0)
            
            # Update campaign
            campaign.update_after_run(leads_generated)
            
            db.session.commit()
            
            logger.info(f"Campaign {campaign.id} executed successfully: {leads_generated} leads generated")
            
        except Exception as e:
            logger.error(f"Campaign {campaign.id} execution failed: {str(e)}")
            execution.mark_failed(str(e))
            db.session.commit()
            
    def get_scheduler_status(self) -> dict:
        """Get current scheduler status"""
        return {
            'running': self.running,
            'thread_alive': self.scheduler_thread.is_alive() if self.scheduler_thread else False,
            'scheduled_jobs': len(schedule.jobs),
            'next_run': str(schedule.next_run()) if schedule.jobs else None
        }
        
    def force_check_campaigns(self):
        """Manually trigger campaign check (for testing)"""
        if not self.app:
            logger.error("Flask app not initialized")
            return False
            
        with self.app.app_context():
            try:
                self._check_and_run_campaigns()
                return True
            except Exception as e:
                logger.error(f"Error in force check: {str(e)}")
                return False


class CampaignExecutionService:
    """Service for managing campaign executions"""
    
    @staticmethod
    def get_execution_stats(client_id: str, days: int = 30) -> dict:
        """Get execution statistics for a client"""
        try:
            # Get campaigns for client
            campaigns = Campaign.query.filter_by(client_id=client_id).all()
            campaign_ids = [c.id for c in campaigns]
            
            if not campaign_ids:
                return {
                    'total_executions': 0,
                    'successful_executions': 0,
                    'failed_executions': 0,
                    'total_leads_generated': 0,
                    'success_rate': 0,
                    'avg_leads_per_execution': 0,
                    'executions_by_day': []
                }
            
            # Get executions from last N days
            since_date = datetime.utcnow() - timedelta(days=days)
            executions = CampaignExecution.query.filter(
                CampaignExecution.campaign_id.in_(campaign_ids),
                CampaignExecution.started_at >= since_date
            ).all()
            
            # Calculate stats
            total_executions = len(executions)
            successful_executions = len([e for e in executions if e.status == 'completed'])
            failed_executions = len([e for e in executions if e.status == 'failed'])
            total_leads_generated = sum(e.leads_generated for e in executions if e.status == 'completed')
            
            success_rate = (successful_executions / total_executions * 100) if total_executions > 0 else 0
            avg_leads_per_execution = (total_leads_generated / successful_executions) if successful_executions > 0 else 0
            
            # Group executions by day
            executions_by_day = {}
            for execution in executions:
                day = execution.started_at.date().isoformat()
                if day not in executions_by_day:
                    executions_by_day[day] = {
                        'date': day,
                        'executions': 0,
                        'successful': 0,
                        'failed': 0,
                        'leads_generated': 0
                    }
                
                executions_by_day[day]['executions'] += 1
                if execution.status == 'completed':
                    executions_by_day[day]['successful'] += 1
                    executions_by_day[day]['leads_generated'] += execution.leads_generated
                elif execution.status == 'failed':
                    executions_by_day[day]['failed'] += 1
            
            return {
                'total_executions': total_executions,
                'successful_executions': successful_executions,
                'failed_executions': failed_executions,
                'total_leads_generated': total_leads_generated,
                'success_rate': round(success_rate, 1),
                'avg_leads_per_execution': round(avg_leads_per_execution, 1),
                'executions_by_day': list(executions_by_day.values())
            }
            
        except Exception as e:
            logger.error(f"Error getting execution stats: {str(e)}")
            return {
                'error': str(e),
                'total_executions': 0,
                'successful_executions': 0,
                'failed_executions': 0,
                'total_leads_generated': 0,
                'success_rate': 0,
                'avg_leads_per_execution': 0,
                'executions_by_day': []
            }
    
    @staticmethod
    def get_recent_executions(client_id: str, limit: int = 10) -> List[dict]:
        """Get recent executions for a client"""
        try:
            # Get campaigns for client
            campaigns = Campaign.query.filter_by(client_id=client_id).all()
            campaign_ids = [c.id for c in campaigns]
            
            if not campaign_ids:
                return []
            
            # Get recent executions
            executions = CampaignExecution.query.filter(
                CampaignExecution.campaign_id.in_(campaign_ids)
            ).order_by(CampaignExecution.started_at.desc()).limit(limit).all()
            
            # Include campaign names
            result = []
            for execution in executions:
                execution_dict = execution.to_dict()
                campaign = Campaign.query.get(execution.campaign_id)
                execution_dict['campaign_name'] = campaign.name if campaign else 'Unknown'
                result.append(execution_dict)
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting recent executions: {str(e)}")
            return []
    
    @staticmethod
    def cancel_running_executions(campaign_id: str) -> int:
        """Cancel all running executions for a campaign"""
        try:
            running_executions = CampaignExecution.query.filter_by(
                campaign_id=campaign_id,
                status='running'
            ).all()
            
            count = 0
            for execution in running_executions:
                execution.status = 'cancelled'
                execution.completed_at = datetime.utcnow()
                execution.duration_seconds = int((execution.completed_at - execution.started_at).total_seconds())
                count += 1
            
            db.session.commit()
            return count
            
        except Exception as e:
            logger.error(f"Error cancelling executions: {str(e)}")
            return 0


# Global scheduler instance
campaign_scheduler = AutomatedCampaignScheduler()

def init_campaign_scheduler(app):
    """Initialize campaign scheduler with Flask app"""
    campaign_scheduler.init_app(app)
    
    # Start scheduler if not in testing mode
    if not app.config.get('TESTING', False):
        campaign_scheduler.start_scheduler()
        
    return campaign_scheduler

