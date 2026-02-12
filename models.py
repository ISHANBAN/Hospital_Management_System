from flask_sqlalchemy import SQLAlchemy

from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()
# MODELS

class Patient(db.Model):   # <- db.Model (capital M)
    __tablename__ = 'patients'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True, nullable=False)
    passhash = db.Column(db.String(512), nullable=False)
    name = db.Column(db.String(64), nullable=True)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)


    @property
    def password(self):
        raise AttributeError("Password is not a readable attribute")
    
    @password.setter
    def password(self, password):
        self.passhash=generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.passhash, password)

    # One patient -> many appointments
    appointments = db.relationship("Appointment", backref="patient", lazy=True)


class Doctor(db.Model):
    __tablename__ = 'doctors'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True, nullable=False)
    passhash = db.Column(db.String(512), nullable=False)
    name = db.Column(db.String(64), nullable=True)

    department_id = db.Column(
        db.Integer,
        db.ForeignKey('departments.id'),   # FK to Department
        nullable=True
    )

    # One doctor -> many appointments
    appointments = db.relationship("Appointment", backref="doctor", lazy=True)


class Department(db.Model):
    __tablename__ = 'departments'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=True)
    description = db.Column(db.String(64), nullable=True)
    doctors_registered = db.Column(db.String(64), nullable=True)

    # relationships
    doctors = db.relationship('Doctor', backref='department', lazy=True)


class Appointment(db.Model):
    __tablename__ = 'appointments'
    id = db.Column(db.Integer, primary_key=True)

    patient_id = db.Column(
        db.Integer,
        db.ForeignKey('patients.id'),
        nullable=False
    )
    doctor_id = db.Column(
        db.Integer,
        db.ForeignKey('doctors.id'),
        nullable=False
    )

    datetime = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="pending")

    # One appointment -> one treatment (optional)
    treatment = db.relationship("Treatment", backref="appointment", uselist=False)


class Treatment(db.Model):
    __tablename__ = 'treatments'
    id = db.Column(db.Integer, primary_key=True)  # primary key
    appointment_id = db.Column(
        db.Integer,
        db.ForeignKey('appointments.id'),
        nullable=False
    )
    diagnosis = db.Column(db.String(64), nullable=False)
    prescription = db.Column(db.String(64), nullable=False)
    notes = db.Column(db.String(64), nullable=False)


    