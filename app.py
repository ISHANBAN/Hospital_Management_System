# app.py
from flask import Flask, render_template, request, redirect, url_for, flash

from config import Config
from models import db, Patient, Doctor, Department, Appointment, Treatment

# Create Flask app instance
app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

# create tables + seed admin once
with app.app_context():
    db.create_all()

    admin = Patient.query.filter_by(username='admin').first()
    if not admin:
        admin = Patient(username='admin', name='Admin', is_admin=True)
        admin.password = 'admin'   # uses @password.setter
        db.session.add(admin)
        db.session.commit()



import routes 

if __name__ == "__main__":
    app.run(debug=True)
