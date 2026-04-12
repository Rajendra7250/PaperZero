from flask import Blueprint, request, jsonify
from flask_login import login_required
from models import Document

documents_bp = Blueprint("documents", __name__)


@documents_bp.route("/", methods=["GET"])
@login_required
def get_documents():
    q   = (request.args.get("q") or "").strip().lower()
    cat = (request.args.get("category") or "").strip()

    query = Document.query
    if cat:
        query = query.filter_by(category=cat)

    results = query.all()
    if q:
        results = [
            d for d in results
            if q in d.name.lower() or q in d.category.lower()
        ]
    return jsonify([d.to_dict() for d in results])