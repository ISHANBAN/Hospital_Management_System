from datetime import datetime
from functools import wraps

from flask import render_template, request, redirect, url_for, flash, session

from app import app
from models import db, Patient, Doctor, Department, Appointment, Treatment
from werkzeug.security import generate_password_hash, check_password_hash

def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if 'user_id' not in session:
                flash("Please log in first.")
                return redirect(url_for('login'))

            if role == 'admin' and not session.get('is_admin'):
                flash("Admin access only.")
                return redirect(url_for('index'))

            # you could add patient/doctor specific logic here later
            return f(*args, **kwargs)
        return wrapper
    return decorator

@app.route('/')
def index():
    if 'user_id' in session:
        if session.get('is_admin'):
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('patient_dashboard'))
    return render_template('index.html')



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    # POST: handle login
    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        flash('Username or password cannot be empty.')
        return redirect(url_for('login'))

    # Only patients for now (including admin as special patient)
    patient = Patient.query.filter_by(username=username).first()
    if not patient:
        flash("User does not exist.")
        return redirect(url_for('login'))

    if not patient.check_password(password):
        flash('Incorrect password.')
        return redirect(url_for('login'))

    # login success → store in session
    session.clear()
    session['user_id'] = patient.id
    session['is_admin'] = patient.is_admin
    session['role'] = 'admin' if patient.is_admin else 'patient'

    # redirect based on role
    if patient.is_admin:
        return redirect(url_for('admin_dashboard'))
    else:
        return redirect(url_for('patient_dashboard'))
    
@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out.")
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')

    username = request.form.get('username')
    password = request.form.get('password')
    name = request.form.get('name')

    if not username or not password:
        flash('Username or password cannot be empty.')
        return redirect(url_for('register'))

    if Patient.query.filter_by(username=username).first():
        flash("Patient with this username already exists.")
        return redirect(url_for('register'))

    patient = Patient(username=username, name=name)
    patient.password = password   # uses setter to hash

    db.session.add(patient)
    db.session.commit()
    flash('User successfully registered! Please login.')
    return redirect(url_for('login'))

@app.route('/admin')
@login_required(role='admin')
def admin_dashboard():
    total_patients = Patient.query.count()
    total_doctors = Doctor.query.count()
    total_appointments = Appointment.query.count()
    return render_template(
        'admin_dashboard.html',
        total_patients=total_patients,
        total_doctors=total_doctors,
        total_appointments=total_appointments
    )

@app.route('/admin/doctors')
@login_required(role='admin')
def admin_doctors():
    doctors = Doctor.query.all()
    departments = Department.query.all()
    return render_template('admin_doctors.html', doctors=doctors, departments=departments)

@app.route('/admin/doctors/new', methods=['GET', 'POST'])
@login_required(role='admin')
def admin_doctors_new():
    departments = Department.query.all()

    if request.method == 'GET':
        return render_template('admin_doctors_new.html', departments=departments)

    username = request.form.get('username')
    password = request.form.get('password')
    name = request.form.get('name')
    department_id = request.form.get('department_id')

    if not username or not password:
        flash("Username and password required.")
        return redirect(url_for('admin_doctors_new'))

    if Doctor.query.filter_by(username=username).first():
        flash("Doctor with this username already exists.")
        return redirect(url_for('admin_doctors_new'))

    doc = Doctor(
        username=username,
        passhash=generate_password_hash(password),
        name=name,
        department_id=department_id or None
    )
    db.session.add(doc)
    db.session.commit()
    flash("Doctor created successfully.")
    return redirect(url_for('admin_doctors'))

@app.route('/patient')
@login_required()
def patient_dashboard():
    patient_id = session['user_id']
    patient = Patient.query.get(patient_id)
    upcoming = Appointment.query.filter_by(patient_id=patient_id).order_by(Appointment.datetime).all()
    return render_template('patient_dashboard.html', patient=patient, appointments=upcoming)

