"""
ECO_FLOW — College Edition
---------------------------
Features:
  - User registration & login (stored in SQLite)
  - Departments: CSE, AIML, ECE, EEE, Mechanical, Civil
  - Workflows & Approvals (leave, NOC, bonafide)
  - Daily Announcements / Notice Board
  - Attendance Tracking
  - Timetable
  - Exam Schedule
  - Library Book Issues
  - Fee Payment Status
  - Analytics & Recommendations

Run:  python app.py
"""

import os
from datetime import date, datetime, timedelta
import uuid

from dotenv import load_dotenv
load_dotenv()

from flask import Flask, jsonify, request, render_template, redirect, url_for, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin,
    login_user, logout_user, login_required, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy import func

# ─── App Setup ────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.config["SECRET_KEY"]                     = os.getenv("SECRET_KEY", "ecoflow-college-secret-2025")
app.config["SQLALCHEMY_DATABASE_URI"]        = os.getenv("DATABASE_URL", "sqlite:///ecoflow_college.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

CORS(app, origins=os.getenv("CORS_ORIGINS", "http://localhost:5000").split(","),
     supports_credentials=True)

db            = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login_page"

# ─── Upload Config ────────────────────────────────────────────────────────────
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads', 'approvals')
DOCS_UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads', 'documents')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DOCS_UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DOCS_UPLOAD_FOLDER'] = DOCS_UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024  # 20 MB max upload

# ─── Constants ────────────────────────────────────────────────────────────────
DEPARTMENTS = ["CSE", "AIML", "ECE", "EEE", "Mechanical", "Civil", "Admin", "Library", "Finance", "HR"]
ROLES       = ["admin", "hod", "student"]


# ══════════════════════════════════════════════════════════════════════════════
# MODELS
# ══════════════════════════════════════════════════════════════════════════════

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id         = db.Column(db.Integer, primary_key=True)
    username   = db.Column(db.String(80),  unique=True, nullable=False)
    email      = db.Column(db.String(120), unique=True, nullable=False)
    password   = db.Column(db.String(256), nullable=False)
    full_name  = db.Column(db.String(120), default="")
    role       = db.Column(db.String(20),  default="student")   # admin|hod|faculty|student
    department = db.Column(db.String(50),  default="CSE")
    year       = db.Column(db.Integer,     nullable=True)        # 1–4 for students
    usn        = db.Column(db.String(20),  nullable=True)        # student roll number
    streak_count = db.Column(db.Integer,   default=0)
    eco_points   = db.Column(db.Integer,   default=0)   # Gamification: points for paper saved
    last_active_date = db.Column(db.Date,  nullable=True)
    created_at = db.Column(db.DateTime,    default=datetime.utcnow)

    def set_password(self, raw):
        self.password = generate_password_hash(raw)

    def check_password(self, raw):
        return check_password_hash(self.password, raw)

    def add_points(self, pts):
        self.eco_points += pts
        # Bonus: build streak if they take action
        today = date.today()
        if self.last_active_date != today:
            if self.last_active_date == today - timedelta(days=1):
                self.streak_count += 1
            else:
                self.streak_count = 1
            self.last_active_date = today

    def to_dict(self):
        return {
            "id": self.id, "username": self.username, "email": self.email,
            "full_name": self.full_name, "role": self.role,
            "department": self.department, "year": self.year, "usn": self.usn,
            "streak_count": self.streak_count, "eco_points": self.eco_points
        }


class Workflow(db.Model):
    __tablename__ = "workflows"
    id        = db.Column(db.String(36), primary_key=True)
    name      = db.Column(db.String(120), nullable=False)
    dept      = db.Column(db.String(80),  default="Admin")
    monthly   = db.Column(db.Integer,     default=100)
    score     = db.Column(db.Integer,     default=50)
    digitized = db.Column(db.Boolean,     default=False)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "dept": self.dept,
                "monthly": self.monthly, "score": self.score, "digitized": self.digitized}


