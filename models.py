

from flask_sqlalchemy import SQLAlchemy
from datetime import date


db = SQLAlchemy()


class Student(db.Model):
    """
    Represents a student in the system.
    Each row = one student.
    """
    __tablename__ = 'students'

    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(100), nullable=False)
    class_name  = db.Column(db.String(50),  nullable=False)
    phone       = db.Column(db.String(15),  nullable=True)
    email       = db.Column(db.String(120), nullable=True)
    joined_date = db.Column(db.Date, default=date.today)

    # One student can have many attendance records and fee records
    attendances = db.relationship('Attendance', backref='student', lazy=True, cascade='all, delete-orphan')
    fees        = db.relationship('Fee',        backref='student', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Student {self.name}>'


class Attendance(db.Model):
    """
    Represents one attendance record for one student on one date.
    """
    __tablename__ = 'attendance'

    id         = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    date       = db.Column(db.Date, default=date.today, nullable=False)
    status     = db.Column(db.String(10), default='Absent')  # 'Present' or 'Absent'

    def __repr__(self):
        return f'<Attendance {self.student_id} {self.date} {self.status}>'


class Fee(db.Model):
    """
    Represents one month's fee record for one student.
    """
    __tablename__ = 'fees'

    id         = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    month      = db.Column(db.String(20), nullable=False)   # e.g. 'June 2025'
    amount     = db.Column(db.Float, default=0.0)
    status     = db.Column(db.String(10), default='Pending') # 'Paid' or 'Pending'

    def __repr__(self):
        return f'<Fee {self.student_id} {self.month} {self.status}>'