@app.route('/patient/appointments/new', methods=['GET', 'POST'])
@login_required()
def patient_appointments_new():
    patient_id = session['user_id']
    doctors = Doctor.query.all()

    if request.method == 'GET':
        return render_template('patient_appointments_new.html', doctors=doctors)

    doctor_id = request.form.get('doctor_id')
    date_str = request.form.get('date')    # e.g. "2025-11-30"
    time_str = request.form.get('time')    # e.g. "14:30"

    if not doctor_id or not date_str or not time_str:
        flash("Doctor, date and time are required.")
        return redirect(url_for('patient_appointments_new'))

    try:
        dt = datetime.fromisoformat(f"{date_str}T{time_str}")
    except ValueError:
        flash("Invalid date/time format.")
        return redirect(url_for('patient_appointments_new'))

    appt = Appointment(
        patient_id=patient_id,
        doctor_id=doctor_id,
        datetime=dt,
        status="pending"
    )
    db.session.add(appt)
    db.session.commit()
    flash("Appointment booked!")
    return redirect(url_for('patient_dashboard'))

# --- doctor auth --- #

@app.route('/doctor/login', methods=['GET', 'POST'])
def doctor_login():
    if request.method == 'GET':
        return render_template('doctor_login.html')

    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        flash("Username and password are required.")
        return redirect(url_for('doctor_login'))

    doctor = Doctor.query.filter_by(username=username).first()
    if not doctor:
        flash("Doctor does not exist.")
        return redirect(url_for('doctor_login'))

    if not check_password_hash(doctor.passhash, password):
        flash("Incorrect password.")
        return redirect(url_for('doctor_login'))

    # login success → store doctor in session
    session.clear()
    session['doctor_id'] = doctor.id
    session['role'] = 'doctor'

    return redirect(url_for('doctor_dashboard'))
 
@app.route('/doctor')
def doctor_dashboard():
    if session.get('role') != 'doctor':
        flash("Doctor access only. Please login as doctor.")
        return redirect(url_for('doctor_login'))

    doctor_id = session['doctor_id']
    doctor = Doctor.query.get(doctor_id)

    # all appointments assigned to this doctor
    appointments = Appointment.query.filter_by(doctor_id=doctor_id).order_by(Appointment.datetime).all()

    return render_template('doctor_dashboard.html', doctor=doctor, appointments=appointments)

@app.route('/doctor/appointments/<int:appointment_id>', methods=['GET', 'POST'])
def doctor_appointment_detail(appointment_id):
    # Only allow logged-in doctors
    if session.get('role') != 'doctor':
        flash("Doctor access only. Please login as doctor.")
        return redirect(url_for('doctor_login'))

    doctor_id = session.get('doctor_id')
    appt = Appointment.query.get_or_404(appointment_id)

    # Ensure this appointment actually belongs to the logged-in doctor
    if appt.doctor_id != doctor_id:
        flash("You are not assigned to this appointment.")
        return redirect(url_for('doctor_dashboard'))

    if request.method == 'GET':
        # Show appointment details + existing treatment (if any)
        return render_template('doctor_appointment_detail.html', appointment=appt)

    # POST: save treatment data
    diagnosis = request.form.get('diagnosis')
    prescription = request.form.get('prescription')
    notes = request.form.get('notes')

    if not diagnosis or not prescription:
        flash("Diagnosis and prescription are required.")
        return redirect(url_for('doctor_appointment_detail', appointment_id=appointment_id))

    if appt.treatment is None:
        # Create new treatment record
        treatment = Treatment(
            appointment_id=appt.id,
            diagnosis=diagnosis,
            prescription=prescription,
            notes=notes
        )
        db.session.add(treatment)
    else:
        # Update existing treatment
        appt.treatment.diagnosis = diagnosis
        appt.treatment.prescription = prescription
        appt.treatment.notes = notes

    # Optional: mark appointment as completed
    appt.status = "completed"

    db.session.commit()
    flash("Treatment saved.")
    return redirect(url_for('doctor_dashboard'))
