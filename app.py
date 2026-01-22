import os
from dotenv import load_dotenv  # Add this import at the top

load_dotenv()  # Load environment variables

from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for, flash
import json
import datetime
import secrets
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
import base64
import hashlib
import re

app = Flask(__name__)
# Use environment variable for secret key in production
app.secret_key = os.environ.get('SECRET_KEY', 'healthcare-secret-key-2024')

# ==================== IN-MEMORY DATA STORAGE ====================
users = []
patients = []
appointments = []
medical_records = []
consent_records = []
prescriptions = []

# ==================== PASSWORD VALIDATION ====================
def validate_password(password):
    """
    Validate password strength:
    - At least 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character (!@#$%^&*(),.?\":{}|<>)"
    
    return True, "Password is valid"

# ==================== INITIAL DATA SETUP ====================
def initialize_data():
    """Initialize in-memory data storage with sample users and data"""
    global users, patients, appointments, medical_records, consent_records, prescriptions
    
    # Clear any existing data
    users.clear()
    patients.clear()
    appointments.clear()
    medical_records.clear()
    consent_records.clear()
    prescriptions.clear()
    
    # Create user IDs counter
    user_id_counter = 1
    patient_id_counter = 1
    appointment_id_counter = 1
    
    # ==================== ADMIN ACCOUNTS (2 hardcoded) ====================
    admins = [
        {
            'id': user_id_counter, 
            'username': 'admin',
            'email': 'admin@healthcenter.org',
            'password': 'Admin123!',
            'role': 'admin',
            'first_name': 'System',
            'last_name': 'Administrator',
            'phone': '26650000001',
            'is_active': True,
            'created_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        },
        {
            'id': user_id_counter + 1,
            'username': 'sysadmin',
            'email': 'sysadmin@healthcenter.org',
            'password': 'Admin456!',
            'role': 'admin',
            'first_name': 'Data',
            'last_name': 'Manager',
            'phone': '26650000002',
            'is_active': True,
            'created_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    ]
    
    for admin in admins:
        users.append(admin)
    user_id_counter += 2
    
    # ==================== DOCTORS (3 hardcoded) ====================
    doctors = [
        {
            'id': user_id_counter,
            'username': 'dr_thabo',
            'email': 'thabo.mokoena@healthcenter.org',
            'password': 'Doctor123!',
            'role': 'doctor',
            'first_name': 'Thabo',
            'last_name': 'Mokoena',
            'phone': '26650123456',
            'specialization': 'General Medicine',
            'is_active': True,
            'created_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        },
        {
            'id': user_id_counter + 1,
            'username': 'dr_masechaba',
            'email': 'masechaba.moloi@healthcenter.org',
            'password': 'Doctor456!',
            'role': 'doctor',
            'first_name': 'Masechaba',
            'last_name': 'Moloi',
            'phone': '26650234567',
            'specialization': 'Pediatrics',
            'is_active': True,
            'created_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        },
        {
            'id': user_id_counter + 2,
            'username': 'dr_sefako',
            'email': 'sefako.mohale@healthcenter.org',
            'password': 'Doctor789!',
            'role': 'doctor',
            'first_name': 'Sefako',
            'last_name': 'Mohale',
            'phone': '26650345678',
            'specialization': 'Cardiology',
            'is_active': True,
            'created_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    ]
    
    for doctor in doctors:
        users.append(doctor)
    user_id_counter += 3
    
    # ==================== NURSES (2 hardcoded) ====================
    nurses = [
        {
            'id': user_id_counter,
            'username': 'nurse_mpho',
            'email': 'mpho.letsie@healthcenter.org',
            'password': 'Nurse123!',
            'role': 'nurse',
            'first_name': 'Mpho',
            'last_name': 'Letsie',
            'phone': '26650456789',
            'is_active': True,
            'created_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        },
        {
            'id': user_id_counter + 1,
            'username': 'nurse_lineo',
            'email': 'lineo.mokhothu@healthcenter.org',
            'password': 'Nurse456!',
            'role': 'nurse',
            'first_name': 'Lineo',
            'last_name': 'Mokhothu',
            'phone': '26650567890',
            'is_active': True,
            'created_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    ]
    
    for nurse in nurses:
        users.append(nurse)
    user_id_counter += 2
    
    # ==================== PATIENTS (3 hardcoded) ====================
    patients_data = [
        {
            'username': 'patient_tlali',
            'email': 'tlali.mokone@gmail.com',
            'password': 'Patient123!',
            'first_name': 'Tlali',
            'last_name': 'Mokone',
            'phone': '26650678901',
            'date_of_birth': '1985-06-15',
            'gender': 'male',
            'blood_type': 'O+',
            'allergies': 'Penicillin, Peanuts',
            'emergency_contact': '26650123456',
            'address': '123 Maseru Street, Maseru',
            'medical_history': 'Hypertension, Asthma'
        },
        {
            'username': 'patient_lerato',
            'email': 'lerato.khutlang@yahoo.com',
            'password': 'Patient456!',
            'first_name': 'Lerato',
            'last_name': 'Khutlang',
            'phone': '26650789012',
            'date_of_birth': '1992-11-03',
            'gender': 'female',
            'blood_type': 'A-',
            'allergies': 'None',
            'emergency_contact': '26650234567',
            'address': '456 Roma Road, Roma',
            'medical_history': 'Diabetes type 2'
        },
        {
            'username': 'patient_thabiso',
            'email': 'thabiso.matsoso@outlook.com',
            'password': 'Patient789!',
            'first_name': 'Thabiso',
            'last_name': 'Matsoso',
            'phone': '26650890123',
            'date_of_birth': '1978-03-22',
            'gender': 'male',
            'blood_type': 'B+',
            'allergies': 'Sulfa drugs, Shellfish',
            'emergency_contact': '26650345678',
            'address': '789 Teyateyaneng Street, TY',
            'medical_history': 'High cholesterol, Previous knee surgery (2019)'
        }
    ]
    
    for patient_data in patients_data:
        # Create user
        user = {
            'id': user_id_counter,
            'username': patient_data['username'],
            'email': patient_data['email'],
            'password': patient_data['password'],
            'role': 'patient',
            'first_name': patient_data['first_name'],
            'last_name': patient_data['last_name'],
            'phone': patient_data['phone'],
            'is_active': True,
            'created_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        users.append(user)
        
        # Create patient record
        patient = {
            'id': patient_id_counter,
            'user_id': user_id_counter,
            'date_of_birth': patient_data['date_of_birth'],
            'gender': patient_data['gender'],
            'blood_type': patient_data['blood_type'],
            'allergies': patient_data['allergies'],
            'emergency_contact': patient_data['emergency_contact'],
            'address': patient_data['address'],
            'medical_history': patient_data['medical_history']
        }
        patients.append(patient)
        
        user_id_counter += 1
        patient_id_counter += 1
    
    # ==================== SAMPLE APPOINTMENTS ====================
    sample_appointments = [
        {
            'patient_id': 1,
            'doctor_id': 3,  # Dr. Thabo
            'appointment_date': (datetime.datetime.now() + datetime.timedelta(days=2)).strftime('%Y-%m-%d 10:00:00'),
            'status': 'scheduled',
            'reason': 'Regular checkup',
            'notes': 'Blood pressure monitoring needed'
        },
        {
            'patient_id': 2,
            'doctor_id': 4,  # Dr. Masechaba
            'appointment_date': (datetime.datetime.now() + datetime.timedelta(days=1)).strftime('%Y-%m-%d 14:30:00'),
            'status': 'approved',
            'reason': 'Pediatric consultation',
            'notes': 'Child vaccination follow-up'
        },
        {
            'patient_id': 3,
            'doctor_id': 5,  # Dr. Sefako
            'appointment_date': (datetime.datetime.now() + datetime.timedelta(days=3)).strftime('%Y-%m-%d 09:15:00'),
            'status': 'completed',
            'reason': 'Cardiac evaluation',
            'notes': 'ECG results review'
        }
    ]
    
    for appt in sample_appointments:
        appointment = {
            'id': appointment_id_counter,
            'patient_id': appt['patient_id'],
            'doctor_id': appt['doctor_id'],
            'appointment_date': appt['appointment_date'],
            'status': appt['status'],
            'reason': appt['reason'],
            'notes': appt['notes'],
            'created_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        appointments.append(appointment)
        appointment_id_counter += 1
    
    # ==================== SAMPLE MEDICAL RECORDS ====================
    sample_records = [
        {
            'patient_user_id': 7,  # Tlali
            'doctor_id': 3,
            'record_data': {
                'record_type': 'consultation',
                'title': 'Initial Consultation',
                'description': 'Patient presented with high blood pressure and shortness of breath.',
                'diagnosis': 'Hypertension Stage 2',
                'symptoms': 'Headache, dizziness, fatigue'
            }
        },
        {
            'patient_user_id': 8,  # Lerato
            'doctor_id': 4,
            'record_data': {
                'record_type': 'prescription',
                'title': 'Diabetes Management',
                'description': 'Prescribed medication for diabetes management.',
                'diagnosis': 'Type 2 Diabetes',
                'symptoms': 'Increased thirst, frequent urination',
                'medication_name': 'Metformin',
                'dosage': '500mg',
                'frequency': 'Twice daily',
                'duration': '30 days',
                'instructions': 'Take with meals'
            }
        }
    ]
    
    for record in sample_records:
        add_medical_record(
            record['patient_user_id'],
            record['doctor_id'],
            record['record_data']
        )
    
    # ==================== SAMPLE CONSENTS ====================
    sample_consents = [
        {
            'patient_user_id': 7,
            'consent_data': {
                'consent_type': 'data_processing',
                'consent_given': True,
                'purpose': 'Medical treatment and record keeping',
                'expiration_date': '2025-12-31',
                'recorded_by': 1  # admin
            }
        },
        {
            'patient_user_id': 8,
            'consent_data': {
                'consent_type': 'treatment',
                'consent_given': True,
                'purpose': 'Diabetes treatment and medication',
                'expiration_date': None,
                'recorded_by': 1
            }
        }
    ]
    
    for consent in sample_consents:
        add_consent_record(
            consent['patient_user_id'],
            consent['consent_data']
        )
    
    print(f"✅ Data initialized successfully!")
    print(f"   👥 Users: {len(users)} total")
    print(f"   👑 Admins: {len([u for u in users if u['role'] == 'admin'])}")
    print(f"   👨‍⚕️  Doctors: {len([u for u in users if u['role'] == 'doctor'])}")
    print(f"   👩‍⚕️  Nurses: {len([u for u in users if u['role'] == 'nurse'])}")
    print(f"   👤 Patients: {len([u for u in users if u['role'] == 'patient'])}")
    print(f"   📅 Appointments: {len(appointments)}")
    print(f"   📋 Medical Records: {len(medical_records)}")
    print(f"   ✅ Consent Records: {len(consent_records)}")
    
    return True

# ==================== USER REGISTRATION ====================
def register_user(username, email, password, role, first_name, last_name, phone):
    """Register a new user"""
    
    # Check if username already exists
    for user in users:
        if user['username'] == username:
            return False, "Username already exists"
    
    # Check if email already exists
    for user in users:
        if user['email'] == email:
            return False, "Email already registered"
    
    # Validate password
    is_valid, message = validate_password(password)
    if not is_valid:
        return False, message
    
    # Create new user ID
    user_id = len(users) + 1
    
    # Create new user
    new_user = {
        'id': user_id,
        'username': username,
        'email': email,
        'password': password,
        'role': role,
        'first_name': first_name,
        'last_name': last_name,
        'phone': phone,
        'is_active': True,
        'created_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # Add user-specific fields based on role
    if role == 'doctor':
        new_user['specialization'] = request.form.get('specialization', 'General Medicine')
    elif role == 'patient':
        # Create patient record
        patient_id = len(patients) + 1
        patients.append({
            'id': patient_id,
            'user_id': user_id,
            'date_of_birth': request.form.get('date_of_birth', '1990-01-01'),
            'gender': request.form.get('gender', 'male'),
            'blood_type': request.form.get('blood_type', 'Unknown'),
            'allergies': request.form.get('allergies', 'None'),
            'emergency_contact': request.form.get('emergency_contact', ''),
            'address': request.form.get('address', ''),
            'medical_history': request.form.get('medical_history', '')
        })
    
    users.append(new_user)
    
    return True, "Registration successful"

# ==================== PASSWORD AUTHENTICATION ====================
def check_user_password(username, password):
    """Check user password against stored password"""
    user = find_user_by_username(username)
    if user and user['password'] == password:
        return True
    return False

# ==================== DATA HELPER FUNCTIONS ====================
def find_user_by_username(username):
    """Find user by username"""
    for user in users:
        if user['username'] == username and user['is_active']:
            return user
    return None

def find_user_by_id(user_id):
    """Find user by ID"""
    for user in users:
        if user['id'] == user_id and user['is_active']:
            return user
    return None

def find_patient_by_user_id(user_id):
    """Find patient record by user ID"""
    for patient in patients:
        if patient['user_id'] == user_id:
            return patient
    return None

def find_patient_by_id(patient_id):
    """Find patient record by patient ID"""
    for patient in patients:
        if patient['id'] == patient_id:
            return patient
    return None

def get_patient_appointments(patient_id):
    """Get appointments for a specific patient"""
    patient_appointments = []
    for appointment in appointments:
        if appointment['patient_id'] == patient_id:
            # Get patient and doctor names
            patient = find_patient_by_id(appointment['patient_id'])
            doctor = find_user_by_id(appointment['doctor_id'])
            
            if patient and doctor:
                patient_user = find_user_by_id(patient['user_id'])
                appointment_copy = appointment.copy()
                appointment_copy['patient_name'] = f"{patient_user['first_name']} {patient_user['last_name']}"
                appointment_copy['doctor_name'] = f"{doctor['first_name']} {doctor['last_name']}"
                patient_appointments.append(appointment_copy)
    
    return patient_appointments

def get_all_appointments():
    """Get all appointments with names"""
    all_appointments = []
    for appointment in appointments:
        patient = find_patient_by_id(appointment['patient_id'])
        doctor = find_user_by_id(appointment['doctor_id'])
        
        if patient and doctor:
            patient_user = find_user_by_id(patient['user_id'])
            appointment_copy = appointment.copy()
            appointment_copy['patient_name'] = f"{patient_user['first_name']} {patient_user['last_name']}"
            appointment_copy['doctor_name'] = f"{doctor['first_name']} {doctor['last_name']}"
            all_appointments.append(appointment_copy)
    
    return all_appointments

def get_all_patients():
    """Get all patients with user details"""
    all_patients = []
    for patient in patients:
        user = find_user_by_id(patient['user_id'])
        if user:
            patient_copy = patient.copy()
            patient_copy['first_name'] = user['first_name']
            patient_copy['last_name'] = user['last_name']
            patient_copy['email'] = user['email']
            patient_copy['phone'] = user.get('phone', 'N/A')
            all_patients.append(patient_copy)
    
    return all_patients

def get_patient_users():
    """Get all patient users"""
    patient_users = []
    for user in users:
        if user['role'] == 'patient' and user['is_active']:
            patient_users.append(user)
    return patient_users

def get_doctor_users():
    """Get all doctor users"""
    doctor_users = []
    for user in users:
        if user['role'] == 'doctor' and user['is_active']:
            doctor_users.append(user)
    return doctor_users

def add_medical_record(patient_user_id, doctor_id, record_data):
    """Add a new medical record"""
    medical_record_id = len(medical_records) + 1
    
    # Find patient
    patient = find_patient_by_user_id(patient_user_id)
    if not patient:
        return None
    
    record = {
        'id': medical_record_id,
        'patient_id': patient['id'],
        'doctor_id': doctor_id,
        'record_type': record_data.get('record_type', 'consultation'),
        'title': record_data.get('title', ''),
        'description': record_data.get('description', ''),
        'diagnosis': record_data.get('diagnosis', ''),
        'symptoms': record_data.get('symptoms', ''),
        'created_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    medical_records.append(record)
    
    # If it's a prescription, also add to prescriptions
    if record_data.get('record_type') == 'prescription':
        prescription_id = len(prescriptions) + 1
        prescriptions.append({
            'id': prescription_id,
            'medical_record_id': medical_record_id,
            'medication_name': record_data.get('medication_name', ''),
            'dosage': record_data.get('dosage', ''),
            'frequency': record_data.get('frequency', ''),
            'duration': record_data.get('duration', ''),
            'instructions': record_data.get('instructions', ''),
            'prescribed_date': datetime.datetime.now().strftime('%Y-%m-%d'),
            'status': 'active'
        })
    
    return medical_record_id

def add_consent_record(patient_user_id, consent_data):
    """Add a new consent record"""
    consent_id = len(consent_records) + 1
    
    # Find patient
    patient = find_patient_by_user_id(patient_user_id)
    if not patient:
        return None
    
    record = {
        'id': consent_id,
        'patient_id': patient['id'],
        'consent_type': consent_data.get('consent_type', 'data_processing'),
        'consent_given': consent_data.get('consent_given', True),
        'purpose': consent_data.get('purpose', ''),
        'expiration_date': consent_data.get('expiration_date'),
        'recorded_by': consent_data.get('recorded_by'),
        'created_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    consent_records.append(record)
    return consent_id

def get_patient_consents(patient_user_id):
    """Get consent records for a patient"""
    patient = find_patient_by_user_id(patient_user_id)
    if not patient:
        return []
    
    patient_consents = []
    for consent in consent_records:
        if consent['patient_id'] == patient['id']:
            # Get patient name
            user = find_user_by_id(patient['user_id'])
            if user:
                consent_copy = consent.copy()
                consent_copy['patient_name'] = f"{user['first_name']} {user['last_name']}"
                patient_consents.append(consent_copy)
    
    return patient_consents

def get_all_consents():
    """Get all consent records with names"""
    all_consents = []
    for consent in consent_records:
        patient = find_patient_by_id(consent['patient_id'])
        if patient:
            user = find_user_by_id(patient['user_id'])
            if user:
                consent_copy = consent.copy()
                consent_copy['patient_name'] = f"{user['first_name']} {user['last_name']}"
                all_consents.append(consent_copy)
    
    return all_consents

# ==================== ENCRYPTION FUNCTIONS ====================
def encrypt_data(plaintext, key):
    """Encrypt sensitive data using AES"""
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(plaintext.encode()) + padder.finalize()
    
    encrypted = encryptor.update(padded_data) + encryptor.finalize()
    return base64.b64encode(encrypted).decode('utf-8'), iv

def decrypt_data(encrypted_data, iv, key):
    """Decrypt sensitive data using AES"""
    encrypted_bytes = base64.b64decode(encrypted_data)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    
    decrypted_padded = decryptor.update(encrypted_bytes) + decryptor.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    decrypted = unpadder.update(decrypted_padded) + unpadder.finalize()
    
    return decrypted.decode('utf-8')

# ==================== HTML TEMPLATES ====================

def render_page(content, title="Secure Health Data Management"):
    """Render a complete page with base template and content"""
    base_template = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{0}</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            .sidebar {{ min-height: calc(100vh - 56px); background-color: #f8f9fa; }}
            .main-content {{ padding: 20px; }}
            .navbar-brand {{ font-weight: bold; }}
            .status-pending {{ background-color: #fff3cd; color: #856404; }}
            .status-approved {{ background-color: #d1edff; color: #004085; }}
            .status-completed {{ background-color: #d4edda; color: #155724; }}
            .status-cancelled {{ background-color: #f8d7da; color: #721c24; }}
            .status-scheduled {{ background-color: #d1ecf1; color: #0c5460; }}
            .demo-creds {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 10px; }}
            .demo-creds h6 {{ font-weight: bold; }}
            .password-rules {{ font-size: 0.85rem; }}
            .password-strength {{ height: 5px; margin-top: 5px; }}
        </style>
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
            <div class="container-fluid">
                <a class="navbar-brand" href="/"><i class="fas fa-shield-alt"></i> SecureHealth Lesotho</a>
                <div class="navbar-nav ms-auto">
    '''.format(title)
    
    if session.get('user_id'):
        base_template += '''
                    <span class="navbar-text me-3">Welcome, {0} ({1})</span>
                    <a class="nav-link" href="/logout">Logout</a>
        '''.format(session.get('name', 'User'), session.get('role', 'user'))
    else:
        base_template += '''
                    <a class="nav-link" href="/login">Login</a>
                    <a class="nav-link" href="/register">Register</a>
        '''
    
    base_template += '''
                </div>
            </div>
        </nav>
        <div class="container-fluid">
            <div class="row">
    '''
    
    if session.get('user_id'):
        base_template += '''
                <div class="col-md-2 sidebar p-3">
                    <div class="list-group">
                        <a href="/dashboard" class="list-group-item list-group-item-action"><i class="fas fa-tachometer-alt"></i> Dashboard</a>
        '''
        if session.get('role') == 'patient':
            base_template += '''
                        <a href="/my_appointments" class="list-group-item list-group-item-action"><i class="fas fa-calendar-check"></i> My Appointments</a>
                        <a href="/book_appointment" class="list-group-item list-group-item-action"><i class="fas fa-calendar-plus"></i> Book Appointment</a>
            '''
        elif session.get('role') in ['doctor', 'nurse', 'admin']:
            base_template += '''
                        <a href="/patients" class="list-group-item list-group-item-action"><i class="fas fa-users"></i> Patients</a>
                        <a href="/appointments" class="list-group-item list-group-item-action"><i class="fas fa-calendar-alt"></i> Appointments</a>
                        <a href="/add_medical_record" class="list-group-item list-group-item-action"><i class="fas fa-file-medical"></i> Add Record</a>
            '''
        base_template += '''
                        <a href="/consent" class="list-group-item list-group-item-action"><i class="fas fa-clipboard-check"></i> Consent</a>
                    </div>
                </div>
                <div class="col-md-10 main-content">
        '''
    else:
        base_template += '''
                <div class="col-12">
        '''
    
    # Flash messages section
    base_template += '''
                {% with messages = get_flashed_messages(with_categories=true) %}
                    {% if messages %}
                        {% for category, message in messages %}
                            <div class="alert alert-{{ 'danger' if category == 'error' else 'success' if category == 'success' else 'info' }} alert-dismissible fade show mt-3">
                                {{ message }}
                                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                            </div>
                        {% endfor %}
                    {% endif %}
                {% endwith %}
    '''
    
    base_template += content
    
    base_template += '''
                </div>
            </div>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    '''
    
    return base_template

# ==================== PAGE CONTENT TEMPLATES ====================

def get_login_content():
    """Get login content with registration link"""
    content = '''
<div class="row justify-content-center mt-5">
    <div class="col-md-5">
        <div class="card shadow">
            <div class="card-header bg-primary text-white">
                <h4 class="card-title text-center mb-0"><i class="fas fa-sign-in-alt"></i> Login to SecureHealth Lesotho</h4>
            </div>
            <div class="card-body">
                <form method="POST" action="/login">
                    <div class="mb-3">
                        <label class="form-label"><i class="fas fa-user"></i> Username</label>
                        <input type="text" class="form-control" name="username" required placeholder="Enter your username">
                    </div>
                    <div class="mb-3">
                        <label class="form-label"><i class="fas fa-lock"></i> Password</label>
                        <input type="password" class="form-control" name="password" required placeholder="Enter your password">
                    </div>
                    <button type="submit" class="btn btn-primary w-100">
                        <i class="fas fa-sign-in-alt"></i> Login
                    </button>
                </form>
                
                <div class="text-center mt-3">
                    <p class="mb-2">Don't have an account?</p>
                    <a href="/register" class="btn btn-outline-success">
                        <i class="fas fa-user-plus"></i> Create New Account
                    </a>
                </div>
                
                <div class="demo-creds p-3 mt-4">
                    <h6 class="text-center mb-3"><i class="fas fa-info-circle"></i> Demo Credentials</h6>
                    <div class="row text-center">
                        <div class="col-md-4">
                            <div class="p-2">
                                <div class="bg-white text-dark rounded-circle d-inline-flex align-items-center justify-content-center" style="width: 50px; height: 50px;">
                                    <i class="fas fa-user-shield text-primary"></i>
                                </div>
                                <h6 class="mt-2">Admin</h6>
                                <p class="small mb-0">admin / Admin123!</p>
                                <p class="small">sysadmin / Admin456!</p>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="p-2">
                                <div class="bg-white text-dark rounded-circle d-inline-flex align-items-center justify-content-center" style="width: 50px; height: 50px;">
                                    <i class="fas fa-user-md text-info"></i>
                                </div>
                                <h6 class="mt-2">Doctors</h6>
                                <p class="small mb-0">dr_thabo / Doctor123!</p>
                                <p class="small">dr_masechaba / Doctor456!</p>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="p-2">
                                <div class="bg-white text-dark rounded-circle d-inline-flex align-items-center justify-content-center" style="width: 50px; height: 50px;">
                                    <i class="fas fa-user-injured text-success"></i>
                                </div>
                                <h6 class="mt-2">Patients</h6>
                                <p class="small mb-0">patient_tlali / Patient123!</p>
                                <p class="small">patient_lerato / Patient456!</p>
                            </div>
                        </div>
                    </div>
                    <p class="text-center mt-3 mb-0 small">
                        <i class="fas fa-shield-alt"></i> HIPAA/GDPR Compliant Healthcare System
                    </p>
                </div>
                
                <div class="mt-3 text-center">
                    <small class="text-muted">
                        <i class="fas fa-lock"></i> All data is encrypted and securely stored
                    </small>
                </div>
            </div>
        </div>
    </div>
</div>
'''
    
    return content

def get_register_content():
    """Get registration form content"""
    content = '''
<div class="row justify-content-center mt-5">
    <div class="col-md-8">
        <div class="card shadow">
            <div class="card-header bg-success text-white">
                <h4 class="card-title text-center mb-0"><i class="fas fa-user-plus"></i> Register for SecureHealth Lesotho</h4>
            </div>
            <div class="card-body">
                <form method="POST" action="/register" id="registerForm">
                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label"><i class="fas fa-user"></i> First Name *</label>
                                <input type="text" class="form-control" name="first_name" required placeholder="Enter your first name">
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label"><i class="fas fa-user"></i> Last Name *</label>
                                <input type="text" class="form-control" name="last_name" required placeholder="Enter your last name">
                            </div>
                        </div>
                    </div>
                    
                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label"><i class="fas fa-envelope"></i> Email Address *</label>
                                <input type="email" class="form-control" name="email" required placeholder="Enter your email address">
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label"><i class="fas fa-phone"></i> Phone Number *</label>
                                <input type="tel" class="form-control" name="phone" required placeholder="Enter your phone number">
                            </div>
                        </div>
                    </div>
                    
                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label"><i class="fas fa-user-tag"></i> Username *</label>
                                <input type="text" class="form-control" name="username" required placeholder="Choose a username">
                                <div class="form-text">Must be unique. This will be your login ID.</div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label"><i class="fas fa-users"></i> Account Type *</label>
                                <select class="form-select" name="role" required id="roleSelect">
                                    <option value="">Select your role</option>
                                    <option value="patient">Patient</option>
                                    <option value="doctor">Doctor</option>
                                    <option value="nurse">Nurse</option>
                                </select>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Doctor-specific fields (hidden by default) -->
                    <div id="doctorFields" class="row" style="display: none;">
                        <div class="col-md-12">
                            <div class="mb-3">
                                <label class="form-label"><i class="fas fa-stethoscope"></i> Specialization</label>
                                <input type="text" class="form-control" name="specialization" placeholder="Enter your medical specialization">
                            </div>
                        </div>
                    </div>
                    
                    <!-- Patient-specific fields (hidden by default) -->
                    <div id="patientFields" class="row" style="display: none;">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label"><i class="fas fa-birthday-cake"></i> Date of Birth</label>
                                <input type="date" class="form-control" name="date_of_birth">
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label"><i class="fas fa-venus-mars"></i> Gender</label>
                                <select class="form-select" name="gender">
                                    <option value="">Select gender</option>
                                    <option value="male">Male</option>
                                    <option value="female">Female</option>
                                    <option value="other">Other</option>
                                </select>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label"><i class="fas fa-tint"></i> Blood Type</label>
                                <select class="form-select" name="blood_type">
                                    <option value="Unknown">Unknown</option>
                                    <option value="A+">A+</option>
                                    <option value="A-">A-</option>
                                    <option value="B+">B+</option>
                                    <option value="B-">B-</option>
                                    <option value="AB+">AB+</option>
                                    <option value="AB-">AB-</option>
                                    <option value="O+">O+</option>
                                    <option value="O-">O-</option>
                                </select>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label"><i class="fas fa-allergies"></i> Allergies</label>
                                <input type="text" class="form-control" name="allergies" placeholder="List any allergies (separate by comma)">
                            </div>
                        </div>
                    </div>
                    
                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label"><i class="fas fa-lock"></i> Password *</label>
                                <input type="password" class="form-control" name="password" id="password" required 
                                       placeholder="Create a strong password" onkeyup="checkPasswordStrength()">
                                <div class="password-rules text-muted">
                                    <small>Password must contain:</small>
                                    <ul class="mb-1">
                                        <li id="rule-length">✓ At least 8 characters</li>
                                        <li id="rule-upper">✓ One uppercase letter</li>
                                        <li id="rule-lower">✓ One lowercase letter</li>
                                        <li id="rule-digit">✓ One digit</li>
                                        <li id="rule-special">✓ One special character</li>
                                    </ul>
                                </div>
                                <div class="password-strength">
                                    <div class="progress">
                                        <div id="password-strength-bar" class="progress-bar" role="progressbar" style="width: 0%"></div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label class="form-label"><i class="fas fa-lock"></i> Confirm Password *</label>
                                <input type="password" class="form-control" name="confirm_password" id="confirm_password" required 
                                       placeholder="Confirm your password" onkeyup="checkPasswordMatch()">
                                <div id="password-match" class="form-text"></div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="mb-3 form-check">
                        <input type="checkbox" class="form-check-input" name="terms" id="terms" required>
                        <label class="form-check-label" for="terms">
                            I agree to the <a href="#" data-bs-toggle="modal" data-bs-target="#termsModal">Terms of Service</a> and <a href="#" data-bs-toggle="modal" data-bs-target="#privacyModal">Privacy Policy</a>
                        </label>
                    </div>
                    
                    <div class="d-grid gap-2 d-md-flex justify-content-md-between">
                        <a href="/" class="btn btn-secondary">
                            <i class="fas fa-arrow-left"></i> Back to Login
                        </a>
                        <button type="submit" class="btn btn-success" id="registerBtn">
                            <i class="fas fa-user-plus"></i> Create Account
                        </button>
                    </div>
                </form>
            </div>
        </div>
        
        <div class="text-center mt-3">
            <p class="text-muted">
                <i class="fas fa-shield-alt"></i> Your data is protected with encryption
            </p>
        </div>
    </div>
</div>

<!-- Terms of Service Modal -->
<div class="modal fade" id="termsModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Terms of Service</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <h6>SecureHealth Lesotho Terms of Service</h6>
                <p>By creating an account, you agree to:</p>
                <ul>
                    <li>Provide accurate and complete information</li>
                    <li>Keep your login credentials secure</li>
                    <li>Use the system only for legitimate healthcare purposes</li>
                    <li>Respect patient privacy and confidentiality</li>
                    <li>Comply with HIPAA and GDPR regulations</li>
                </ul>
                <p><strong>Note:</strong> All medical data is encrypted and stored securely.</p>
            </div>
        </div>
    </div>
</div>

<!-- Privacy Policy Modal -->
<div class="modal fade" id="privacyModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Privacy Policy</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <h6>Data Protection and Privacy</h6>
                <p>We are committed to protecting your personal and medical information:</p>
                <ul>
                    <li>All data is encrypted using AES-256 encryption</li>
                    <li>Access is restricted based on user roles</li>
                    <li>We comply with HIPAA and GDPR requirements</li>
                    <li>Your data will not be shared without consent</li>
                    <li>You have the right to access and correct your data</li>
                </ul>
                <p>For more information, contact our Data Protection Officer.</p>
            </div>
        </div>
    </div>
</div>

<script>
// Show/hide role-specific fields
document.getElementById('roleSelect').addEventListener('change', function() {
    var role = this.value;
    document.getElementById('doctorFields').style.display = 'none';
    document.getElementById('patientFields').style.display = 'none';
    
    if (role === 'doctor') {
        document.getElementById('doctorFields').style.display = 'block';
    } else if (role === 'patient') {
        document.getElementById('patientFields').style.display = 'block';
    }
});

// Password strength checker
function checkPasswordStrength() {
    var password = document.getElementById('password').value;
    var strength = 0;
    
    // Length check
    if (password.length >= 8) {
        strength += 20;
        document.getElementById('rule-length').innerHTML = '✓ At least 8 characters';
        document.getElementById('rule-length').style.color = 'green';
    } else {
        document.getElementById('rule-length').innerHTML = '✗ At least 8 characters';
        document.getElementById('rule-length').style.color = 'red';
    }
    
    // Upper case check
    if (/[A-Z]/.test(password)) {
        strength += 20;
        document.getElementById('rule-upper').innerHTML = '✓ One uppercase letter';
        document.getElementById('rule-upper').style.color = 'green';
    } else {
        document.getElementById('rule-upper').innerHTML = '✗ One uppercase letter';
        document.getElementById('rule-upper').style.color = 'red';
    }
    
    // Lower case check
    if (/[a-z]/.test(password)) {
        strength += 20;
        document.getElementById('rule-lower').innerHTML = '✓ One lowercase letter';
        document.getElementById('rule-lower').style.color = 'green';
    } else {
        document.getElementById('rule-lower').innerHTML = '✗ One lowercase letter';
        document.getElementById('rule-lower').style.color = 'red';
    }
    
    // Digit check
    if (/\\d/.test(password)) {
        strength += 20;
        document.getElementById('rule-digit').innerHTML = '✓ One digit';
        document.getElementById('rule-digit').style.color = 'green';
    } else {
        document.getElementById('rule-digit').innerHTML = '✗ One digit';
        document.getElementById('rule-digit').style.color = 'red';
    }
    
    // Special character check
    if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
        strength += 20;
        document.getElementById('rule-special').innerHTML = '✓ One special character';
        document.getElementById('rule-special').style.color = 'green';
    } else {
        document.getElementById('rule-special').innerHTML = '✗ One special character';
        document.getElementById('rule-special').style.color = 'red';
    }
    
    // Update progress bar
    var bar = document.getElementById('password-strength-bar');
    bar.style.width = strength + '%';
    
    if (strength < 60) {
        bar.className = 'progress-bar bg-danger';
    } else if (strength < 80) {
        bar.className = 'progress-bar bg-warning';
    } else {
        bar.className = 'progress-bar bg-success';
    }
}

// Password match checker
function checkPasswordMatch() {
    var password = document.getElementById('password').value;
    var confirm = document.getElementById('confirm_password').value;
    var matchDiv = document.getElementById('password-match');
    
    if (confirm === '') {
        matchDiv.innerHTML = '';
        matchDiv.style.color = '';
    } else if (password === confirm) {
        matchDiv.innerHTML = '✓ Passwords match';
        matchDiv.style.color = 'green';
    } else {
        matchDiv.innerHTML = '✗ Passwords do not match';
        matchDiv.style.color = 'red';
    }
}

// Form validation
document.getElementById('registerForm').addEventListener('submit', function(e) {
    var password = document.getElementById('password').value;
    var confirm = document.getElementById('confirm_password').value;
    
    if (password !== confirm) {
        e.preventDefault();
        alert('Passwords do not match!');
        return false;
    }
    
    // Check password strength
    var strength = 0;
    if (password.length >= 8) strength += 20;
    if (/[A-Z]/.test(password)) strength += 20;
    if (/[a-z]/.test(password)) strength += 20;
    if (/\\d/.test(password)) strength += 20;
    if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) strength += 20;
    
    if (strength < 80) {
        e.preventDefault();
        alert('Please create a stronger password. Your password should contain at least 8 characters with uppercase, lowercase, numbers, and special characters.');
        return false;
    }
    
    return true;
});
</script>
'''
    
    return content

def get_dashboard_content():
    content = '''
<div class="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pt-3 pb-2 mb-3 border-bottom">
    <h1 class="h2"><i class="fas fa-tachometer-alt"></i> Dashboard</h1>
</div>

<div class="row">
    <div class="col-12">
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">Welcome to SecureHealth Lesotho</h5>
                <p class="card-text">HIPAA/GDPR Compliant Healthcare Data Management System</p>
                
                <div class="row mt-4">
                    <div class="col-md-3 mb-3">
                        <div class="card text-white bg-primary h-100">
                            <div class="card-body text-center">
                                <h5><i class="fas fa-shield-alt fa-2x"></i></h5>
                                <h6>Data Security</h6>
                                <p class="small">Encrypted patient records</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3 mb-3">
                        <div class="card text-white bg-success h-100">
                            <div class="card-body text-center">
                                <h5><i class="fas fa-mobile-alt fa-2x"></i></h5>
                                <h6>Mobile Ready</h6>
                                <p class="small">API for mobile apps</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3 mb-3">
                        <div class="card text-white bg-info h-100">
                            <div class="card-body text-center">
                                <h5><i class="fas fa-clipboard-check fa-2x"></i></h5>
                                <h6>Compliance</h6>
                                <p class="small">HIPAA & GDPR Compliant</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3 mb-3">
                        <div class="card text-white bg-warning h-100">
                            <div class="card-body text-center">
                                <h5><i class="fas fa-user-shield fa-2x"></i></h5>
                                <h6>Secure Access</h6>
                                <p class="small">Role-based permissions</p>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="row mt-4">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">
                                <h6><i class="fas fa-user-md"></i> Quick Actions</h6>
                            </div>
                            <div class="card-body">
                                <div class="d-grid gap-2">
    '''
    
    if session.get('role') == 'patient':
        content += '''
                                    <a href="/book_appointment" class="btn btn-outline-primary">
                                        <i class="fas fa-calendar-plus"></i> Book Appointment
                                    </a>
                                    <a href="/my_appointments" class="btn btn-outline-success">
                                        <i class="fas fa-calendar-check"></i> My Appointments
                                    </a>
        '''
    elif session.get('role') in ['doctor', 'nurse', 'admin']:
        content += '''
                                    <a href="/patients" class="btn btn-outline-primary">
                                        <i class="fas fa-users"></i> View Patients
                                    </a>
                                    <a href="/appointments" class="btn btn-outline-success">
                                        <i class="fas fa-calendar-alt"></i> Manage Appointments
                                    </a>
                                    <a href="/add_medical_record" class="btn btn-outline-info">
                                        <i class="fas fa-file-medical"></i> Add Medical Record
                                    </a>
        '''
    
    content += '''
                                    <a href="/consent" class="btn btn-outline-warning">
                                        <i class="fas fa-clipboard-check"></i> Manage Consent
                                    </a>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">
                                <h6><i class="fas fa-mobile-alt"></i> Mobile API</h6>
                            </div>
                            <div class="card-body">
                                <p>Access patient prescriptions via secure API:</p>
                                <code>GET /api/prescriptions/&lt;patient_user_id&gt;</code>
                                <p class="mt-2 small text-muted">Requires authentication. Returns JSON data for mobile apps.</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
'''
    return content

def get_appointments_content(appointments_list, user_role='patient'):
    appointments_html = '''
    <div class="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pt-3 pb-2 mb-3 border-bottom">
        <h1 class="h2"><i class="fas fa-calendar-alt"></i> {0}</h1>
    </div>

    <div class="card">
        <div class="card-header">
            <h5 class="card-title mb-0"><i class="fas fa-list"></i> Appointment List</h5>
        </div>
        <div class="card-body">
    '''.format('My Appointments' if user_role == 'patient' else 'All Appointments')
    
    if appointments_list:
        appointments_html += '''
            <div class="table-responsive">
                <table class="table table-striped table-hover">
                    <thead class="table-dark">
                        <tr>
                            <th>ID</th>
                            <th>Patient</th>
                            <th>Doctor</th>
                            <th>Date & Time</th>
                            <th>Reason</th>
                            <th>Status</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
        '''
        
        for appointment in appointments_list:
            status_class = ''
            if appointment['status'] == 'pending':
                status_class = 'status-pending'
            elif appointment['status'] == 'approved':
                status_class = 'status-approved'
            elif appointment['status'] == 'completed':
                status_class = 'status-completed'
            elif appointment['status'] == 'cancelled':
                status_class = 'status-cancelled'
            elif appointment['status'] == 'scheduled':
                status_class = 'status-scheduled'
            
            # Format datetime for display
            appointment_datetime = appointment['appointment_date']
            if isinstance(appointment_datetime, str):
                try:
                    appointment_datetime = datetime.datetime.strptime(appointment_datetime, '%Y-%m-%d %H:%M:%S')
                except:
                    appointment_datetime = datetime.datetime.now()
            
            appointment_date = appointment_datetime.strftime('%Y-%m-%d')
            appointment_time = appointment_datetime.strftime('%I:%M %p')
            
            appointments_html += '''
                        <tr>
                            <td>{0}</td>
                            <td><strong>{1}</strong></td>
                            <td>{2}</td>
                            <td>{3} at {4}</td>
                            <td>{5}</td>
                            <td><span class="badge {6}">{7}</span></td>
                            <td>
            '''.format(
                appointment['id'],
                appointment.get('patient_name', 'Unknown'),
                appointment.get('doctor_name', 'Unknown'),
                appointment_date,
                appointment_time,
                appointment.get('reason', 'General Checkup'),
                status_class,
                appointment['status'].title()
            )
            
            # Add action buttons
            if user_role == 'patient' and appointment['status'] == 'scheduled':
                appointments_html += '''
                                <button class="btn btn-sm btn-warning" onclick="cancelAppointment({0})">
                                    <i class="fas fa-times"></i> Cancel
                                </button>
                '''.format(appointment['id'])
            elif user_role in ['doctor', 'admin'] and appointment['status'] == 'scheduled':
                appointments_html += '''
                                <button class="btn btn-sm btn-success" onclick="approveAppointment({0})">
                                    <i class="fas fa-check"></i> Approve
                                </button>
                                <button class="btn btn-sm btn-danger" onclick="rejectAppointment({0})">
                                    <i class="fas fa-times"></i> Reject
                                </button>
                '''.format(appointment['id'])
            elif user_role in ['doctor', 'admin'] and appointment['status'] == 'approved':
                appointments_html += '''
                                <button class="btn btn-sm btn-info" onclick="completeAppointment({0})">
                                    <i class="fas fa-check-double"></i> Complete
                                </button>
                '''.format(appointment['id'])
            
            appointments_html += '''
                            </td>
                        </tr>
            '''
        
        appointments_html += '''
                    </tbody>
                </table>
            </div>
        '''
    else:
        appointments_html += '''
            <div class="text-center py-4">
                <i class="fas fa-calendar-times fa-3x text-muted mb-3"></i>
                <p class="text-muted">No appointments found.</p>
            </div>
        '''
    
    appointments_html += '''
        </div>
    </div>
    
    <script>
    function approveAppointment(appointmentId) {
        if (confirm('Are you sure you want to approve this appointment?')) {
            window.location.href = '/appointment/' + appointmentId + '/approve';
        }
    }
    
    function rejectAppointment(appointmentId) {
        if (confirm('Are you sure you want to reject this appointment?')) {
            window.location.href = '/appointment/' + appointmentId + '/reject';
        }
    }
    
    function completeAppointment(appointmentId) {
        if (confirm('Are you sure you want to mark this appointment as completed?')) {
            window.location.href = '/appointment/' + appointmentId + '/complete';
        }
    }
    
    function cancelAppointment(appointmentId) {
        if (confirm('Are you sure you want to cancel this appointment?')) {
            window.location.href = '/appointment/' + appointmentId + '/cancel';
        }
    }
    </script>
    '''
    
    return appointments_html

def get_book_appointment_content(doctors_list):
    content = '''
    <div class="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pt-3 pb-2 mb-3 border-bottom">
        <h1 class="h2"><i class="fas fa-calendar-plus"></i> Book Appointment</h1>
    </div>

    <div class="card">
        <div class="card-header">
            <h5 class="card-title mb-0"><i class="fas fa-plus-circle"></i> New Appointment</h5>
        </div>
        <div class="card-body">
            <form method="POST" action="/book_appointment">
                <div class="row">
                    <div class="col-md-6">
                        <div class="mb-3">
                            <label class="form-label"><i class="fas fa-user-md"></i> Doctor</label>
                            <select class="form-select" name="doctor_id" required>
                                <option value="">Select Doctor</option>
    '''
    
    for doctor in doctors_list:
        specialization = doctor.get('specialization', 'General Practitioner')
        content += '''
                                <option value="{0}">{1} {2} - {3}</option>
        '''.format(doctor['id'], doctor['first_name'], doctor['last_name'], specialization)
    
    content += '''
                            </select>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="mb-3">
                            <label class="form-label"><i class="fas fa-calendar-day"></i> Appointment Date</label>
                            <input type="date" class="form-control" name="appointment_date" required min="{0}">
                        </div>
                    </div>
                </div>
                
                <div class="row">
                    <div class="col-md-6">
                        <div class="mb-3">
                            <label class="form-label"><i class="fas fa-clock"></i> Preferred Time</label>
                            <select class="form-select" name="appointment_time" required>
                                <option value="">Select Time</option>
                                <option value="08:00">08:00 AM</option>
                                <option value="09:00">09:00 AM</option>
                                <option value="10:00">10:00 AM</option>
                                <option value="11:00">11:00 AM</option>
                                <option value="12:00">12:00 PM</option>
                                <option value="13:00">01:00 PM</option>
                                <option value="14:00">02:00 PM</option>
                                <option value="15:00">03:00 PM</option>
                                <option value="16:00">04:00 PM</option>
                            </select>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="mb-3">
                            <label class="form-label"><i class="fas fa-stethoscope"></i> Reason</label>
                            <input type="text" class="form-control" name="reason" required placeholder="Enter appointment reason">
                        </div>
                    </div>
                </div>
                
                <div class="mb-3">
                    <label class="form-label"><i class="fas fa-comment-medical"></i> Additional Notes</label>
                    <textarea class="form-control" name="notes" rows="3" placeholder="Any additional information about your appointment..."></textarea>
                </div>
                
                <div class="d-grid gap-2 d-md-flex justify-content-md-end">
                    <a href="/dashboard" class="btn btn-secondary me-md-2">
                        <i class="fas fa-times"></i> Cancel
                    </a>
                    <button type="submit" class="btn btn-success">
                        <i class="fas fa-calendar-check"></i> Book Appointment
                    </button>
                </div>
            </form>
        </div>
    </div>
    '''.format(datetime.date.today().strftime('%Y-%m-%d'))
    
    return content

def get_patients_content(patients_list):
    patients_html = '''
    <div class="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pt-3 pb-2 mb-3 border-bottom">
        <h1 class="h2"><i class="fas fa-users"></i> Patients</h1>
    </div>

    <div class="card">
        <div class="card-header">
            <h5 class="card-title mb-0"><i class="fas fa-list"></i> Patient List</h5>
        </div>
        <div class="card-body">
    '''
    
    if patients_list:
        patients_html += '''
            <div class="table-responsive">
                <table class="table table-striped table-hover">
                    <thead class="table-dark">
                        <tr>
                            <th>ID</th>
                            <th>Name</th>
                            <th>Email</th>
                            <th>Phone</th>
                            <th>Date of Birth</th>
                            <th>Gender</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
        '''
        
        for patient in patients_list:
            patients_html += '''
                        <tr>
                            <td>{0}</td>
                            <td><strong>{1} {2}</strong></td>
                            <td>{3}</td>
                            <td>{4}</td>
                            <td>{5}</td>
                            <td><span class="badge bg-info">{6}</span></td>
                            <td>
                                <button class="btn btn-sm btn-primary" onclick="viewPatient({0})">
                                    <i class="fas fa-eye"></i> View
                                </button>
                                <button class="btn btn-sm btn-success" onclick="addRecord({7})">
                                    <i class="fas fa-file-medical"></i> Add Record
                                </button>
                            </td>
                        </tr>
            '''.format(
                patient['id'], 
                patient['first_name'], 
                patient['last_name'],
                patient['email'],
                patient.get('phone', 'N/A'),
                patient.get('date_of_birth', 'N/A'),
                patient.get('gender', 'N/A').title(),
                patient['user_id']
            )
        
        patients_html += '''
                    </tbody>
                </table>
            </div>
        '''
    else:
        patients_html += '''
            <div class="text-center py-4">
                <i class="fas fa-users fa-3x text-muted mb-3"></i>
                <p class="text-muted">No patients found.</p>
            </div>
        '''
    
    patients_html += '''
        </div>
    </div>
    
    <script>
    function viewPatient(patientId) {
        alert('View patient details for ID: ' + patientId);
    }
    
    function addRecord(userId) {
        window.location.href = '/add_medical_record?patient_id=' + userId;
    }
    </script>
    '''
    
    return patients_html

def get_add_medical_record_content(patient_users, selected_patient_id=None):
    content = '''
    <div class="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pt-3 pb-2 mb-3 border-bottom">
        <h1 class="h2"><i class="fas fa-file-medical"></i> Add Medical Record</h1>
    </div>

    <div class="card">
        <div class="card-header">
            <h5 class="card-title mb-0"><i class="fas fa-plus-circle"></i> New Medical Record</h5>
        </div>
        <div class="card-body">
            <form method="POST" action="/add_medical_record">
                <div class="row">
                    <div class="col-md-6">
                        <div class="mb-3">
                            <label class="form-label"><i class="fas fa-user"></i> Patient</label>
                            <select class="form-select" name="patient_id" required>
                                <option value="">Select Patient</option>
    '''
    
    for patient in patient_users:
        selected = 'selected' if str(patient['id']) == str(selected_patient_id) else ''
        content += '''
                                <option value="{0}" {1}>{2} {3}</option>
        '''.format(patient['id'], selected, patient['first_name'], patient['last_name'])
    
    content += '''
                            </select>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="mb-3">
                            <label class="form-label"><i class="fas fa-stethoscope"></i> Record Type</label>
                            <select class="form-select" name="record_type" required>
                                <option value="consultation">Consultation</option>
                                <option value="prescription">Prescription</option>
                                <option value="lab_result">Lab Result</option>
                                <option value="radiology">Radiology</option>
                                <option value="surgery">Surgery</option>
                            </select>
                        </div>
                    </div>
                </div>
                
                <div class="mb-3">
                    <label class="form-label"><i class="fas fa-heading"></i> Title</label>
                    <input type="text" class="form-control" name="title" placeholder="Enter record title" required>
                </div>
                
                <div class="mb-3">
                    <label class="form-label"><i class="fas fa-file-alt"></i> Description</label>
                    <textarea class="form-control" name="description" rows="4" placeholder="Enter detailed medical notes and observations"></textarea>
                </div>
                
                <div class="row">
                    <div class="col-md-6">
                        <div class="mb-3">
                            <label class="form-label"><i class="fas fa-diagnoses"></i> Diagnosis</label>
                            <textarea class="form-control" name="diagnosis" rows="3" placeholder="Enter diagnosis"></textarea>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="mb-3">
                            <label class="form-label"><i class="fas fa-thermometer-half"></i> Symptoms</label>
                            <textarea class="form-control" name="symptoms" rows="3" placeholder="Enter patient symptoms"></textarea>
                        </div>
                    </div>
                </div>
                
                <div class="d-grid gap-2 d-md-flex justify-content-md-end">
                    <a href="/dashboard" class="btn btn-secondary me-md-2">
                        <i class="fas fa-times"></i> Cancel
                    </a>
                    <button type="submit" class="btn btn-success">
                        <i class="fas fa-save"></i> Save Medical Record
                    </button>
                </div>
            </form>
        </div>
    </div>
    '''
    
    return content

def get_consent_content(patient_users, consent_records_list):
    content = '''
    <div class="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pt-3 pb-2 mb-3 border-bottom">
        <h1 class="h2"><i class="fas fa-clipboard-check"></i> Consent Management</h1>
    </div>

    <div class="card">
        <div class="card-header">
            <h5 class="card-title mb-0"><i class="fas fa-edit"></i> Record Consent</h5>
        </div>
        <div class="card-body">
            <form method="POST" action="/consent">
                <div class="row">
    '''
    
    if session.get('role') != 'patient':
        content += '''
                    <div class="col-md-6">
                        <div class="mb-3">
                            <label class="form-label"><i class="fas fa-user"></i> Patient</label>
                            <select class="form-select" name="patient_id" required>
                                <option value="">Select Patient</option>
        '''
        for patient in patient_users:
            content += '''
                                <option value="{0}">{1} {2}</option>
            '''.format(patient['id'], patient['first_name'], patient['last_name'])
        content += '''
                            </select>
                        </div>
                    </div>
        '''
    
    content += '''
                    <div class="{0}">
                        <div class="mb-3">
                            <label class="form-label"><i class="fas fa-clipboard-list"></i> Consent Type</label>
                            <select class="form-select" name="consent_type" required>
                                <option value="data_processing">Data Processing</option>
                                <option value="treatment">Medical Treatment</option>
                                <option value="research">Research Participation</option>
                                <option value="data_sharing">Data Sharing</option>
                            </select>
                        </div>
                    </div>
                </div>
                
                <div class="mb-3">
                    <label class="form-label"><i class="fas fa-bullseye"></i> Purpose</label>
                    <textarea class="form-control" name="purpose" rows="3" required placeholder="Describe the purpose of this consent"></textarea>
                </div>
                
                <div class="row">
                    <div class="col-md-6">
                        <div class="mb-3">
                            <label class="form-label"><i class="fas fa-calendar-times"></i> Expiration Date</label>
                            <input type="date" class="form-control" name="expiration_date">
                            <div class="form-text">Leave empty if consent doesn't expire</div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="mb-3">
                            <label class="form-label"><i class="fas fa-check-circle"></i> Consent Status</label>
                            <div class="form-check form-switch mt-2">
                                <input class="form-check-input" type="checkbox" name="consent_given" id="consent_given" checked style="transform: scale(1.5);">
                                <label class="form-check-label" for="consent_given">
                                    <strong>Patient has given consent</strong>
                                </label>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="d-grid">
                    <button type="submit" class="btn btn-primary btn-lg">
                        <i class="fas fa-save"></i> Record Consent
                    </button>
                </div>
            </form>
        </div>
    </div>
    '''.format('col-md-6' if session.get('role') != 'patient' else 'col-12')
    
    if consent_records_list:
        content += '''
    <div class="card mt-4">
        <div class="card-header">
            <h5 class="card-title mb-0"><i class="fas fa-history"></i> Consent History</h5>
        </div>
        <div class="card-body">
            <div class="table-responsive">
                <table class="table table-striped">
                    <thead class="table-dark">
                        <tr>
                            <th>Date</th>
                            <th>Patient</th>
                            <th>Consent Type</th>
                            <th>Given</th>
                            <th>Purpose</th>
                            <th>Expires</th>
                        </tr>
                    </thead>
                    <tbody>
        '''
        
        for consent in consent_records_list:
            patient_name = consent.get('patient_name', session.get('name', 'Current User'))
            purpose = consent.get('purpose', '')[:60] + ('...' if len(consent.get('purpose', '')) > 60 else '')
            consent_given = 'Yes' if consent.get('consent_given') else 'No'
            badge_class = 'bg-success' if consent.get('consent_given') else 'bg-danger'
            expiration = consent.get('expiration_date', 'Never')
            
            content += '''
                        <tr>
                            <td>{0}</td>
                            <td><strong>{1}</strong></td>
                            <td><span class="badge bg-primary">{2}</span></td>
                            <td><span class="badge {3}">{4}</span></td>
                            <td>{5}</td>
                            <td>{6}</td>
                        </tr>
            '''.format(
                consent.get('created_at', ''),
                patient_name,
                consent.get('consent_type', ''),
                badge_class,
                consent_given,
                purpose,
                expiration
            )
        
        content += '''
                    </tbody>
                </table>
            </div>
        </div>
    </div>
        '''
    
    return content

# ==================== ROUTES ====================

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect('/dashboard')
    return render_template_string(render_page(get_login_content(), "Login - SecureHealth Lesotho"))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = find_user_by_username(username)
        
        if user and check_user_password(username, password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['name'] = f"{user['first_name']} {user['last_name']}"
            flash('Login successful! Welcome to SecureHealth Lesotho.', 'success')
            return redirect('/dashboard')
        else:
            if not user:
                flash('User not found. Please check your username or register for a new account.', 'error')
            else:
                flash('Invalid password. Please try again.', 'error')
    
    return render_template_string(render_page(get_login_content(), "Login - SecureHealth Lesotho"))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get form data
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        role = request.form['role']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        phone = request.form['phone']
        
        # Validate required fields
        if not all([username, email, password, confirm_password, role, first_name, last_name, phone]):
            flash('Please fill in all required fields.', 'error')
            return redirect('/register')
        
        # Check if passwords match
        if password != confirm_password:
            flash('Passwords do not match. Please try again.', 'error')
            return redirect('/register')
        
        # Validate password strength
        is_valid, message = validate_password(password)
        if not is_valid:
            flash(message, 'error')
            return redirect('/register')
        
        # Check if terms are accepted
        if 'terms' not in request.form:
            flash('You must agree to the Terms of Service and Privacy Policy.', 'error')
            return redirect('/register')
        
        # Register the user
        success, message = register_user(username, email, password, role, first_name, last_name, phone)
        
        if success:
            flash('Registration successful! You can now login with your credentials.', 'success')
            return redirect('/login')
        else:
            flash(f'Registration failed: {message}', 'error')
            return redirect('/register')
    
    return render_template_string(render_page(get_register_content(), "Register - SecureHealth Lesotho"))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template_string(render_page(get_dashboard_content(), "Dashboard"))

@app.route('/patients')
def patients_route():
    if 'user_id' not in session or session['role'] not in ['doctor', 'nurse', 'admin']:
        flash('Access denied. You need staff privileges to view patients.', 'error')
        return redirect('/dashboard')
    
    patients_data = get_all_patients()
    return render_template_string(render_page(get_patients_content(patients_data), "Patients"))

@app.route('/add_medical_record', methods=['GET', 'POST'])
def add_medical_record_route():
    if 'user_id' not in session or session['role'] not in ['doctor', 'nurse', 'admin']:
        flash('Access denied. You need staff privileges to add medical records.', 'error')
        return redirect('/dashboard')
    
    selected_patient_id = request.args.get('patient_id')
    
    if request.method == 'POST':
        patient_user_id = int(request.form['patient_id'])
        record_type = request.form['record_type']
        title = request.form['title']
        description = request.form['description']
        diagnosis = request.form['diagnosis']
        symptoms = request.form['symptoms']
        
        record_data = {
            'record_type': record_type,
            'title': title,
            'description': description,
            'diagnosis': diagnosis,
            'symptoms': symptoms
        }
        
        record_id = add_medical_record(patient_user_id, session['user_id'], record_data)
        
        if record_id:
            flash('Medical record added successfully!', 'success')
        else:
            flash('Error saving medical record. Please try again.', 'error')
        
        return redirect('/dashboard')
    
    patient_users = get_patient_users()
    return render_template_string(render_page(get_add_medical_record_content(patient_users, selected_patient_id), "Add Medical Record"))

@app.route('/consent', methods=['GET', 'POST'])
def consent_route():
    if 'user_id' not in session:
        return redirect('/login')
    
    if request.method == 'POST':
        consent_type = request.form['consent_type']
        consent_given = 'consent_given' in request.form
        purpose = request.form['purpose']
        expiration_date = request.form['expiration_date'] or None
        
        if session.get('role') != 'patient':
            patient_user_id = int(request.form.get('patient_id'))
        else:
            patient_user_id = session['user_id']
        
        consent_data = {
            'consent_type': consent_type,
            'consent_given': consent_given,
            'purpose': purpose,
            'expiration_date': expiration_date,
            'recorded_by': session['user_id']
        }
        
        consent_id = add_consent_record(patient_user_id, consent_data)
        
        if consent_id:
            flash('Consent recorded successfully!', 'success')
        else:
            flash('Error recording consent. Please try again.', 'error')
        
        return redirect('/consent')
    
    # Get patients for dropdown (if staff)
    patient_users = []
    if session.get('role') != 'patient':
        patient_users = get_patient_users()
    
    # Get consent history
    if session.get('role') == 'patient':
        consent_data = get_patient_consents(session['user_id'])
    else:
        consent_data = get_all_consents()
    
    return render_template_string(render_page(get_consent_content(patient_users, consent_data), "Consent Management"))

@app.route('/book_appointment', methods=['GET', 'POST'])
def book_appointment_route():
    if 'user_id' not in session or session['role'] != 'patient':
        flash('Access denied. Only patients can book appointments.', 'error')
        return redirect('/dashboard')
    
    if request.method == 'POST':
        doctor_id = int(request.form['doctor_id'])
        appointment_date = request.form['appointment_date']
        appointment_time = request.form['appointment_time']
        reason = request.form['reason']
        notes = request.form.get('notes', '')
        
        # Combine date and time
        appointment_datetime = f"{appointment_date} {appointment_time}:00"
        
        # Get patient
        patient = find_patient_by_user_id(session['user_id'])
        
        if patient:
            # Create new appointment
            appointment_id = len(appointments) + 1
            appointment = {
                'id': appointment_id,
                'patient_id': patient['id'],
                'doctor_id': doctor_id,
                'appointment_date': appointment_datetime,
                'status': 'scheduled',
                'reason': reason,
                'notes': notes,
                'created_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            appointments.append(appointment)
            flash('Appointment booked successfully!', 'success')
        else:
            flash('Patient record not found. Please contact administrator.', 'error')
        
        return redirect('/my_appointments')
    
    doctors = get_doctor_users()
    return render_template_string(render_page(get_book_appointment_content(doctors), "Book Appointment"))

@app.route('/my_appointments')
def my_appointments_route():
    if 'user_id' not in session or session['role'] != 'patient':
        flash('Access denied. Only patients can view their appointments.', 'error')
        return redirect('/dashboard')
    
    # Get patient
    patient = find_patient_by_user_id(session['user_id'])
    
    if not patient:
        flash('Patient record not found.', 'error')
        return redirect('/dashboard')
    
    # Get patient's appointments
    patient_appointments = get_patient_appointments(patient['id'])
    return render_template_string(render_page(get_appointments_content(patient_appointments, 'patient'), "My Appointments"))

@app.route('/appointments')
def appointments_route():
    if 'user_id' not in session or session['role'] not in ['doctor', 'nurse', 'admin']:
        flash('Access denied. You need staff privileges to view appointments.', 'error')
        return redirect('/dashboard')
    
    all_appointments = get_all_appointments()
    return render_template_string(render_page(get_appointments_content(all_appointments, session['role']), "All Appointments"))

@app.route('/appointment/<int:appointment_id>/<action>')
def update_appointment_status(appointment_id, action):
    if 'user_id' not in session:
        return redirect('/login')
    
    valid_actions = ['approve', 'reject', 'complete', 'cancel']
    if action not in valid_actions:
        flash('Invalid action.', 'error')
        return redirect(request.referrer or '/dashboard')
    
    # Find appointment
    appointment = None
    for app in appointments:
        if app['id'] == appointment_id:
            appointment = app
            break
    
    if not appointment:
        flash('Appointment not found.', 'error')
        return redirect(request.referrer or '/dashboard')
    
    # Check permissions
    if session['role'] == 'patient':
        patient = find_patient_by_user_id(session['user_id'])
        if not patient or appointment['patient_id'] != patient['id']:
            flash('Access denied.', 'error')
            return redirect('/my_appointments')
        if action != 'cancel' or appointment['status'] != 'scheduled':
            flash('Invalid action for this appointment.', 'error')
            return redirect('/my_appointments')
    
    # Map actions to status
    status_map = {
        'approve': 'approved',
        'reject': 'cancelled',
        'complete': 'completed',
        'cancel': 'cancelled'
    }
    
    new_status = status_map[action]
    
    # Update appointment status
    for app in appointments:
        if app['id'] == appointment_id:
            app['status'] = new_status
            break
    
    flash(f'Appointment {action}d successfully!', 'success')
    
    # Redirect back to appropriate page
    if session['role'] == 'patient':
        return redirect('/my_appointments')
    else:
        return redirect('/appointments')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been successfully logged out.', 'info')
    return redirect('/')

# API endpoint for mobile app to get prescriptions
@app.route('/api/prescriptions/<int:patient_user_id>')
def api_patient_prescriptions(patient_user_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    # Find patient
    patient = find_patient_by_user_id(patient_user_id)
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    
    # Get prescriptions for this patient
    patient_prescriptions = []
    for prescription in prescriptions:
        # Find the medical record for this prescription
        for record in medical_records:
            if record['id'] == prescription['medical_record_id'] and record['patient_id'] == patient['id']:
                # Get doctor info
                doctor = find_user_by_id(record['doctor_id'])
                prescription_copy = prescription.copy()
                if doctor:
                    prescription_copy['doctor_name'] = f"{doctor['first_name']} {doctor['last_name']}"
                patient_prescriptions.append(prescription_copy)
                break
    
    return jsonify(patient_prescriptions)

# Route to display all usernames and passwords
@app.route('/user-credentials')
def user_credentials():
    if 'user_id' not in session or session['role'] != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect('/dashboard')
    
    credentials_html = '''
    <div class="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pt-3 pb-2 mb-3 border-bottom">
        <h1 class="h2"><i class="fas fa-key"></i> User Credentials</h1>
    </div>
    
    <div class="card">
        <div class="card-header">
            <h5 class="card-title mb-0"><i class="fas fa-users"></i> All User Accounts</h5>
        </div>
        <div class="card-body">
            <div class="table-responsive">
                <table class="table table-striped">
                    <thead class="table-dark">
                        <tr>
                            <th>Role</th>
                            <th>Username</th>
                            <th>Email</th>
                            <th>Full Name</th>
                            <th>Registered</th>
                        </tr>
                    </thead>
                    <tbody>
    '''
    
    # Group by role for better organization
    roles = {
        'admin': [],
        'doctor': [],
        'nurse': [],
        'patient': []
    }
    
    for user in users:
        if user['is_active']:
            full_name = f"{user['first_name']} {user['last_name']}"
            roles[user['role']].append((user['username'], user['email'], full_name, user.get('created_at', 'Unknown')))
    
    for role, users_list in roles.items():
        if users_list:
            credentials_html += f'''
                        <tr class="table-{'primary' if role=='admin' else 'info' if role=='doctor' else 'warning' if role=='nurse' else 'success'}">
                            <td colspan="5"><strong>{role.upper()}S</strong></td>
                        </tr>
            '''
            for username, email, full_name, created_at in users_list:
                credentials_html += f'''
                        <tr>
                            <td>{role.title()}</td>
                            <td><code>{username}</code></td>
                            <td>{email}</td>
                            <td>{full_name}</td>
                            <td>{created_at}</td>
                        </tr>
                '''
    
    credentials_html += '''
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    '''
    
    return render_template_string(render_page(credentials_html, "User Credentials"))

@app.route('/debug/data')
def debug_data():
    """Debug endpoint to view all stored data"""
    if 'user_id' not in session or session['role'] != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    data_summary = {
        'users_count': len(users),
        'patients_count': len(patients),
        'appointments_count': len(appointments),
        'medical_records_count': len(medical_records),
        'consent_records_count': len(consent_records),
        'prescriptions_count': len(prescriptions),
        'users': users,
        'patients': patients,
        'appointments': appointments,
        'medical_records': medical_records,
        'consent_records': consent_records,
        'prescriptions': prescriptions
    }
    
    return jsonify(data_summary)

# ==================== START THE APPLICATION ====================
def create_app():
    print("🚀 Starting SecureHealth Lesotho Application...")
    print("🔄 Initializing in-memory data storage...")
    initialize_data()
    return app

if __name__ == '__main__':
    app = create_app()
    print("🌐 Server running on http://localhost:5000")
    print("\n🔐 Password Requirements:")
    print("   - At least 8 characters")
    print("   - At least one uppercase letter")
    print("   - At least one lowercase letter")
    print("   - At least one digit")
    print("   - At least one special character (!@#$%^&*(),.?\":{}|<>)")
    print("\n👥 Available Users (username / password):")
    print("   👑 Admin: admin / Admin123!")
    print("   👑 Admin: sysadmin / Admin456!")
    print("   👨‍⚕️  Doctor: dr_thabo / Doctor123!")
    print("   👨‍⚕️  Doctor: dr_masechaba / Doctor456!")
    print("   👨‍⚕️  Doctor: dr_sefako / Doctor789!")
    print("   👩‍⚕️  Nurse: nurse_mpho / Nurse123!")
    print("   👩‍⚕️  Nurse: nurse_lineo / Nurse456!")
    print("   👤 Patient: patient_tlali / Patient123!")
    print("   👤 Patient: patient_lerato / Patient456!")
    print("   👤 Patient: patient_thabiso / Patient789!")
    print("\n🔗 Open your browser and go to: http://localhost:5000")
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)