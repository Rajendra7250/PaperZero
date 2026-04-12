import uuid
from flask import Blueprint, request, jsonify
from flask_login import login_required
from models import db, Workflow

workflows_bp = Blueprint("workflows", __name__)

MAX_MONTHLY = 10_000  # sanity cap for input


def _compute_score(monthly: int, digitized: bool) -> int:
    """Higher sheets + not digitized = higher priority score."""
    if digitized:
        return min(100, 70 + max(0, monthly // 100))
    return min(95, max(10, round(monthly / 15)))


@workflows_bp.route("/", methods=["GET"])
@login_required
def get_workflows():
    dept = request.args.get("dept", "").strip()
    query = Workflow.query
    if dept:
        query = query.filter_by(dept=dept)
    return jsonify([w.to_dict() for w in query.order_by(Workflow.monthly.desc()).all()])


@workflows_bp.route("/", methods=["POST"])
@login_required
def add_workflow():
    data = request.get_json(silent=True) or {}

    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Workflow name is required."}), 400

    try:
        monthly = int(data.get("monthly", 100))
        if not (1 <= monthly <= MAX_MONTHLY):
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({"error": f"'monthly' must be an integer between 1 and {MAX_MONTHLY}."}), 400

    dept = (data.get("dept") or "Admin").strip()

    wf = Workflow(
        id=str(uuid.uuid4()),
        name=name,
        dept=dept,
        monthly=monthly,
        digitized=False,
    )
    wf.score = _compute_score(monthly, wf.digitized)

    db.session.add(wf)
    db.session.commit()
    return jsonify(wf.to_dict()), 201


@workflows_bp.route("/<wf_id>", methods=["PATCH"])
@login_required
def update_workflow(wf_id):
    wf = Workflow.query.get_or_404(wf_id)
    data = request.get_json(silent=True) or {}

    if "digitized" in data:
        wf.digitized = bool(data["digitized"])
    if "name" in data:
        name = data["name"].strip()
        if not name:
            return jsonify({"error": "Name cannot be empty."}), 400
        wf.name = name
    if "monthly" in data:
        try:
            monthly = int(data["monthly"])
            if not (1 <= monthly <= MAX_MONTHLY):
                raise ValueError
            wf.monthly = monthly
        except (ValueError, TypeError):
            return jsonify({"error": f"'monthly' must be 1–{MAX_MONTHLY}."}), 400

    wf.score = _compute_score(wf.monthly, wf.digitized)
    db.session.commit()
    return jsonify(wf.to_dict())


@workflows_bp.route("/<wf_id>", methods=["DELETE"])
@login_required
def delete_workflow(wf_id):
    wf = Workflow.query.get_or_404(wf_id)
    db.session.delete(wf)
    db.session.commit()
    return jsonify({"message": f"Workflow '{wf.name}' deleted."}), 200