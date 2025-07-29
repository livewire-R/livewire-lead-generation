from flask import Blueprint, request, jsonify, current_app
from flask_cors import cross_origin
import jwt
from functools import wraps
import logging
from datetime import datetime

from src.models.lead import Lead, Campaign, db
from src.models.client import Client
from src.services.lead_generator import LeadCriteria, LeadGenerationService

logger = logging.getLogger(__name__)

leads_bp = Blueprint("leads", __name__)

def token_required(f):
    """Decorator to require JWT token for protected routes"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")
        
        if not token:
            return jsonify({"error": "Token is missing"}), 401
        
        try:
            if token.startswith("Bearer "):
                token = token[7:]
            
            data = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
            current_client_id = data["client_id"]
            
            # Verify client exists and is active
            client = Client.query.get(current_client_id)
            if not client or client.status != "active":
                return jsonify({"error": "Invalid or inactive client"}), 401
            
            return f(current_client_id, *args, **kwargs)
            
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
    
    return decorated

@leads_bp.route("/generate", methods=["POST"])
@cross_origin()
@token_required
def generate_leads(current_client_id):
    """
    Generate leads based on criteria
    
    Expected JSON payload:
    {
        "keywords": "CEO marketing director",
        "industries": ["Technology", "Healthcare"],
        "locations": ["Sydney", "Melbourne"],
        "titles": ["CEO", "Marketing Director"],
        "company_sizes": ["medium", "large"],
        "min_score": 70,
        "max_results": 50,
        "verify_emails": true,
        "enrich_linkedin": true,
        "campaign_id": "optional-campaign-id"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Create lead criteria from request
        criteria = LeadCriteria(
            keywords=data.get("keywords", ""),
            industries=data.get("industries", []),
            locations=data.get("locations", ["Australia"]),  # Default to Australia
            titles=data.get("titles", []),
            company_sizes=data.get("company_sizes", []),
            min_score=data.get("min_score", 60),
            max_results=min(data.get("max_results", 100), 500),  # Cap at 500
            verify_emails=data.get("verify_emails", True),
            enrich_linkedin=data.get("enrich_linkedin", True)
        )
        
        campaign_id = data.get("campaign_id")
        
        # Generate leads
        lead_service = LeadGenerationService()
        result = lead_service.generate_leads(current_client_id, criteria, campaign_id)
        
        if result["success"]:
            logger.info(f"Generated {result["leads_generated"]} leads for client {current_client_id}")
            return jsonify(result), 200
        else:
            logger.error(f"Lead generation failed for client {current_client_id}: {result.get("error")}")
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Lead generation endpoint error: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Internal server error",
            "message": str(e)
        }), 500

