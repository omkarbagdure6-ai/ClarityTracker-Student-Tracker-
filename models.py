

# models.py — Database models with User authentication

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import date

db = SQLAlchemy()


class User(db.Model, UserMixin):
    """
    Represents a logged-in user (teacher/admin).
    Each user owns their own students.
    """
    __tablename__ = 'users'

    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(100), nullable=False)
    email      = db.Column(db.String(120), unique=True, nullable=False)
    password   = db.Column(db.String(200), nullable=False)
    role       = db.Column(db.String(10), default='user')  # 'admin' or 'user'
    created_at = db.Column(db.Date, default=date.today)

    # One user owns many students
    students = db.relationship('Student', backref='owner', lazy=True,
                               cascade='all, delete-orphan')

    def __repr__(self):
        return f'<User {self.email}>'


class Student(db.Model):
    """
    Represents a student owned by a specific user.
    """
    __tablename__ = 'students'

    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(100), nullable=False)
    class_name  = db.Column(db.String(50),  nullable=False)
    phone       = db.Column(db.String(15),  nullable=True)
    email       = db.Column(db.String(120), nullable=True)
    joined_date = db.Column(db.Date, default=date.today)

    # Foreign key — links student to the user who created them
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    attendances = db.relationship('Attendance', backref='student', lazy=True,
                                  cascade='all, delete-orphan')
    fees        = db.relationship('Fee', backref='student', lazy=True,
                                  cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Student {self.name}>'


class Attendance(db.Model):
    """
    One attendance record for one student on one date.
    """
    __tablename__ = 'attendance'

    id         = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    date       = db.Column(db.Date, default=date.today, nullable=False)
    status     = db.Column(db.String(10), default='Absent')

    def __repr__(self):
        return f'<Attendance {self.student_id} {self.date} {self.status}>'


class Fee(db.Model):
    """
    One month fee record for one student.
    """
    __tablename__ = 'fees'

    id         = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    month      = db.Column(db.String(20), nullable=False)
    amount     = db.Column(db.Float, default=0.0)
    status     = db.Column(db.String(10), default='Pending')

    def __repr__(self):
        return f'<Fee {self.student_id} {self.month} {self.status}>'