class Approval(db.Model):
    __tablename__ = "approvals"
    id          = db.Column(db.String(36), primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    name        = db.Column(db.String(120), nullable=False)
    initials    = db.Column(db.String(4),   nullable=False)
    doc         = db.Column(db.String(200), nullable=False)
    dept        = db.Column(db.String(80),  default="Admin")
    urgent      = db.Column(db.Boolean,     default=False)
    remarks     = db.Column(db.Text,         nullable=True)
    status      = db.Column(db.String(20),  default="pending")
    submitted   = db.Column(db.Date,        default=date.today)
    resolved_at = db.Column(db.Date,        nullable=True)
    rejection_reason = db.Column(db.Text,   nullable=True)
    attachment  = db.Column(db.String(300), nullable=True)   # uploaded filename

    def to_dict(self):
        def parse_date(d):
            if not d: return None
            if isinstance(d, str): return d
            try: return d.isoformat()
            except: return str(d)

        return {
            "id": self.id, "name": self.name, "initials": self.initials,
            "doc": self.doc, "dept": self.dept, "urgent": self.urgent,
            "status": self.status,
            "remarks": self.remarks,
            "submitted":   parse_date(self.submitted),
            "resolved_at": parse_date(self.resolved_at),
            "rejection_reason": self.rejection_reason,
            "attachment": self.attachment,
        }


class Document(db.Model):
    __tablename__ = "documents"
    id       = db.Column(db.String(36), primary_key=True)
    name     = db.Column(db.String(200), nullable=False)
    type     = db.Column(db.String(10),  nullable=False)
    category = db.Column(db.String(80),  nullable=False)
    size     = db.Column(db.String(20),  nullable=False)
    date     = db.Column(db.String(20),  nullable=False)
    filepath = db.Column(db.String(300), nullable=True) # allow storing upload path

    def to_dict(self):
        return {"id": self.id, "name": self.name, "type": self.type,
                "category": self.category, "size": self.size, "date": self.date}


class Announcement(db.Model):
    """Daily notice board entries."""
    __tablename__ = "announcements"
    id         = db.Column(db.String(36),  primary_key=True)
    title      = db.Column(db.String(200), nullable=False)
    body       = db.Column(db.Text,        nullable=False)
    dept       = db.Column(db.String(80),  default="All")   # "All" = college-wide
    category   = db.Column(db.String(50),  default="General")  # General|Exam|Event|Holiday|Fee
    priority   = db.Column(db.String(10),  default="normal")   # normal|high|urgent
    posted_by  = db.Column(db.String(120), nullable=False)
    posted_on  = db.Column(db.Date,        default=date.today)
    expires_on = db.Column(db.Date,        nullable=True)

    def to_dict(self):
        return {
            "id": self.id, "title": self.title, "body": self.body,
            "dept": self.dept, "category": self.category, "priority": self.priority,
            "posted_by": self.posted_by,
            "posted_on":  self.posted_on.isoformat()  if self.posted_on  else None,
            "expires_on": self.expires_on.isoformat() if self.expires_on else None,
        }


class Attendance(db.Model):
    """Per-subject attendance record for a student on a date."""
    __tablename__ = "attendance"
    id         = db.Column(db.String(36), primary_key=True)
    student_id = db.Column(db.Integer,    db.ForeignKey("users.id"), nullable=False)
    subject    = db.Column(db.String(100), nullable=False)
    dept       = db.Column(db.String(50),  nullable=False)
    year       = db.Column(db.Integer,     nullable=False)
    date       = db.Column(db.Date,        nullable=False)
    status     = db.Column(db.String(10),  default="present")   # present|absent|od

    student = db.relationship("User", backref="attendance_records")

    def to_dict(self):
        return {
            "id": self.id, "student_id": self.student_id,
            "subject": self.subject, "dept": self.dept, "year": self.year,
            "date": self.date.isoformat(), "status": self.status,
        }


class TimetableEntry(db.Model):
    """One class slot in the weekly timetable."""
    __tablename__ = "timetable"
    id      = db.Column(db.String(36),  primary_key=True)
    dept    = db.Column(db.String(50),  nullable=False)
    year    = db.Column(db.Integer,     nullable=False)
    day     = db.Column(db.String(10),  nullable=False)   # Mon–Sat
    slot    = db.Column(db.String(20),  nullable=False)   # e.g. "09:00–10:00"
    subject = db.Column(db.String(100), nullable=False)
    faculty = db.Column(db.String(120), default="TBA")
    room    = db.Column(db.String(30),  default="TBA")

    def to_dict(self):
        return {"id": self.id, "dept": self.dept, "year": self.year,
                "day": self.day, "slot": self.slot, "subject": self.subject,
                "faculty": self.faculty, "room": self.room}


class ExamSchedule(db.Model):
    """Exam timetable entry."""
    __tablename__ = "exam_schedule"
    id         = db.Column(db.String(36),  primary_key=True)
    dept       = db.Column(db.String(50),  nullable=False)
    year       = db.Column(db.Integer,     nullable=False)
    subject    = db.Column(db.String(100), nullable=False)
    exam_type  = db.Column(db.String(30),  default="CIE")   # CIE|SEE|Practical
    exam_date  = db.Column(db.Date,        nullable=False)
    start_time = db.Column(db.String(10),  default="10:00")
    hall       = db.Column(db.String(50),  default="TBA")

    def to_dict(self):
        return {
            "id": self.id, "dept": self.dept, "year": self.year,
            "subject": self.subject, "exam_type": self.exam_type,
            "exam_date": self.exam_date.isoformat(), "start_time": self.start_time,
            "hall": self.hall,
        }


class LibraryBook(db.Model):
    """Library book issue record."""
    __tablename__ = "library"
    id           = db.Column(db.String(36),  primary_key=True)
    student_id   = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    book_title   = db.Column(db.String(200), nullable=False)
    book_author  = db.Column(db.String(120), default="Unknown")
    issued_on    = db.Column(db.Date,        default=date.today)
    due_date     = db.Column(db.Date,        nullable=False)
    returned_on  = db.Column(db.Date,        nullable=True)
    fine         = db.Column(db.Float,       default=0.0)

    student = db.relationship("User", backref="borrowed_books")

    def to_dict(self):
        overdue = (
            not self.returned_on
            and date.today() > self.due_date
        )
        return {
            "id": self.id, "student_id": self.student_id,
            "book_title": self.book_title, "book_author": self.book_author,
            "issued_on":   self.issued_on.isoformat(),
            "due_date":    self.due_date.isoformat(),
            "returned_on": self.returned_on.isoformat() if self.returned_on else None,
            "fine": self.fine, "overdue": overdue,
        }


class FeeRecord(db.Model):
    """Semester fee payment record per student."""
    __tablename__ = "fees"
    id           = db.Column(db.String(36),  primary_key=True)
    student_id   = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    semester     = db.Column(db.Integer,     nullable=False)    # 1–8
    amount       = db.Column(db.Float,       nullable=False)
    paid         = db.Column(db.Boolean,     default=False)
    paid_on      = db.Column(db.Date,        nullable=True)
    due_date     = db.Column(db.Date,        nullable=False)
    receipt_no   = db.Column(db.String(50),  nullable=True)

    student = db.relationship("User", backref="fee_records")

    def to_dict(self):
        return {
            "id": self.id, "student_id": self.student_id,
            "semester": self.semester, "amount": self.amount,
            "paid": self.paid,
            "paid_on":  self.paid_on.isoformat()  if self.paid_on  else None,
            "due_date": self.due_date.isoformat(),
            "receipt_no": self.receipt_no,
            "overdue": not self.paid and date.today() > self.due_date,
        }


class ExamResult(db.Model):
    __tablename__ = "exam_results"
    id           = db.Column(db.String(36), primary_key=True)
    student_name = db.Column(db.String(120), nullable=False)
    exam_name    = db.Column(db.String(120), nullable=False)
    dept         = db.Column(db.String(50),   nullable=True)
    year         = db.Column(db.Integer,      nullable=True)
    score        = db.Column(db.Integer, default=0)
    status       = db.Column(db.String(50), default="Completed")

    def to_dict(self):
        return {
            "id": self.id,
            "student_name": self.student_name,
            "exam_name": self.exam_name,
            "dept": self.dept,
            "year": self.year,
            "score": self.score,
            "status": self.status
        }


class OnlineExam(db.Model):
    """Dynamically created exam with questions, scoped to a department and year."""
    __tablename__ = "online_exams"
    id           = db.Column(db.String(36),  primary_key=True)
    title        = db.Column(db.String(200),  nullable=False)
    dept         = db.Column(db.String(50),   nullable=False)
    year         = db.Column(db.Integer,      nullable=True)    # None = all years
    duration     = db.Column(db.Integer,      default=30)
    questions    = db.Column(db.Text,         nullable=False)
    created_by   = db.Column(db.String(120),  nullable=False)
    created_at   = db.Column(db.DateTime,     default=datetime.utcnow)
    is_active    = db.Column(db.Boolean,      default=True)

    def to_dict(self):
        import json
        return {
            "id": self.id,
            "title": self.title,
            "dept": self.dept,
            "year": self.year,
            "duration": self.duration,
            "questions": json.loads(self.questions) if self.questions else [],
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_active": self.is_active,
        }


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ─── Helpers ──────────────────────────────────────────────────────────────────
def new_id():
    return str(uuid.uuid4())

def compute_score(monthly: int, digitized: bool) -> int:
    if digitized:
        return min(100, 70 + max(0, monthly // 100))
    return min(95, max(10, round(monthly / 15)))


# ══════════════════════════════════════════════════════════════════════════════
# SEED DATA
# ══════════════════════════════════════════════════════════════════════════════
def seed_data():
    if User.query.first():
        return

    # ── Users ──
    users_data = [
        ("admin",    "admin@college.edu",         "Admin@1234",    "Admin User",       "admin",   "Admin",      None, None),
        ("hod_cse",  "hod.cse@college.edu",       "Hod@1234",      "Dr. Ramesh Kumar", "hod",     "CSE",        None, None),
        ("hod_aiml", "hod.aiml@college.edu",      "Hod@1234",      "Dr. Priya Nair",   "hod",     "AIML",       None, None),
        ("stu001",   "stu001@college.edu",         "Student@1234",  "Rajendra Kumar",   "student", "CSE",        3,    "1CS21CS001"),
        ("stu002",   "stu002@college.edu",         "Student@1234",  "Priya Sharma",     "student", "AIML",       2,    "1CS21AI002"),
        ("stu003",   "stu003@college.edu",         "Student@1234",  "Vikram Singh",     "student", "ECE",        3,    "1CS21EC003"),
        ("stu004",   "stu004@college.edu",         "Student@1234",  "Meena Iyer",       "student", "EEE",        1,    "1CS24EE004"),
        ("stu005",   "stu005@college.edu",         "Student@1234",  "Deepak Reddy",     "student", "Mechanical", 4,    "1CS20ME005"),
    ]
    user_objs = {}
    for uname, email, pwd, fullname, role, dept, year, usn in users_data:
        u = User(username=uname, email=email, full_name=fullname,
                 role=role, department=dept, year=year, usn=usn)
        u.set_password(pwd)
        db.session.add(u)
        user_objs[uname] = u
    db.session.flush()  # get IDs before using them below

    # ── Workflows (college departments) ──
    wf_data = [
        ("Leave Applications",    "HR",         320,  False),
        ("Bonafide Certificates", "Admin",      280,  False),
        ("Fee Payment Receipts",  "Finance",    900,  False),
        ("Exam Hall Tickets",     "CSE",        1200, False),
        ("Library Issue Slips",   "Library",    450,  True),
        ("Admission Forms",       "Admin",      200,  True),
        ("Budget Requisitions",   "Finance",    140,  False),
        ("NOC / Certificates",    "Admin",      180,  False),
        ("Lab Attendance Sheets", "ECE",        600,  False),
        ("Project Reports",       "AIML",       300,  False),
        ("Workshop Registers",    "Mechanical", 250,  False),
        ("Safety Logs",           "Civil",      120,  False),
    ]
    for name, dept, monthly, digitized in wf_data:
        db.session.add(Workflow(
            id=new_id(), name=name, dept=dept,
            monthly=monthly, digitized=digitized,
            score=compute_score(monthly, digitized)
        ))

    # ── Approvals ──
    ap_data = [
        ("Rajendra Kumar", "RK", "Leave Application – 3 Days",          "CSE",        True,  date(2025,4,9)),
        ("Priya Sharma",   "PS", "Budget Requisition – Lab Equipment",   "Finance",    False, date(2025,4,9)),
        ("Vikram Singh",   "VS", "Bonafide Certificate",                 "Admin",      False, date(2025,4,8)),
        ("Meena Iyer",     "MI", "NOC for Internship",                   "EEE",        True,  date(2025,4,8)),
        ("Deepak Reddy",   "DR", "Exam Repeat Form",                     "Mechanical", False, date(2025,4,7)),
        ("Ananya Joshi",   "AJ", "Lab Access Request",                   "ECE",        False, date(2025,4,7)),
        ("Suresh Kumar",   "SK", "Fee Waiver Application",               "Finance",    True,  date(2025,4,7)),
    ]
    for name, initials, doc, dept, urgent, submitted in ap_data:
        db.session.add(Approval(
            id=new_id(), name=name, initials=initials,
            doc=doc, dept=dept, urgent=urgent, submitted=submitted
        ))

    # ── Announcements ──
    ann_data = [
        ("CIE-1 Results Published",       "CIE-1 results for all 3rd year CSE students are now available on the portal.",
         "CSE",  "Exam",    "high",   "Dr. Ramesh Kumar",  date(2025,4,9),  date(2025,4,30)),
        ("Holiday – Ambedkar Jayanti",    "College will remain closed on 14th April on account of Ambedkar Jayanti.",
         "All",  "Holiday", "normal", "Admin Office",      date(2025,4,8),  date(2025,4,14)),
        ("Library Book Return Reminder",  "All students who have books due before April 15 must return them to avoid fine.",
         "All",  "General", "normal", "Library",           date(2025,4,7),  date(2025,4,15)),
        ("AIML Project Submission",       "Final project reports for 4th sem AIML must be submitted by April 20.",
         "AIML", "Exam",    "urgent", "Dr. Priya Nair",    date(2025,4,6),  date(2025,4,20)),
        ("Fee Payment – Last Date",       "Semester fee payment for odd semester is due by April 30. Pay at finance office.",
         "All",  "Fee",     "high",   "Finance Office",    date(2025,4,5),  date(2025,4,30)),
        ("Campus Recruitment – Infosys",  "Infosys will conduct placement drive on April 25. Eligible: 2025 passouts.",
         "All",  "Event",   "high",   "Placement Cell",    date(2025,4,4),  date(2025,4,25)),
        ("Workshop – Arduino & IoT",      "2-day workshop on Arduino & IoT for ECE/EEE students on April 18–19.",
         "ECE",  "Event",   "normal", "ECE Dept",          date(2025,4,3),  date(2025,4,18)),
    ]
    for title, body, dept, cat, priority, posted_by, posted_on, expires_on in ann_data:
        db.session.add(Announcement(
            id=new_id(), title=title, body=body, dept=dept,
            category=cat, priority=priority, posted_by=posted_by,
            posted_on=posted_on, expires_on=expires_on
        ))

    # ── Timetable (CSE Year 3 sample) ──
    tt_data = [
        ("CSE", 3, "Mon", "09:00–10:00", "Data Structures",       "Prof. Suresh M",  "CS101"),
        ("CSE", 3, "Mon", "10:00–11:00", "Operating Systems",     "Prof. Ananya J",  "CS102"),
        ("CSE", 3, "Mon", "11:15–12:15", "DBMS",                  "Prof. Suresh M",  "CS103"),
        ("CSE", 3, "Mon", "14:00–15:00", "Computer Networks",     "Prof. Ravi T",    "CS104"),
        ("CSE", 3, "Tue", "09:00–10:00", "Operating Systems",     "Prof. Ananya J",  "CS102"),
        ("CSE", 3, "Tue", "10:00–11:00", "Microcontrollers",      "Prof. Kumar B",   "CS105"),
        ("CSE", 3, "Tue", "11:15–12:15", "Data Structures Lab",   "Prof. Suresh M",  "Lab1"),
        ("CSE", 3, "Wed", "09:00–10:00", "DBMS",                  "Prof. Suresh M",  "CS103"),
        ("CSE", 3, "Wed", "10:00–11:00", "Computer Networks",     "Prof. Ravi T",    "CS104"),
        ("CSE", 3, "Wed", "11:15–12:15", "Microcontrollers Lab",  "Prof. Kumar B",   "Lab2"),
        ("CSE", 3, "Thu", "09:00–10:00", "Data Structures",       "Prof. Suresh M",  "CS101"),
        ("CSE", 3, "Thu", "10:00–11:00", "DBMS",                  "Prof. Suresh M",  "CS103"),
        ("CSE", 3, "Thu", "11:15–12:15", "Operating Systems",     "Prof. Ananya J",  "CS102"),
        ("CSE", 3, "Thu", "14:00–15:00", "Seminar",               "TBA",             "Hall A"),
        ("CSE", 3, "Fri", "09:00–10:00", "Computer Networks",     "Prof. Ravi T",    "CS104"),
        ("CSE", 3, "Fri", "10:00–11:00", "Microcontrollers",      "Prof. Kumar B",   "CS105"),
        ("CSE", 3, "Fri", "11:15–12:15", "DBMS Lab",              "Prof. Suresh M",  "Lab3"),
        # AIML Year 2
        ("AIML",2, "Mon", "09:00–10:00", "Machine Learning",      "Dr. Priya Nair",  "AI101"),
        ("AIML",2, "Mon", "10:00–11:00", "Python Programming",    "Prof. Meena S",   "AI102"),
        ("AIML",2, "Tue", "09:00–10:00", "Deep Learning",         "Dr. Priya Nair",  "AI103"),
        ("AIML",2, "Tue", "10:00–11:00", "ML Lab",                "Dr. Priya Nair",  "Lab4"),
    ]
    for dept, year, day, slot, subject, faculty, room in tt_data:
        db.session.add(TimetableEntry(
            id=new_id(), dept=dept, year=year, day=day,
            slot=slot, subject=subject, faculty=faculty, room=room
        ))

    # ── Exam Schedule ──
    exam_data = [
        ("CSE",        3, "Data Structures",      "CIE", date(2025,4,15), "10:00", "Hall A"),
        ("CSE",        3, "Operating Systems",    "CIE", date(2025,4,16), "10:00", "Hall A"),
        ("CSE",        3, "DBMS",                 "CIE", date(2025,4,17), "10:00", "Hall B"),
        ("CSE",        3, "Computer Networks",    "CIE", date(2025,4,18), "10:00", "Hall B"),
        ("AIML",       2, "Machine Learning",     "CIE", date(2025,4,15), "14:00", "Hall C"),
        ("AIML",       2, "Deep Learning",        "CIE", date(2025,4,16), "14:00", "Hall C"),
        ("ECE",        3, "Digital Circuits",     "CIE", date(2025,4,15), "10:00", "Hall D"),
        ("Mechanical", 4, "Thermodynamics",       "SEE", date(2025,5,5),  "10:00", "Hall E"),
        ("Civil",      2, "Structural Analysis",  "CIE", date(2025,4,20), "10:00", "Hall F"),
        ("EEE",        1, "Circuit Theory",       "CIE", date(2025,4,22), "10:00", "Hall G"),
    ]
    for dept, year, subject, etype, edate, stime, hall in exam_data:
        db.session.add(ExamSchedule(
            id=new_id(), dept=dept, year=year, subject=subject,
            exam_type=etype, exam_date=edate, start_time=stime, hall=hall
        ))

    # ── Library ──
    from datetime import timedelta
    stu_id = user_objs["stu001"].id
    lib_data = [
        (stu_id, "Introduction to Algorithms",  "CLRS",            date(2025,3,20), date(2025,4,10)),
        (stu_id, "Operating System Concepts",   "Silberschatz",    date(2025,4,1),  date(2025,4,22)),
        (user_objs["stu002"].id, "Deep Learning","Ian Goodfellow",  date(2025,3,25), date(2025,4,15)),
        (user_objs["stu003"].id, "Signals & Systems","Oppenheim",   date(2025,4,5),  date(2025,4,26)),
    ]
    for sid, title, author, issued, due in lib_data:
        db.session.add(LibraryBook(
            id=new_id(), student_id=sid, book_title=title,
            book_author=author, issued_on=issued, due_date=due
        ))

    # ── Fees ──
    fee_data = [
        (user_objs["stu001"].id, 5, 45000.0, True,  date(2025,1,15), date(2025,1,31), "REC20250115001"),
        (user_objs["stu001"].id, 6, 45000.0, False, None,            date(2025,7,31), None),
        (user_objs["stu002"].id, 3, 45000.0, True,  date(2025,1,10), date(2025,1,31), "REC20250110002"),
        (user_objs["stu003"].id, 5, 48000.0, False, None,            date(2025,4,30), None),
        (user_objs["stu004"].id, 1, 50000.0, True,  date(2024,9,5),  date(2024,9,30), "REC20240905003"),
    ]
    for sid, sem, amt, paid, paid_on, due_date, receipt in fee_data:
        db.session.add(FeeRecord(
            id=new_id(), student_id=sid, semester=sem,
            amount=amt, paid=paid, paid_on=paid_on,
            due_date=due_date, receipt_no=receipt
        ))

    # ── Attendance (sample for stu001) ──
    subjects = ["Data Structures", "Operating Systems", "DBMS", "Computer Networks", "Microcontrollers"]
    for i in range(5):   # last 5 days
        for subj in subjects:
            status = "absent" if (i == 2 and subj == "DBMS") else "present"
            att_date = date(2025, 4, 9 - i)
            db.session.add(Attendance(
                id=new_id(), student_id=user_objs["stu001"].id,
                subject=subj, dept="CSE", year=3,
                date=att_date, status=status
            ))

    # ── Documents ──
    doc_data = [
        ("Admission Policy 2024",  "PDF",  "Admissions", "1.2 MB", "Jan 2024"),
        ("Fee Structure 2024-25",  "XLSX", "Finance",    "340 KB", "Jun 2024"),
        ("Academic Calendar",      "PDF",  "Academic",   "890 KB", "Jul 2024"),
        ("Staff Leave Policy",     "DOCX", "HR",         "220 KB", "Mar 2024"),
        ("Examination Bylaws",     "PDF",  "Academic",   "2.1 MB", "Nov 2023"),
        ("Procurement Rules",      "PDF",  "Compliance", "1.5 MB", "Feb 2024"),
        ("Lab Safety Manual",      "PDF",  "Academic",   "3.2 MB", "Aug 2024"),
        ("Hostel Regulations",     "PDF",  "Compliance", "780 KB", "Jul 2024"),
        ("Anti-Ragging Policy",    "PDF",  "Compliance", "420 KB", "Jan 2024"),
        ("Placement Brochure",     "PDF",  "Placements", "5.1 MB", "Aug 2024"),
    ]
    for name, ftype, cat, size, fdate in doc_data:
        db.session.add(Document(id=new_id(), name=name, type=ftype,
                                category=cat, size=size, date=fdate))

    db.session.commit()
    print("Database seeded with college data.")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE ROUTES
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/")
def index():
    return redirect(url_for("login_page"))

@app.route("/login")
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("index.html")


# ══════════════════════════════════════════════════════════════════════════════
# AUTH API
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/api/register", methods=["POST"])
def api_register():
    data      = request.get_json(silent=True) or {}
    username  = (data.get("username") or "").strip()
    email     = (data.get("email") or "").strip()
    password  = data.get("password") or ""
    full_name = (data.get("full_name") or "").strip()
    role      = (data.get("role") or "student").strip().lower()
    dept      = (data.get("department") or "CSE").strip()
    year      = data.get("year")
    usn       = (data.get("usn") or "").strip() or None

    # Validation
    if not username or not email or not password:
        return jsonify({"error": "username, email, and password are required."}), 400
    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters."}), 400
    if role not in ROLES:
        return jsonify({"error": f"role must be one of: {', '.join(ROLES)}"}), 400
    if dept not in DEPARTMENTS:
        return jsonify({"error": f"department must be one of: {', '.join(DEPARTMENTS)}"}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already taken."}), 409
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered."}), 409

    user = User(username=username, email=email, full_name=full_name,
                role=role, department=dept, usn=usn,
                year=int(year) if year else None)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "Registered successfully.", "user": user.to_dict()}), 201


@app.route("/api/login", methods=["POST"])
def api_login():
    data     = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not username or not password:
        return jsonify({"error": "Username and password are required."}), 400

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid username or password."}), 401

    today = date.today()
    if user.role == "student":
        if user.last_active_date == today - timedelta(days=1):
            user.streak_count += 1
        elif user.last_active_date != today:
            user.streak_count = 1
        user.last_active_date = today
        db.session.commit()

    login_user(user, remember=bool(data.get("remember", False)))
    return jsonify({"message": "Login successful.", "user": user.to_dict()}), 200


@app.route("/api/logout", methods=["POST"])
@login_required
def api_logout():
    logout_user()
    return jsonify({"message": "Logged out."}), 200


@app.route("/api/me")
@login_required
def api_me():
    return jsonify(current_user.to_dict())


@app.route("/api/users", methods=["GET"])
@login_required
def get_users():
    dept = request.args.get("dept", "").strip()
    role = request.args.get("role", "").strip()
    q    = User.query
    if dept: q = q.filter_by(department=dept)
    if role: q = q.filter_by(role=role)
    return jsonify([u.to_dict() for u in q.all()])


# ══════════════════════════════════════════════════════════════════════════════
# ANNOUNCEMENTS API  (Notice Board)
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/api/announcements", methods=["GET"])
@login_required
def get_announcements():
    dept     = request.args.get("dept", "").strip()
    category = request.args.get("category", "").strip()
    q        = Announcement.query

    if dept:
        q = q.filter(
            (Announcement.dept == dept) | (Announcement.dept == "All")
        )
    if category:
        q = q.filter_by(category=category)

    results = q.order_by(Announcement.posted_on.desc()).all()
    return jsonify([a.to_dict() for a in results])


@app.route("/api/announcements", methods=["POST"])
@login_required
def post_announcement():
    if current_user.role not in ("admin", "hod", "faculty"):
        return jsonify({"error": "Only staff can post announcements."}), 403

    data     = request.get_json(silent=True) or {}
    title    = (data.get("title") or "").strip()
    body     = (data.get("body") or "").strip()
    if not title or not body:
        return jsonify({"error": "title and body are required."}), 400

    ann = Announcement(
        id=new_id(), title=title, body=body,
        dept=(data.get("dept") or "All").strip(),
        category=(data.get("category") or "General").strip(),
        priority=(data.get("priority") or "normal").strip(),
        posted_by=current_user.full_name or current_user.username,
        posted_on=date.today(),
    )
    expires_str = data.get("expires_on")
    if expires_str:
        try:
            ann.expires_on = date.fromisoformat(expires_str)
        except ValueError:
            return jsonify({"error": "expires_on must be YYYY-MM-DD."}), 400

    db.session.add(ann)
    db.session.commit()
    return jsonify(ann.to_dict()), 201


@app.route("/api/announcements/<ann_id>", methods=["DELETE"])
@login_required
def delete_announcement(ann_id):
    if current_user.role not in ("admin", "hod"):
        return jsonify({"error": "Insufficient permissions."}), 403
    ann = Announcement.query.get_or_404(ann_id)
    db.session.delete(ann)
    db.session.commit()
    return jsonify({"message": "Deleted."}), 200


# ══════════════════════════════════════════════════════════════════════════════
# TIMETABLE API
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/api/timetable", methods=["GET"])
@login_required
def get_timetable():
    dept = request.args.get("dept", "").strip()
    year = request.args.get("year", "").strip()
    day  = request.args.get("day", "").strip()

    q = TimetableEntry.query
    if dept: q = q.filter_by(dept=dept)
    if year: q = q.filter_by(year=int(year))
    if day:  q = q.filter_by(day=day)

    DAY_ORDER = ["Mon","Tue","Wed","Thu","Fri","Sat"]
    results   = q.all()
    results.sort(key=lambda e: (DAY_ORDER.index(e.day) if e.day in DAY_ORDER else 99, e.slot))
    return jsonify([e.to_dict() for e in results])


@app.route("/api/timetable", methods=["POST"])
@login_required
def add_timetable_entry():
    if current_user.role not in ("admin", "hod"):
        return jsonify({"error": "Only admin/HoD can edit timetable."}), 403
    data = request.get_json(silent=True) or {}
    required = ["dept", "year", "day", "slot", "subject"]
    for field in required:
        if not data.get(field):
            return jsonify({"error": f"'{field}' is required."}), 400

    entry = TimetableEntry(
        id=new_id(), dept=data["dept"], year=int(data["year"]),
        day=data["day"], slot=data["slot"], subject=data["subject"],
        faculty=data.get("faculty", "TBA"), room=data.get("room", "TBA"),
    )
    db.session.add(entry)
    db.session.commit()
    return jsonify(entry.to_dict()), 201


# ══════════════════════════════════════════════════════════════════════════════
# EXAM SCHEDULE API
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/api/exams", methods=["GET"])
@login_required
def get_exams():
    dept      = request.args.get("dept", "").strip()
    year      = request.args.get("year", "").strip()
    exam_type = request.args.get("type", "").strip()

    q = ExamSchedule.query
    if dept:      q = q.filter_by(dept=dept)
    if year:      q = q.filter_by(year=int(year))
    if exam_type: q = q.filter_by(exam_type=exam_type)

    results = q.order_by(ExamSchedule.exam_date).all()
    return jsonify([e.to_dict() for e in results])


@app.route("/api/exams", methods=["POST"])
@login_required
def add_exam():
    if current_user.role not in ("admin", "hod"):
        return jsonify({"error": "Only admin/HoD can add exam schedules."}), 403
    data = request.get_json(silent=True) or {}
    required = ["dept", "year", "subject", "exam_date"]
    for field in required:
        if not data.get(field):
            return jsonify({"error": f"'{field}' is required."}), 400
    try:
        edate = date.fromisoformat(data["exam_date"])
    except ValueError:
        return jsonify({"error": "exam_date must be YYYY-MM-DD."}), 400

    exam = ExamSchedule(
        id=new_id(), dept=data["dept"], year=int(data["year"]),
        subject=data["subject"], exam_type=data.get("exam_type", "CIE"),
        exam_date=edate, start_time=data.get("start_time", "10:00"),
        hall=data.get("hall", "TBA"),
    )
    db.session.add(exam)
    db.session.commit()
    return jsonify(exam.to_dict()), 201


# ══════════════════════════════════════════════════════════════════════════════
# ONLINE EXAM API  (department-scoped, question-based)
# ══════════════════════════════════════════════════════════════════════════════
import json as _json

@app.route("/api/online-exams", methods=["GET"])
@login_required
def get_online_exams():
    """
    Students get only their dept+year active exams (or exams with year=None).
    Admin/HoD/Faculty get all, optionally filtered by ?dept= and ?year=.
    """
    if current_user.role == "student":
        dept = current_user.department
        year = current_user.year
    else:
        dept = request.args.get("dept", "").strip() or None
        year_str = request.args.get("year", "").strip()
        year = int(year_str) if year_str.isdigit() else None

    q = OnlineExam.query.filter_by(is_active=True)
    if dept:
        q = q.filter_by(dept=dept)
    if year:
        # include exams targeted at this specific year OR exams open to all years (year=None)
        q = q.filter((OnlineExam.year == year) | (OnlineExam.year == None))

    exams = q.order_by(OnlineExam.created_at.desc()).all()
    return jsonify([e.to_dict() for e in exams])


@app.route("/api/online-exams", methods=["POST"])
@login_required
def create_online_exam():
    """Create a new online exam scoped to a department and optionally a year."""
    if current_user.role not in ("admin", "hod", "faculty"):
        return jsonify({"error": "Only staff can create exams."}), 403

    data      = request.get_json(silent=True) or {}
    title     = (data.get("title") or "").strip()
    dept      = (data.get("dept")  or "").strip()
    duration  = int(data.get("duration") or 30)
    questions = data.get("questions", [])
    year_val  = data.get("year")  # None means all years
    year      = int(year_val) if year_val else None

    if not title:
        return jsonify({"error": "Exam title is required."}), 400
    if not dept:
        return jsonify({"error": "Department is required."}), 400
    if not questions:
        return jsonify({"error": "At least one question is required."}), 400

    exam = OnlineExam(
        id=new_id(),
        title=title,
        dept=dept,
        year=year,
        duration=duration,
        questions=_json.dumps(questions),
        created_by=current_user.full_name or current_user.username,
    )
    db.session.add(exam)
    db.session.commit()
    return jsonify(exam.to_dict()), 201


@app.route("/api/online-exams/<exam_id>", methods=["DELETE"])
@login_required
def delete_online_exam(exam_id):
    if current_user.role not in ("admin", "hod"):
        return jsonify({"error": "Insufficient permissions."}), 403
    exam = OnlineExam.query.get_or_404(exam_id)
    db.session.delete(exam)
    db.session.commit()
    return jsonify({"message": "Exam deleted."}), 200



# ══════════════════════════════════════════════════════════════════════════════
# ATTENDANCE API
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/api/attendance", methods=["GET"])
@login_required
def get_attendance():
    student_id = request.args.get("student_id", type=int)
    subject    = request.args.get("subject", "").strip()
    dept       = request.args.get("dept", "").strip()
    year       = request.args.get("year", type=int)

    q = Attendance.query
    if student_id: q = q.filter_by(student_id=student_id)
    if subject:    q = q.filter_by(subject=subject)
    if dept:       q = q.filter_by(dept=dept)
    if year:       q = q.filter_by(year=year)

    records = q.order_by(Attendance.date.desc()).all()

    # Calculate summary per subject
    summary = {}
    for r in records:
        if r.subject not in summary:
            summary[r.subject] = {"present": 0, "absent": 0, "od": 0, "total": 0}
        summary[r.subject][r.status] += 1
        summary[r.subject]["total"]  += 1

    for subj, s in summary.items():
        attended = s["present"] + s["od"]
        s["percentage"] = round(attended / s["total"] * 100, 1) if s["total"] else 0
        s["below_75"]   = s["percentage"] < 75

    return jsonify({"records": [r.to_dict() for r in records], "summary": summary})


@app.route("/api/attendance", methods=["POST"])
@login_required
def mark_attendance():
    if current_user.role not in ("admin", "hod", "faculty"):
        return jsonify({"error": "Only faculty can mark attendance."}), 403
    data = request.get_json(silent=True) or {}

    # Accept a list of records
    entries = data.get("entries", [])
    if not entries:
        return jsonify({"error": "Provide 'entries': [{student_id, subject, dept, year, date, status}]"}), 400

    created = []
    for e in entries:
        try:
            att_date = date.fromisoformat(e["date"])
        except (ValueError, KeyError):
            return jsonify({"error": "Each entry needs a valid 'date' (YYYY-MM-DD)."}), 400

        # Prevent duplicate
        exists = Attendance.query.filter_by(
            student_id=e["student_id"], subject=e["subject"], date=att_date
        ).first()
        if exists:
            exists.status = e.get("status", "present")
            created.append(exists.to_dict())
            continue

        att = Attendance(
            id=new_id(), student_id=e["student_id"],
            subject=e["subject"], dept=e["dept"],
            year=e["year"], date=att_date,
            status=e.get("status", "present"),
        )
        db.session.add(att)
        created.append(att.to_dict())

    db.session.commit()
    return jsonify({"marked": len(created), "records": created}), 201


# ══════════════════════════════════════════════════════════════════════════════
# LIBRARY API
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/api/library", methods=["GET"])
@login_required
def get_library():
    student_id = request.args.get("student_id", type=int)
    returned   = request.args.get("returned")   # "true" | "false"

    q = LibraryBook.query
    if student_id: q = q.filter_by(student_id=student_id)
    if returned == "false": q = q.filter_by(returned_on=None)
    if returned == "true":  q = q.filter(LibraryBook.returned_on.isnot(None))

    books = q.order_by(LibraryBook.due_date).all()
    return jsonify([b.to_dict() for b in books])


@app.route("/api/library", methods=["POST"])
@login_required
def issue_book():
    if current_user.role not in ("admin", "faculty"):
        return jsonify({"error": "Only admin/faculty can issue books."}), 403
    data = request.get_json(silent=True) or {}
    required = ["student_id", "book_title", "due_date"]
    for f in required:
        if not data.get(f):
            return jsonify({"error": f"'{f}' is required."}), 400
    try:
        due = date.fromisoformat(data["due_date"])
    except ValueError:
        return jsonify({"error": "due_date must be YYYY-MM-DD."}), 400

    book = LibraryBook(
        id=new_id(), student_id=int(data["student_id"]),
        book_title=data["book_title"],
        book_author=data.get("book_author", "Unknown"),
        issued_on=date.today(), due_date=due,
    )
    db.session.add(book)
    db.session.commit()
    return jsonify(book.to_dict()), 201


@app.route("/api/library/<book_id>/return", methods=["PATCH"])
@login_required
def return_book(book_id):
    book = LibraryBook.query.get_or_404(book_id)
    if book.returned_on:
        return jsonify({"error": "Book already returned."}), 409
    book.returned_on = date.today()
    # ₹2 fine per overdue day
    if book.returned_on > book.due_date:
        delta = (book.returned_on - book.due_date).days
        book.fine = delta * 2.0
    db.session.commit()
    return jsonify(book.to_dict())


# ══════════════════════════════════════════════════════════════════════════════
# FEE API
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/api/fees", methods=["GET"])
@login_required
def get_fees():
    student_id = request.args.get("student_id", type=int)
    paid       = request.args.get("paid")

    q = FeeRecord.query
    if student_id: q = q.filter_by(student_id=student_id)
    if paid == "true":  q = q.filter_by(paid=True)
    if paid == "false": q = q.filter_by(paid=False)

    return jsonify([f.to_dict() for f in q.order_by(FeeRecord.semester).all()])


@app.route("/api/fees/<fee_id>/pay", methods=["PATCH"])
@login_required
def pay_fee(fee_id):
    if current_user.role not in ("admin", "faculty"):
        return jsonify({"error": "Only admin/faculty can record payments."}), 403
    fee = FeeRecord.query.get_or_404(fee_id)
    if fee.paid:
        return jsonify({"error": "Fee already paid."}), 409
    fee.paid       = True
    fee.paid_on    = date.today()
    fee.receipt_no = f"REC{date.today().strftime('%Y%m%d')}{fee.id[:6].upper()}"
    db.session.commit()
    return jsonify(fee.to_dict())


# ══════════════════════════════════════════════════════════════════════════════
# WORKFLOWS, APPROVALS, DOCUMENTS, ANALYTICS (same as before)
# ══════════════════════════════════════════════════════════════════════════════
VALID_ACTIONS = {"approve", "reject"}

@app.route("/api/workflows", methods=["GET"])
@login_required
def get_workflows():
    dept = request.args.get("dept", "").strip()
    q    = Workflow.query
    if dept: q = q.filter_by(dept=dept)
    return jsonify([w.to_dict() for w in q.order_by(Workflow.monthly.desc()).all()])


@app.route("/api/workflows", methods=["POST"])
@login_required
def add_workflow():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Workflow name is required."}), 400
    try:
        monthly = int(data.get("monthly", 100))
        assert 1 <= monthly <= 10000
    except (ValueError, TypeError, AssertionError):
        return jsonify({"error": "'monthly' must be an integer 1–10000."}), 400

    dept = (data.get("dept") or "Admin").strip()
    wf   = Workflow(id=new_id(), name=name, dept=dept,
                    monthly=monthly, digitized=False,
                    score=compute_score(monthly, False))
    db.session.add(wf)
    db.session.commit()
    return jsonify(wf.to_dict()), 201


@app.route("/api/workflows/<wf_id>", methods=["PATCH"])
@login_required
def update_workflow(wf_id):
    wf   = Workflow.query.get_or_404(wf_id)
    data = request.get_json(silent=True) or {}
    if "digitized" in data: wf.digitized = bool(data["digitized"])
    if "name"      in data:
        n = (data["name"] or "").strip()
        if not n: return jsonify({"error": "Name cannot be empty."}), 400
        wf.name = n
    if "monthly" in data:
        try:
            m = int(data["monthly"])
            assert 1 <= m <= 10000
            wf.monthly = m
        except Exception:
            return jsonify({"error": "'monthly' must be 1–10000."}), 400
    wf.score = compute_score(wf.monthly, wf.digitized)
    db.session.commit()
    return jsonify(wf.to_dict())


@app.route("/api/approvals", methods=["GET"])
@login_required
def get_approvals():
    status = request.args.get("status", "").strip().lower()
    q      = Approval.query
    
    # Students see their own requests
    if current_user.role == "student":
        # Search for records linked to user_id OR records that match their name exactly (legacy)
        q = q.filter((Approval.user_id == current_user.id) | 
                     ((Approval.user_id == None) & (Approval.name == current_user.full_name)))
    
    if status: q = q.filter_by(status=status)
    return jsonify([a.to_dict() for a in
                    q.order_by(Approval.urgent.desc(), Approval.submitted.desc()).all()])


@app.route("/api/approvals", methods=["POST"])
@login_required
def submit_approval():
    # Support both JSON and multipart/form-data (for file uploads)
    if request.content_type and 'multipart/form-data' in request.content_type:
        data = request.form.to_dict()
        file = request.files.get('attachment')
    else:
        data = request.get_json(silent=True) or {}
        file = None

    submitted_by = (data.get("submitted_by") or "").strip()
    if not submitted_by:
        return jsonify({"error": "submitted_by is required."}), 400

    req_dept = (data.get("dept") or data.get("approver") or "Admin").strip()
    words    = submitted_by.split()
    initials = "".join(w[0].upper() for w in words[:2])

    # Handle file upload
    attachment_name = None
    if file and file.filename:
        safe_name = secure_filename(file.filename)
        attachment_name = f"{new_id()[:8]}_{safe_name}"
        file.save(os.path.join(UPLOAD_FOLDER, attachment_name))

    try:
        ap = Approval(
            id=new_id(),
            user_id=current_user.id,
            name=submitted_by, initials=initials,
            doc=(data.get("doc_type") or "Document").strip(),
            dept=req_dept,
            urgent=bool(data.get("urgent", False)),
            remarks=data.get("remarks", "").strip(),
            submitted=date.today(),
            attachment=attachment_name,
        )
        db.session.add(ap)

        # Gamification: Reward students for paperless actions
        if current_user.role == "student":
            current_user.add_points(10)

        db.session.commit()
        return jsonify(ap.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/api/approvals/<approval_id>", methods=["PATCH"])
@login_required
def update_approval(approval_id):
    ap     = Approval.query.get_or_404(approval_id)
    data   = request.get_json(silent=True) or {}
    action = (data.get("action") or "").strip().lower()
    if not action:
        return jsonify({"error": "'action' is required."}), 400
    if action not in VALID_ACTIONS:
        return jsonify({"error": "action must be 'approve' or 'reject'."}), 400
    if ap.status != "pending":
        return jsonify({"error": f"Already {ap.status}."}), 409
    if action == "approve":
        # Hierarchy: Fee/Budget routing. If HOD approves, forward to Admin.
        MULTI_STEP_DOCS = ["Fee Payment", "Budget Requisition", "Admission Form"]
        if ap.doc in MULTI_STEP_DOCS and current_user.role.lower() == "hod":
            # Forward to Admin
            ap.dept = "Admin"
            ap.status = "pending"
            ap.remarks = f"{ap.remarks if ap.remarks else ''}\n[Approved by HOD. Forwarded to Admin.]".strip()
        else:
            ap.status = "approved"
            ap.resolved_at = date.today()
    else:
        ap.status = "rejected"
        ap.resolved_at = date.today()
        ap.rejection_reason = (data.get("rejection_reason") or "").strip() or None

    db.session.commit()
    return jsonify(ap.to_dict())


@app.route("/api/approvals/<approval_id>/resubmit", methods=["PUT"])
@login_required
def resubmit_approval(approval_id):
    """Let a student edit and resubmit a rejected request."""
    ap = Approval.query.get_or_404(approval_id)
    if ap.user_id != current_user.id:
        return jsonify({"error": "You can only resubmit your own requests."}), 403
    if ap.status != "rejected":
        return jsonify({"error": "Only rejected requests can be resubmitted."}), 400

    if request.content_type and 'multipart/form-data' in request.content_type:
        data = request.form.to_dict()
        file = request.files.get('attachment')
    else:
        data = request.get_json(silent=True) or {}
        file = None

    # Update editable fields
    if data.get("doc_type"):  ap.doc     = data["doc_type"].strip()
    if data.get("remarks"):   ap.remarks = data["remarks"].strip()
    if data.get("dept"):      ap.dept    = data["dept"].strip()

    # Handle new file attachment
    if file and file.filename:
        if ap.attachment:
            old_path = os.path.join(UPLOAD_FOLDER, ap.attachment)
            if os.path.exists(old_path):
                os.remove(old_path)
        safe_name = secure_filename(file.filename)
        ap.attachment = f"{new_id()[:8]}_{safe_name}"
        file.save(os.path.join(UPLOAD_FOLDER, ap.attachment))

    ap.status           = "pending"
    ap.rejection_reason = None
    ap.resolved_at      = None
    ap.submitted        = date.today()
    db.session.commit()
    return jsonify(ap.to_dict()), 200


@app.route("/api/documents", methods=["GET"])
@login_required
def get_documents():
    q   = (request.args.get("q") or "").strip().lower()
    cat = (request.args.get("category") or "").strip()
    query = Document.query
    if cat: query = query.filter_by(category=cat)
    results = query.all()
    if q:
        results = [d for d in results if q in d.name.lower() or q in d.category.lower()]
    return jsonify([d.to_dict() for d in results])

@app.route("/api/uploads", methods=["POST"])
@login_required
def student_upload():
    """Students submit assignments/journals. Creates an Approval for HOD review."""
    if 'file' not in request.files:
        return jsonify({"error": "No file attached"}), 400
    file = request.files['file']
    if not file or file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    category = request.form.get("category", "Assignment")
    remarks  = request.form.get("remarks", "").strip()

    safe_name   = secure_filename(file.filename)
    unique_name = f"{new_id()[:8]}_{safe_name}"
    filepath    = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
    file.save(filepath)

    name     = current_user.full_name or current_user.username
    initials = "".join(w[0].upper() for w in name.split()[:2]) if name else "ST"
    dept     = current_user.department or "Admin"

    ap = Approval(
        id=new_id(),
        user_id=current_user.id,
        name=name,
        initials=initials,
        doc=category,
        dept=dept,
        urgent=False,
        remarks=remarks or f"Student upload: {safe_name}",
        submitted=date.today(),
        attachment=unique_name,
        status="pending"
    )
    db.session.add(ap)
    db.session.commit()
    return jsonify(ap.to_dict()), 201


@app.route("/api/uploads", methods=["GET"])
@login_required
def list_uploads():
    """HOD/Admin sees all student upload approvals; student sees their own."""
    UPLOAD_CATEGORIES = ["Assignment", "Journal", "Research Paper", "Project Report", "Other"]
    cat    = request.args.get("category", "").strip()
    status = request.args.get("status", "").strip()

    query = Approval.query.filter(Approval.doc.in_(UPLOAD_CATEGORIES))
    if current_user.role == "student":
        query = query.filter_by(user_id=current_user.id)
    elif current_user.role == "hod":
        query = query.filter_by(dept=current_user.department)

    if cat:    query = query.filter_by(doc=cat)
    if status: query = query.filter_by(status=status)

    results = query.order_by(Approval.submitted.desc()).all()
    return jsonify([r.to_dict() for r in results])


@app.route("/api/departments", methods=["GET"])
def get_departments():
    return jsonify(DEPARTMENTS)


@app.route("/uploads/files/<path:filename>", methods=["GET"])
@login_required
def serve_upload(filename):
    """Serve uploaded student files."""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route("/static/samples/<path:filename>", methods=["GET"])
@login_required
def serve_sample(filename):
    """Serve sample assignment/journal files."""
    samples_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'samples')
    return send_from_directory(samples_dir, filename, as_attachment=True)


@app.route("/api/chat/info", methods=["GET"])
@login_required
def chat_info():
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        return jsonify({"model": None})
    return jsonify({"model": "gemini-1.5-flash"})


@app.route("/api/chat", methods=["POST"])
@login_required
def chat():
    import requests
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        return jsonify({"error": "I cannot answer this yet. Please configure the GEMINI_API_KEY in the server .env file!"}), 400
        
    data = request.json
    prompt = data.get("prompt", "")
    
    sys_prompt = "You are Nexus AI, an intelligent academic system assistant for PaperZero. Keep answers brief, helpful, and friendly."
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={key}"
    payload = {
        "contents": [{"parts": [{"text": f"{sys_prompt}\n\nUser: {prompt}"}]}]
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
        resp_json = r.json()
        if "candidates" not in resp_json or not resp_json["candidates"]:
            raise Exception("API returned an unusual response.")
        text = resp_json["candidates"][0]["content"]["parts"][0]["text"]
        return jsonify({"response": text})
    except Exception as e:
        return jsonify({"error": f"API Error: {str(e)}"}), 500


@app.route("/api/analytics", methods=["GET"])
@login_required
def get_analytics():
    total_monthly    = db.session.query(func.sum(Workflow.monthly)).scalar() or 0
    digitized_count  = Workflow.query.filter_by(digitized=True).count()
    total_workflows  = Workflow.query.count()
    digitization_pct = round(digitized_count / total_workflows * 100) if total_workflows else 0
    paper_saved      = int(total_monthly * digitization_pct / 100)
    pending_count    = Approval.query.filter_by(status="pending").count()
    overdue_books    = LibraryBook.query.filter(
        LibraryBook.returned_on.is_(None),
        LibraryBook.due_date < date.today()
    ).count()
    unpaid_fees      = FeeRecord.query.filter_by(paid=False).count()

    return jsonify({
        "paper_saved":         paper_saved,
        "cost_saved":          round(paper_saved * 2.58),
        "co2_avoided":         round(paper_saved * 0.000498, 2),
        "digitized_workflows": digitized_count,
        "total_workflows":     total_workflows,
        "digitization_pct":   digitization_pct,
        "pending_approvals":   pending_count,
        "overdue_books":       overdue_books,
        "unpaid_fees":         unpaid_fees,
        "monthly_usage":       [18200, 16400, 15100, 13800, 11200, 9400],
        "monthly_labels":      ["Nov","Dec","Jan","Feb","Mar","Apr"],
        "dept_usage":          [3200, 2100, 4100, 2800, 1100, 900],
        "dept_labels":         ["CSE","AIML","ECE","EEE","Mechanical","Civil"],
        "weekly_usage":        [2100, 1800, 2400, 1900, 2100, 1400, 1100],
        "weekly_labels":       ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"],
    })


@app.route("/api/dashboard", methods=["GET"])
@login_required
def get_dashboard():
    digitized_count  = Workflow.query.filter_by(digitized=True).count()
    total_workflows  = Workflow.query.count()
    digitization_pct = round(digitized_count / total_workflows * 100) if total_workflows else 0
    total_monthly    = db.session.query(func.sum(Workflow.monthly)).scalar() or 0
    paper_saved      = int(total_monthly * digitization_pct / 100)

    return jsonify({
        "paper_saved":         paper_saved,
        "cost_saved":          round(paper_saved * 2.58),
        "co2_avoided":         round(paper_saved * 0.000498, 2),
        "digitized_workflows": digitized_count,
        "total_workflows":     total_workflows,
        "pending_approvals":   Approval.query.filter_by(status="pending").count(),
        "total_users":         User.query.count(),
        "overdue_books":       LibraryBook.query.filter(
                                   LibraryBook.returned_on.is_(None),
                                   LibraryBook.due_date < date.today()
                               ).count(),
        "upcoming_exams":      ExamSchedule.query.filter(
                                   ExamSchedule.exam_date >= date.today()
                               ).count(),
        "progress": [
            {"label": "Student Admission Forms", "pct": 100},
            {"label": "Leave Applications",      "pct": 88},
            {"label": "Fee Receipts",             "pct": 72},
            {"label": "Exam Hall Tickets",        "pct": 45},
            {"label": "Certificates / NOC",       "pct": 18},
        ],
        "activity": [
            {"event": "Leave Approved", "module": "Approvals", "by": "HoD - CSE", "time": "2 mins ago", "status": "done"},
            {"event": "New Request",    "module": "Workflows", "by": "stu001",    "time": "15 mins ago", "status": "pending"},
            {"event": "Book Issued",    "module": "Library",   "by": "Librarian", "time": "1 hour ago", "status": "done"},
            {"event": "Fee Payment",    "module": "Finance",   "by": "stu004",    "time": "3 hours ago", "status": "done"},
        ]
    })


# ══════════════════════════════════════════════════════════════════════════════
# LEADERBOARD API
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/api/leaderboard", methods=["GET"])
@login_required
def get_leaderboard():
    # Student Leaderboard
    students = User.query.filter_by(role="student").order_by(User.eco_points.desc()).all()
    
    leaderboard = []
    for idx, s in enumerate(students):
        rank = idx + 1
        badge = "🌱 Starter"
        if s.eco_points >= 1000:   badge = "🌿 Eco-Guardian"
        elif s.eco_points >= 500:  badge = "👑 Eco-King"
        elif s.eco_points >= 200:  badge = "💎 Diamond"
        elif s.eco_points >= 100:  badge = "🥇 Gold"
        elif s.eco_points >= 50:   badge = "🥈 Silver"
        
        leaderboard.append({
            "rank": rank,
            "name": s.full_name or s.username,
            "department": s.department,
            "streak": s.streak_count,
            "points": s.eco_points,
            "badge": badge
        })

    # Department Sustainability Ranking (for HOD/Admin)
    dept_ranking = []
    if current_user.role in ("admin", "hod"):
        results = db.session.query(
            User.department, 
            func.sum(User.eco_points).label("total_points"),
            func.count(User.id).label("student_count")
        ).filter(User.role == "student").group_by(User.department).order_by(func.sum(User.eco_points).desc()).all()
        
        for dept, total, count in results:
            avg = round(total / count) if count > 0 else 0
            dept_ranking.append({
                "department": dept,
                "total_points": total,
                "avg_per_student": avg
            })

    # AI Insight logic
    user_points = current_user.eco_points if hasattr(current_user, 'eco_points') else 0
    suggestion = ""
    if current_user.role == "student":
        if user_points < 50:
            suggestion = "💡 AI Insight: You are just starting out! Digitizing one application saves ~5 pages and earns 10 Eco Points. 50 points unlocks your Silver badge!"
        elif user_points < 100:
            suggestion = f"💡 AI Insight: Great progress with {user_points} points! Every digital approval avoids CO2 emissions. Just a few more for Gold!"
        else:
            suggestion = f"💡 AI Insight: Brilliant work! You are helping {current_user.department} lead the leaderboard. Keep it up for Eco-Guardian status!"
    else:
        dept_leader = dept_ranking[0]["department"] if dept_ranking else "None"
        suggestion = f"💡 Faculty Insight: {dept_leader} department is leading in sustainability points this month! Motivate your students to digitize more forms."

    return jsonify({
        "leaderboard": leaderboard,
        "dept_ranking": dept_ranking,
        "ai_suggestion": suggestion
    })

# ══════════════════════════════════════════════════════════════════════════════
# ONLINE EXAM API
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/api/exams/submit", methods=["POST"])
@login_required
def submit_exam():
    data = request.get_json(silent=True) or {}
    record = ExamResult(
        id=new_id(),
        student_name=current_user.full_name or current_user.username,
        exam_name=data.get("exam_name", "Paperless Test"),
        dept=current_user.department,
        year=current_user.year,
        score=data.get("score", 0),
        status=data.get("status", "Completed")
    )
    db.session.add(record)
    db.session.commit()
    return jsonify(record.to_dict()), 201

@app.route("/api/exams/results", methods=["GET"])
@login_required
def get_exam_results():
    dept = request.args.get("dept", "").strip()
    year = request.args.get("year", "").strip()

    q = ExamResult.query
    if dept: q = q.filter_by(dept=dept)
    if year: q = q.filter_by(year=int(year))

    results = q.order_by(ExamResult.score.desc()).all()
    
    user_locked = False
    if current_user.role == "student":
        name = current_user.full_name or current_user.username
        cheated = ExamResult.query.filter_by(student_name=name, status="Cheating Detected").first()
        user_locked = cheated is not None

    return jsonify({
        "results": [r.to_dict() for r in results],
        "is_locked": user_locked
    })

# ══════════════════════════════════════════════════════════════════════════════
# RECOMMENDATIONS API
# ══════════════════════════════════════════════════════════════════════════════
@app.route("/api/recommendations", methods=["GET"])
@login_required
def get_recommendations():
    priority = request.args.get("priority", "").lower()
    
    all_recs = [
        {"title": "Digitize Exam Hall Tickets", "desc": "Switch to digital hall tickets with QR codes to save 1,200 sheets/month.", "priority": "high", "impact": "1,200 sheets/mo"},
        {"title": "E-Signature for Leave", "desc": "Implementing digital signatures for faculty leave can reduce paper by 40%.", "priority": "high", "impact": "320 sheets/mo"},
        {"title": "Library Barcode Scanners", "desc": "Using digital slips instead of paper logs for library issues.", "priority": "med", "impact": "450 sheets/mo"},
        {"title": "Centralized Fee Receipts", "desc": "Send receipts via Email/SMS instead of printing two copies for every student.", "priority": "high", "impact": "900 sheets/mo"},
        {"title": "Digital Lab Manuals", "desc": "Replace physical manuals with iPad/Tablet kiosks in ECE/CSE labs.", "priority": "med", "impact": "600 sheets/mo"},
        {"title": "NOC Digital Portal", "desc": "Process student NOCs entirely online through the new student portal module.", "priority": "low", "impact": "180 sheets/mo"},
        {"title": "Email Admission Forms", "desc": "Move the last 20% of offline admission forms to this portal.", "priority": "med", "impact": "200 sheets/mo"},
        {"title": "Attendance QR System", "desc": "Eliminate physical registers by using student USN QR code scanning.", "priority": "high", "impact": "1,500 sheets/mo"},
    ]
    
    if priority:
        results = [r for r in all_recs if r["priority"] == priority]
    else:
        results = all_recs
        
    return jsonify(results)

# ══════════════════════════════════════════════════════════════════════════════
# RUN
# ══════════════════════════════════════════════════════════════════════════════
def migrate_db():
    """Add new columns to existing tables (SQLite does not auto-migrate)."""
    with db.engine.connect() as conn:
        result = conn.execute(db.text("PRAGMA table_info(approvals)"))
        existing = [row[1] for row in result.fetchall()]
        if 'rejection_reason' not in existing:
            conn.execute(db.text('ALTER TABLE approvals ADD COLUMN rejection_reason TEXT'))
        if 'attachment' not in existing:
            conn.execute(db.text('ALTER TABLE approvals ADD COLUMN attachment VARCHAR(300)'))
            
        doc_result = conn.execute(db.text("PRAGMA table_info(documents)"))
        doc_existing = [row[1] for row in doc_result.fetchall()]
        if 'filepath' not in doc_existing:
            conn.execute(db.text('ALTER TABLE documents ADD COLUMN filepath VARCHAR(300)'))
        conn.commit()


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        migrate_db()
        seed_data()
    debug_mode = os.getenv("FLASK_DEBUG", "true").lower() == "true"
    print("\n[*] ECO_FLOW College Edition running!")
    print("   Open   : http://127.0.0.1:5000")
    print("   Admin  : admin / Admin@1234")
    # trigger reload
    print("   HoD    : hod_cse / Hod@1234")
    print("   Student: stu001 / Student@1234\n")
    app.run(debug=debug_mode, port=5000)
    