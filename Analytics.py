from flask import Blueprint, jsonify
from flask_login import login_required
from models import Workflow, Approval
from sqlalchemy import func

analytics_bp = Blueprint("analytics", __name__)

# Static analytics data (replace with real DB aggregation as the app grows)
_MONTHLY_USAGE  = [18200, 16400, 15100, 13800, 11200, 9400]
_MONTHLY_LABELS = ["Nov", "Dec", "Jan", "Feb", "Mar", "Apr"]
_DEPT_USAGE     = [3200, 2100, 4100, 900, 1100]
_DEPT_LABELS    = ["Admin", "Finance", "Academic", "Library", "HR"]
_WEEKLY_USAGE   = [420, 380, 510, 290, 340]
_WEEKLY_LABELS  = ["Mon", "Tue", "Wed", "Thu", "Fri"]

_RECOMMENDATIONS = [
    {"id": "r1", "title": "Digitize Exam Hall Tickets Fully",   "priority": "high", "impact": "~1,200 sheets/month", "desc": "Replace printed hall tickets with QR-based digital passes."},
    {"id": "r2", "title": "Implement E-Leave Management",        "priority": "high", "impact": "~320 sheets/month",  "desc": "Deploy automated leave approval chain with email/SMS notifications."},
    {"id": "r3", "title": "Switch to Digital Fee Receipts",      "priority": "high", "impact": "~900 sheets/month",  "desc": "Integrate payment gateway with automated PDF receipt emailing."},
    {"id": "r4", "title": "QR-Based Library System",             "priority": "med",  "impact": "~450 sheets/month",  "desc": "Replace issue slips with QR scan-in/scan-out using student IDs."},
    {"id": "r5", "title": "Automate Bonafide Generation",        "priority": "med",  "impact": "~280 sheets/month",  "desc": "Self-service portal for students with digital institutional seal."},
    {"id": "r6", "title": "Digital Notice Boards",               "priority": "med",  "impact": "~180 sheets/month",  "desc": "Replace printed circulars with push notifications and digital displays."},
    {"id": "r7", "title": "Eliminate Budget Requisition Trail",  "priority": "low",  "impact": "~140 sheets/month",  "desc": "Digital budget tracking with role-based approvals and auto audit trail."},
    {"id": "r8", "title": "E-Certificates for Events",           "priority": "low",  "impact": "~90 sheets/month",   "desc": "Digitally signed PDF certificates with online verification."},
]


@analytics_bp.route("/", methods=["GET"])
@login_required
def get_analytics():
    # Compute live stats from the DB
    total_monthly    = Workflow.query.with_entities(func.sum(Workflow.monthly)).scalar() or 0
    digitized_count  = Workflow.query.filter_by(digitized=True).count()
    total_workflows  = Workflow.query.count()
    digitization_pct = round(digitized_count / total_workflows * 100) if total_workflows else 0

    # Rough sustainability estimates
    paper_saved = int(total_monthly * (digitization_pct / 100))
    cost_saved  = round(paper_saved * 2.58)    # ~₹2.58 per sheet
    co2_avoided = round(paper_saved * 0.000498, 2)  # kg CO₂ per sheet

    return jsonify({
        "paper_saved":        paper_saved,
        "cost_saved":         cost_saved,
        "co2_avoided":        co2_avoided,
        "digitized_workflows": digitized_count,
        "total_workflows":     total_workflows,
        "digitization_pct":   digitization_pct,
        "monthly_usage":      _MONTHLY_USAGE,
        "monthly_labels":     _MONTHLY_LABELS,
        "dept_usage":         _DEPT_USAGE,
        "dept_labels":        _DEPT_LABELS,
        "weekly_usage":       _WEEKLY_USAGE,
        "weekly_labels":      _WEEKLY_LABELS,
    })


@analytics_bp.route("/recommendations", methods=["GET"])
@login_required
def get_recommendations():
    priority = (request.args.get("priority") or "").strip().lower()
    valid = {"high", "med", "low", ""}
    if priority not in valid:
        return jsonify({"error": "priority must be 'high', 'med', or 'low'."}), 400

    result = [r for r in _RECOMMENDATIONS if not priority or r["priority"] == priority]
    return jsonify(result)


@analytics_bp.route("/dashboard", methods=["GET"])
@login_required
def get_dashboard():
    pending_count    = Approval.query.filter_by(status="pending").count()
    digitized_count  = Workflow.query.filter_by(digitized=True).count()
    total_workflows  = Workflow.query.count()
    digitization_pct = round(digitized_count / total_workflows * 100) if total_workflows else 0
    total_monthly    = Workflow.query.with_entities(func.sum(Workflow.monthly)).scalar() or 0
    paper_saved      = int(total_monthly * (digitization_pct / 100))

    return jsonify({
        "paper_saved":         paper_saved,
        "cost_saved":          round(paper_saved * 2.58),
        "co2_avoided":         round(paper_saved * 0.000498, 2),
        "digitized_workflows": digitized_count,
        "total_workflows":     total_workflows,
        "pending_approvals":   pending_count,
        "progress": [
            {"label": "Student Admission Forms", "pct": 100},
            {"label": "Leave Applications",      "pct": 88},
            {"label": "Fee Receipts",             "pct": 72},
            {"label": "Exam Hall Tickets",        "pct": 45},
            {"label": "Certificates / NOC",       "pct": 18},
        ],
    })