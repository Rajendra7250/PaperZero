from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


# ─── User ─────────────────────────────────────────────────────────────────────
class User(UserMixin, db.Model):
    __tablename__ = "users"

    id       = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email    = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    role     = db.Column(db.String(20), default="staff")  # admin | staff

    def set_password(self, raw_password: str):
        self.password = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password, raw_password)

    def to_dict(self):
        return {"id": self.id, "username": self.username,
                "email": self.email, "role": self.role}


# ─── Workflow ──────────────────────────────────────────────────────────────────
class Workflow(db.Model):
    __tablename__ = "workflows"

    id        = db.Column(db.String(36), primary_key=True)   # full UUID
    name      = db.Column(db.String(120), nullable=False)
    dept      = db.Column(db.String(80), nullable=False, default="Admin")
    monthly   = db.Column(db.Integer, nullable=False, default=100)
    score     = db.Column(db.Integer, nullable=False, default=50)
    digitized = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "dept": self.dept,
            "monthly": self.monthly, "score": self.score,
            "digitized": self.digitized,
        }


# ─── Approval ─────────────────────────────────────────────────────────────────
class Approval(db.Model):
    __tablename__ = "approvals"

    id          = db.Column(db.String(36), primary_key=True)
    name        = db.Column(db.String(120), nullable=False)
    initials    = db.Column(db.String(4), nullable=False)
    doc         = db.Column(db.String(200), nullable=False)
    dept        = db.Column(db.String(80), nullable=False, default="Admin")
    urgent      = db.Column(db.Boolean, default=False)
    status      = db.Column(db.String(20), default="pending")  # pending|approved|rejected
    submitted   = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    resolved_at = db.Column(db.Date, nullable=True)

    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "initials": self.initials,
            "doc": self.doc, "dept": self.dept, "urgent": self.urgent,
            "status": self.status,
            "submitted":    self.submitted.isoformat() if self.submitted else None,
            "resolved_at":  self.resolved_at.isoformat() if self.resolved_at else None,
        }


# ─── Document ─────────────────────────────────────────────────────────────────
class Document(db.Model):
    __tablename__ = "documents"

    id       = db.Column(db.String(36), primary_key=True)
    name     = db.Column(db.String(200), nullable=False)
    type     = db.Column(db.String(10), nullable=False)    # PDF | DOCX | XLSX
    category = db.Column(db.String(80), nullable=False)
    size     = db.Column(db.String(20), nullable=False)
    date     = db.Column(db.String(20), nullable=False)

    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "type": self.type,
            "category": self.category, "size": self.size, "date": self.date,
        }