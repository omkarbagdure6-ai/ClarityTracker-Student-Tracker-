# app.py — Main Flask application

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, Student, Attendance, Fee
from datetime import date

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tracker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'student_tracker_secret_2024'

db.init_app(app)

with app.app_context():
    db.create_all()


# ── DASHBOARD ────────────────────────────────────────

@app.route('/')
def index():
    total_students = Student.query.count()
    fee_pending    = Fee.query.filter_by(status='Pending').count()
    present_today  = Attendance.query.filter_by(
                        date=date.today(), status='Present').count()
    students       = Student.query.order_by(Student.id.desc()).limit(5).all()

    return render_template('index.html',
                           total_students=total_students,
                           present_today=present_today,
                           fee_pending=fee_pending,
                           students=students)


# ── STUDENTS ─────────────────────────────────────────

@app.route('/students')
def students():
    search  = request.args.get('search', '')
    if search:
        all_students = Student.query.filter(
            Student.name.ilike(f'%{search}%')).all()
    else:
        all_students = Student.query.order_by(Student.id.desc()).all()

    return render_template('students.html',
                           students=all_students,
                           search=search)


@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        name       = request.form.get('name', '').strip()
        class_name = request.form.get('class_name', '').strip()
        phone      = request.form.get('phone', '').strip()
        email      = request.form.get('email', '').strip()

        # Basic validation
        if not name or not class_name:
            flash('Name and Class are required.', 'danger')
            return redirect(url_for('add_student'))

        student = Student(name=name, class_name=class_name,
                          phone=phone, email=email)
        db.session.add(student)
        db.session.commit()
        flash(f'Student "{name}" added successfully!', 'success')
        return redirect(url_for('students'))

    return render_template('add_student.html')


@app.route('/delete_student/<int:student_id>')
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    db.session.delete(student)
    db.session.commit()
    flash(f'Student "{student.name}" deleted.', 'success')
    return redirect(url_for('students'))


# ── ATTENDANCE ───────────────────────────────────────

@app.route('/attendance', methods=['GET', 'POST'])
def attendance():
    students     = Student.query.order_by(Student.name).all()
    today        = date.today()
    # Get today's attendance records as a dict {student_id: status}
    records      = Attendance.query.filter_by(date=today).all()
    marked       = {r.student_id: r.status for r in records}

    if request.method == 'POST':
        for student in students:
            status = request.form.get(f'status_{student.id}', 'Absent')
            existing = Attendance.query.filter_by(
                student_id=student.id, date=today).first()
            if existing:
                existing.status = status
            else:
                record = Attendance(student_id=student.id,
                                    date=today, status=status)
                db.session.add(record)
        db.session.commit()
        flash('Attendance saved successfully!', 'success')
        return redirect(url_for('attendance'))

    return render_template('attendance.html',
                           students=students,
                           marked=marked,
                           today=today)


# ── FEES ─────────────────────────────────────────────

@app.route('/fees')
def fees():
    students = Student.query.order_by(Student.name).all()
    # Get all fee records as a dict {student_id: [fee, fee, ...]}
    all_fees = {}
    for s in students:
        all_fees[s.id] = Fee.query.filter_by(student_id=s.id).all()

    return render_template('fees.html',
                           students=students,
                           all_fees=all_fees)


@app.route('/add_fee/<int:student_id>', methods=['GET', 'POST'])
def add_fee(student_id):
    student = Student.query.get_or_404(student_id)

    if request.method == 'POST':
        month  = request.form.get('month', '').strip()
        amount = request.form.get('amount', 0)
        status = request.form.get('status', 'Pending')

        if not month:
            flash('Month is required.', 'danger')
            return redirect(url_for('add_fee', student_id=student_id))

        fee = Fee(student_id=student_id, month=month,
                  amount=float(amount), status=status)
        db.session.add(fee)
        db.session.commit()
        flash(f'Fee record added for {student.name}!', 'success')
        return redirect(url_for('fees'))

    return render_template('add_fee.html', student=student)


@app.route('/update_fee/<int:fee_id>/<status>')
def update_fee(fee_id, status):
    fee = Fee.query.get_or_404(fee_id)
    fee.status = status
    db.session.commit()
    flash('Fee status updated!', 'success')
    return redirect(url_for('fees'))


@app.route('/delete_fee/<int:fee_id>')
def delete_fee(fee_id):
    fee = Fee.query.get_or_404(fee_id)
    db.session.delete(fee)
    db.session.commit()
    flash('Fee record deleted.', 'success')
    return redirect(url_for('fees'))


# ── RUN ──────────────────────────────────────────────

if __name__ == '__main__':
    app.run(debug=True)