@leads_bp.route("/suggestions", methods=["POST"])
@cross_origin()
@token_required
def get_lead_suggestions(current_client_id):
    """
    Get lead suggestions for preview without generating actual leads
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Create criteria for suggestions
        criteria = LeadCriteria(
            keywords=data.get("keywords", ""),
            industries=data.get("industries", []),
            locations=data.get("locations", ["Australia"]),
            titles=data.get("titles", []),
            company_sizes=data.get("company_sizes", []),
            min_score=data.get("min_score", 60)
        )
        
        # Get suggestions
        lead_service = LeadGenerationService()
        result = lead_service.get_lead_suggestions(current_client_id, criteria)
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Lead suggestions endpoint error: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Internal server error",
            "message": str(e)
        }), 500

@leads_bp.route("/", methods=["GET"])
@cross_origin()
@token_required
def get_leads(current_client_id):
    """
    Get leads for current client with filtering and pagination
    
    Query parameters:
    - page: Page number (default: 1)
    - per_page: Results per page (default: 25, max: 100)
    - status: Filter by status (new, contacted, qualified, converted, rejected)
    - min_score: Minimum lead score
    - campaign_id: Filter by campaign
    - search: Search in name, email, company
    - sort_by: Sort field (score, created_at, name, company)
    - sort_order: Sort order (asc, desc)
    """
    try:
        # Parse query parameters
        page = int(request.args.get("page", 1))
        per_page = min(int(request.args.get("per_page", 25)), 100)
        status = request.args.get("status")
        min_score = request.args.get("min_score", type=int)
        campaign_id = request.args.get("campaign_id")
        search = request.args.get("search", "").strip()
        sort_by = request.args.get("sort_by", "created_at")
        sort_order = request.args.get("sort_order", "desc")
        
        # Build query
        query = Lead.query.filter_by(client_id=current_client_id)
        
        # Apply filters
        if status:
            query = query.filter(Lead.status == status)
        
        if min_score:
            query = query.filter(Lead.score >= min_score)
        
        if campaign_id:
            query = query.filter(Lead.campaign_id == campaign_id)
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                db.or_(
                    Lead.name.ilike(search_term),
                    Lead.email.ilike(search_term),
                    Lead.company.ilike(search_term)
                )
            )
        
        # Apply sorting
        if sort_by == "score":
            order_column = Lead.score
        elif sort_by == "name":
            order_column = Lead.name
        elif sort_by == "company":
            order_column = Lead.company
        else:
            order_column = Lead.created_at
        
        if sort_order == "asc":
            query = query.order_by(order_column.asc())
        else:
            query = query.order_by(order_column.desc())
        
        # Paginate
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        leads = pagination.items
        
        return jsonify({
            "success": True,
            "leads": [lead.to_dict() for lead in leads],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": pagination.total,
                "pages": pagination.pages,
                "has_next": pagination.has_next,
                "has_prev": pagination.has_prev
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get leads endpoint error: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Internal server error",
            "message": str(e)
        }), 500

@leads_bp.route("/<lead_id>", methods=["GET"])
@cross_origin()
@token_required
def get_lead(current_client_id, lead_id):
    """Get single lead by ID"""
    try:
        lead = Lead.query.filter_by(id=lead_id, client_id=current_client_id).first()
        
        if not lead:
            return jsonify({"error": "Lead not found"}), 404
        
        return jsonify({
            "success": True,
            "lead": lead.to_dict(include_raw_data=True)
        }), 200
        
    except Exception as e:
        logger.error(f"Get lead endpoint error: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Internal server error",
            "message": str(e)
        }), 500

@leads_bp.route("/<lead_id>/status", methods=["PUT"])
@cross_origin()
@token_required
def update_lead_status(current_client_id, lead_id):
    """
    Update lead status
    
    Expected JSON payload:
    {
        "status": "contacted",
        "notes": "Called and left voicemail"
    }
    """
    try:
        data = request.get_json()
        
        if not data or "status" not in data:
            return jsonify({"error": "Status is required"}), 400
        
        lead = Lead.query.filter_by(id=lead_id, client_id=current_client_id).first()
        
        if not lead:
            return jsonify({"error": "Lead not found"}), 404
        
        valid_statuses = ["new", "contacted", "qualified", "converted", "rejected"]
        new_status = data["status"]
        
        if new_status not in valid_statuses:
            return jsonify({"error": f"Invalid status. Must be one of: {valid_statuses}"}), 400
        
        notes = data.get("notes", "")
        lead.update_status(new_status, notes)
        
        return jsonify({
            "success": True,
            "lead": lead.to_dict(),
            "message": f"Lead status updated to {new_status}"
        }), 200
        
    except Exception as e:
        logger.error(f"Update lead status endpoint error: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Internal server error",
            "message": str(e)
        }), 500

@leads_bp.route("/stats", methods=["GET"])
@cross_origin()
@token_required
def get_lead_stats(current_client_id):
    """
    Get lead statistics for current client"""
    try:
        # Get basic counts
        total_leads = Lead.query.filter_by(client_id=current_client_id).count()
        
        # Status breakdown
        status_stats = db.session.query(
            Lead.status,
            db.func.count(Lead.id).label("count")
        ).filter_by(client_id=current_client_id).group_by(Lead.status).all()
        
        status_breakdown = {status: count for status, count in status_stats}
        
        # Score distribution
        score_ranges = [
            (90, 100, "excellent"),
            (80, 89, "very_good"),
            (70, 79, "good"),
            (60, 69, "fair"),
            (0, 59, "poor")
        ]
        
        score_breakdown = {}
        for min_score, max_score, label in score_ranges:
            count = Lead.query.filter_by(client_id=current_client_id).filter(
                Lead.score >= min_score,
                Lead.score <= max_score
            ).count()
            score_breakdown[label] = count
        
        # Recent activity (last 30 days)
        from datetime import datetime, timedelta
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        recent_leads = Lead.query.filter_by(client_id=current_client_id).filter(
            Lead.created_at >= thirty_days_ago
        ).count()
        
        # Average score
        avg_score_result = db.session.query(
            db.func.avg(Lead.score)
        ).filter_by(client_id=current_client_id).scalar()
        
        avg_score = round(avg_score_result, 1) if avg_score_result else 0
        
        # Top sources
        source_stats = db.session.query(
            Lead.source,
            db.func.count(Lead.id).label("count")
        ).filter_by(client_id=current_client_id).group_by(Lead.source).all()
        
        source_breakdown = {source: count for source, count in source_stats}
        
        return jsonify({
            "success": True,
            "stats": {
                "total_leads": total_leads,
                "recent_leads": recent_leads,
                "average_score": avg_score,
                "status_breakdown": status_breakdown,
                "score_breakdown": score_breakdown,
                "source_breakdown": source_breakdown
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get lead stats endpoint error: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Internal server error",
            "message": str(e)
        }), 500

@leads_bp.route("/export", methods=["GET"])
@cross_origin()
@token_required
def export_leads(current_client_id):
    """
    Export leads as CSV"""
    try:
        import csv
        import io
        
        # Get leads with same filtering as get_leads
        query = Lead.query.filter_by(client_id=current_client_id)
        
        # Apply filters from query parameters
        status = request.args.get("status")
        min_score = request.args.get("min_score", type=int)
        campaign_id = request.args.get("campaign_id")
        
        if status:
            query = query.filter(Lead.status == status)
        if min_score:
            query = query.filter(Lead.score >= min_score)
        if campaign_id:
            query = query.filter(Lead.campaign_id == campaign_id)
        
        leads = query.order_by(Lead.created_at.desc()).all()
        
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            "Name", "Email", "Phone", "Company", "Title", "Industry",
            "Location", "LinkedIn URL", "Score", "Status", "Email Verified",
            "Source", "Created At"
        ])
        
        # Write data
        for lead in leads:
            writer.writerow([
                lead.name,
                lead.email,
                lead.phone,
                lead.company,
                lead.title,
                lead.industry,
                lead.location,
                lead.linkedin_url,
                lead.score,
                lead.status,
                "Yes" if lead.email_verified else "No",
                lead.source,
                lead.created_at.strftime("%Y-%m-%d %H:%M:%S")
            ])
        
        output.seek(0)
        csv_data = output.getvalue()
        
        return jsonify({
            "success": True,
            "csv_data": csv_data,
            "filename": f"livewire_leads_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"
        }), 200
        
    except Exception as e:
        logger.error(f"Export leads endpoint error: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Internal server error",
            "message": str(e)
        }), 500

