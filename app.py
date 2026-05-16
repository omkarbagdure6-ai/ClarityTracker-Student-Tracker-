# app.py — Full Flask app with login, registration, and admin

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, \
                        login_required, current_user
from flask_bcrypt import Bcrypt
from models import db, User, Student, Attendance, Fee
from datetime import date
from functools import wraps

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tracker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'clarity_tracker_secret_2024'

# Initialize extensions
db.init_app(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'danger'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ── Admin-only decorator ─────────────────────────────
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated


# Create tables and default admin
with app.app_context():
    db.create_all()
    # Create default admin if none exists
    if not User.query.filter_by(role='admin').first():
        hashed = bcrypt.generate_password_hash('omie2006').decode('utf-8')
        admin = User(name='Admin', email='omkarbagdure05@gmail.com',
                     password=hashed, role='admin')
        db.session.add(admin)
        db.session.commit()


# ── AUTH ROUTES ──────────────────────────────────────

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        name     = request.form.get('name', '').strip()
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm', '')

        if not name or not email or not password:
            flash('All fields are required.', 'danger')
            return redirect(url_for('register'))

        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('register'))

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered. Please log in.', 'danger')
            return redirect(url_for('register'))

        hashed = bcrypt.generate_password_hash(password).decode('utf-8')
        user   = User(name=name, email=email, password=hashed)
        db.session.add(user)
        db.session.commit()
        flash('Account created! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash(f'Welcome back, {user.name}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))

        flash('Invalid email or password.', 'danger')
        return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))


# ── DASHBOARD ────────────────────────────────────────

@app.route('/')
@login_required
def index():
    # Each user only sees their own students
    my_students    = Student.query.filter_by(user_id=current_user.id)
    total_students = my_students.count()
    student_ids    = [s.id for s in my_students.all()]

    fee_pending  = Fee.query.filter(
                    Fee.student_id.in_(student_ids),
                    Fee.status == 'Pending').count()
    present_today = Attendance.query.filter(
                    Attendance.student_id.in_(student_ids),
                    Attendance.date == date.today(),
                    Attendance.status == 'Present').count()

    recent = Student.query.filter_by(
                user_id=current_user.id).order_by(
                Student.id.desc()).limit(5).all()

    return render_template("index.html", 
                           total_students=total_students,
                           present_today=present_today,
                           fee_pending=fee_pending,
                           students=recent)


# ── STUDENTS ─────────────────────────────────────────

@app.route('/students')
@login_required
def students():
    search = request.args.get('search', '')
    query  = Student.query.filter_by(user_id=current_user.id)
    if search:
        query = query.filter(Student.name.ilike(f'%{search}%'))
    all_students = query.order_by(Student.id.desc()).all()
    return render_template('students.html',
                           students=all_students, search=search)


@app.route('/add_student', methods=['GET', 'POST'])
@login_required
def add_student():
    if request.method == 'POST':
        name       = request.form.get('name', '').strip()
        class_name = request.form.get('class_name', '').strip()
        phone      = request.form.get('phone', '').strip()
        email      = request.form.get('email', '').strip()

        if not name or not class_name:
            flash('Name and Class are required.', 'danger')
            return redirect(url_for('add_student'))

        student = Student(name=name, class_name=class_name,
                          phone=phone, email=email,
                          user_id=current_user.id)
        db.session.add(student)
        db.session.commit()
        flash(f'Student "{name}" added!', 'success')
        return redirect(url_for('students'))

    return render_template('add_student.html')


@app.route('/delete_student/<int:student_id>')
@login_required
def delete_student(student_id):
    student = Student.query.filter_by(
                id=student_id, user_id=current_user.id).first_or_404()
    db.session.delete(student)
    db.session.commit()
    flash(f'Student "{student.name}" deleted.', 'success')
    return redirect(url_for('students'))


# ── ATTENDANCE ───────────────────────────────────────

@app.route('/attendance', methods=['GET', 'POST'])
@login_required
def attendance():
    students = Student.query.filter_by(
                user_id=current_user.id).order_by(Student.name).all()
    today    = date.today()
    records  = Attendance.query.filter_by(date=today).all()
    marked   = {r.student_id: r.status for r in records}

    if request.method == 'POST':
        for student in students:
            status   = request.form.get(f'status_{student.id}', 'Absent')
            existing = Attendance.query.filter_by(
                        student_id=student.id, date=today).first()
            if existing:
                existing.status = status
            else:
                db.session.add(Attendance(student_id=student.id,
                                          date=today, status=status))
        db.session.commit()
        flash('Attendance saved!', 'success')
        return redirect(url_for('attendance'))

    return render_template('attendance.html',
                           students=students, marked=marked, today=today)


# ── FEES ─────────────────────────────────────────────

@app.route('/fees')
@login_required
def fees():
    students = Student.query.filter_by(
                user_id=current_user.id).order_by(Student.name).all()
    all_fees = {s.id: Fee.query.filter_by(student_id=s.id).all()
                for s in students}
    return render_template('fees.html',
                           students=students, all_fees=all_fees)


@app.route('/add_fee/<int:student_id>', methods=['GET', 'POST'])
@login_required
def add_fee(student_id):
    student = Student.query.filter_by(
                id=student_id, user_id=current_user.id).first_or_404()

    if request.method == 'POST':
        month  = request.form.get('month', '').strip()
        amount = request.form.get('amount', 0)
        status = request.form.get('status', 'Pending')

        if not month:
            flash('Month is required.', 'danger')
            return redirect(url_for('add_fee', student_id=student_id))

        db.session.add(Fee(student_id=student_id, month=month,
                           amount=float(amount), status=status))
        db.session.commit()
        flash(f'Fee added for {student.name}!', 'success')
        return redirect(url_for('fees'))

    return render_template('add_fee.html', student=student)


@app.route('/update_fee/<int:fee_id>/<status>')
@login_required
def update_fee(fee_id, status):
    fee = Fee.query.get_or_404(fee_id)
    fee.status = status
    db.session.commit()
    flash('Fee status updated!', 'success')
    return redirect(url_for('fees'))


@app.route('/delete_fee/<int:fee_id>')
@login_required
def delete_fee(fee_id):
    fee = Fee.query.get_or_404(fee_id)
    db.session.delete(fee)
    db.session.commit()
    flash('Fee record deleted.', 'success')
    return redirect(url_for('fees'))


# ── ADMIN PANEL ──────────────────────────────────────

@app.route('/admin')
@login_required
@admin_required
def admin():
    all_users    = User.query.order_by(User.created_at.desc()).all()
    total_users  = User.query.count()
    total_students = Student.query.count()
    total_fees   = Fee.query.count()
    pending_fees = Fee.query.filter_by(status='Pending').count()

    return render_template('admin.html',
                           all_users=all_users,
                           total_users=total_users,
                           total_students=total_students,
                           total_fees=total_fees,
                           pending_fees=pending_fees)


@app.route('/admin/delete_user/<int:user_id>')
@login_required
@admin_required
def delete_user(user_id):
    if user_id == current_user.id:
        flash('You cannot delete yourself.', 'danger')
        return redirect(url_for('admin'))
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash(f'User {user.email} deleted.', 'success')
    return redirect(url_for('admin'))


@app.route('/admin/make_admin/<int:user_id>')
@login_required
@admin_required
def make_admin(user_id):
    user = User.query.get_or_404(user_id)
    user.role = 'admin'
    db.session.commit()
    flash(f'{user.name} is now an admin.', 'success')
    return redirect(url_for('admin'))


# ── RUN ──────────────────────────────────────────────

if __name__ == '__main__':
    app.run(debug=True)