import streamlit as st
import pandas as pd
from datetime import datetime
import mysql.connector
import matplotlib.pyplot as plt
import requests
from PIL import Image  
import google.generativeai as ggi

# Configure Gemini AI with the provided API key
ggi.configure(api_key="AIzaSyC01xzADGtvT2Ic-JXmvOKdnRTMUk6kwqc")
model = ggi.GenerativeModel("gemini-pro")
chat = model.start_chat()

# Function to get Gemini AI response
def LLM_Response(question):
    response = chat.send_message(question, stream=True)
    return response

# Function to create a database connection
def create_connection():
    connection = mysql.connector.connect(
        host="mydb-instance1.czqcwa4ac7g1.eu-north-1.rds.amazonaws.com",        # e.g., "localhost" or IP address
        user="admin",    # replace with your MySQL username
        password="adminpass", # replace with your MySQL password
        database="shms"  # replace with your database name
    )
    return connection

# Function to authenticate users by role
def authenticate_user(username, password, role):
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    if role == "admin":
        cursor.execute("SELECT * FROM admin_users WHERE username = %s AND password = %s", (username, password))
    elif role == "doctor":
        cursor.execute("SELECT * FROM doctors WHERE email = %s AND id = %s", (username, password))  # doctor_id as password
    elif role == "patient":
        cursor.execute("SELECT * FROM patients WHERE email = %s AND id = %s", (username, password))  # patient_id as password
    user = cursor.fetchone()
    conn.close()
    return user

# Function to add a new patient to the database
def add_patient(name, email, medical_history):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO patients (name, email, medical_history) VALUES (%s, %s, %s)",
                   (name, email, medical_history))
    conn.commit()
    conn.close()


# Function to retrieve all patients
def get_patients():
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM patients")
    patients = cursor.fetchall()
    conn.close()
    return patients

# Function to retrieve all doctors
def get_doctors(only_available=False):
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    if only_available:
        cursor.execute("SELECT * FROM doctors WHERE available = 1")
    else:
        cursor.execute("SELECT * FROM doctors")
    doctors = cursor.fetchall()
    conn.close()
    return doctors

# Function to add a new doctor to the database
def add_doctor(name, specialty, email, available=True):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO doctors (name, specialty, email, available) VALUES (%s, %s, %s, %s)",
                   (name, specialty, email, available))
    conn.commit()
    conn.close()

# Function to book an appointment
def book_appointment(patient_id, doctor_id, appointment_datetime):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO appointments (patient_id, doctor_id, appointment_datetime, status) VALUES (%s, %s, %s, %s)",
                   (patient_id, doctor_id, appointment_datetime, "Scheduled"))
    conn.commit()
    conn.close()

# Function to update doctor availability
def update_doctor_availability(doctor_id, availability):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE doctors SET available = %s WHERE id = %s", (availability, doctor_id))
    conn.commit()
    conn.close()

# Function to retrieve upcoming appointments for the doctor
def get_upcoming_appointments(doctor_id):
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM appointments 
        WHERE doctor_id = %s
        ORDER BY appointment_datetime
    """, (doctor_id,))
    appointments = cursor.fetchall()
    conn.close()
    return appointments

# Function to prescribe medication
def prescribe_medication(doctor_id, patient_id, medication, dosage, frequency):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO prescriptions (doctor_id, patient_id, medication, dosage, frequency, date_prescribed) 
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (doctor_id, patient_id, medication, dosage, frequency, datetime.now()))
    conn.commit()
    conn.close()

# Function to retrieve patients and their medical history
def generate_report():
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT name, medical_history FROM patients")
    patients = cursor.fetchall()
    conn.close()
    return patients

# Updated function to retrieve upcoming appointments for a patient
def get_patient_appointments(patient_id):
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT appointment_datetime, status 
        FROM appointments 
        WHERE patient_id = %s
        ORDER BY appointment_datetime
    """, (patient_id,))
    appointments = cursor.fetchall()
    conn.close()
    return appointments

# Function to retrieve prescriptions for a patient
def get_patient_prescriptions(patient_id):
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT medication, dosage, frequency, date_prescribed 
        FROM prescriptions 
        WHERE patient_id = %s
        ORDER BY date_prescribed DESC
    """, (patient_id,))
    prescriptions = cursor.fetchall()
    conn.close()
    return prescriptions

# Streamlit app main section
st.title("Smart Healthcare Management System")

# Choose user role
role = st.sidebar.selectbox("Login as", ["Admin", "Doctor", "Patient"])

# Login form
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.subheader(f"Login as {role}")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        user = authenticate_user(username, password, role.lower())
        if user:
            st.session_state.logged_in = True
            st.session_state.user = user
            st.session_state.role = role.lower()
            st.success(f"{role} login successful!")
        else:
            st.error("Invalid credentials.")
else:
    # Admin Dashboard
    if st.session_state.role == "admin":
        st.sidebar.title("Admin Dashboard")
        admin_menu = ["Add Doctor","Add Patient", "View Patients", "View Doctors", "Generate Report"]
        admin_choice = st.sidebar.selectbox("Admin Menu", admin_menu)

        if admin_choice == "Add Doctor":
            st.subheader("Add New Doctor")
            name = st.text_input("Doctor Name")
            specialty = st.text_input("Specialty")
            email = st.text_input("Email")
            available = st.checkbox("Available", value=True)
            if st.button("Add Doctor"):
                add_doctor(name, specialty, email, available)
                st.success(f"Doctor {name} added successfully!")
        
        elif admin_choice == "Add Patient":
            st.subheader("Add New Patient")
            name = st.text_input("Patient Name")
            email = st.text_input("Email")
            medical_history = st.text_area("Medical History")
            if st.button("Add Patient"):
                add_patient(name, email, medical_history)
                st.success(f"Patient {name} added successfully!")

        elif admin_choice == "View Patients":
            st.subheader("All Patients")
            patients = get_patients()
            st.dataframe(pd.DataFrame(patients))

        elif admin_choice == "View Doctors":
            st.subheader("All Doctors")
            doctors = get_doctors()
            st.dataframe(pd.DataFrame(doctors))

        elif admin_choice == "Generate Report":
            st.subheader("Generate Patient Report")
            patients = generate_report()
            
            # Format the patient data for download
            report_text = "System Status: good\n\n" + "\n\n".join([f"Patient: {patient['name']}\nMedical History: {patient['medical_history']}" for patient in patients])
            
            # Display the report in a text area
            st.text_area("Patient List", value=report_text, height=300)

            # Allow download as a text file
            st.download_button(
                label="Download Report as Text File",
                data=report_text,
                file_name="patient_report.txt",
                mime="text/plain"
            )

    # Doctor Dashboard
    elif st.session_state.role == "doctor":
        st.sidebar.title("Doctor Dashboard")
        doctor_menu = ["View My Patients", "Update Availability", "Upcoming Appointments", "Prescribe Medication"]
        doctor_choice = st.sidebar.selectbox("Doctor Menu", doctor_menu)

        if doctor_choice == "View My Patients":
            st.subheader("My Patients")
            doctor_id = st.session_state.user["id"]
            conn = create_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT patients.id, patients.name, patients.medical_history 
                FROM patients 
                JOIN appointments ON patients.id = appointments.patient_id 
                WHERE appointments.doctor_id = %s
            """, (doctor_id,))
            patients = cursor.fetchall()
            conn.close()

            if patients:
                patient_options = [(p['id'], p['name']) for p in patients]
                selected_patient_id = st.selectbox(
                    "Select Patient to View and Update", 
                    options=patient_options, 
                    format_func=lambda x: x[1]
                )[0]

                # Fetch the selected patient's details
                selected_patient = next((p for p in patients if p['id'] == selected_patient_id), None)

                if selected_patient:
                    st.write(f"### {selected_patient['name']}'s Medical History")
                    updated_medical_history = st.text_area(
                        "Medical History",
                        value=selected_patient['medical_history'],
                        height=200,
                        key="medical_history_update"
                    )

                    if st.button("Update Medical History"):
                        conn = create_connection()
                        cursor = conn.cursor()
                        cursor.execute(
                            "UPDATE patients SET medical_history = %s WHERE id = %s",
                            (updated_medical_history, selected_patient_id)
                        )
                        conn.commit()
                        conn.close()
                        st.success(f"{selected_patient['name']}'s medical history updated successfully!")
            else:
                st.write("No patients found.")


        elif doctor_choice == "Update Availability":
            st.subheader("Update Availability")
            doctor_id = st.session_state.user["id"]
            availability = st.radio("Set Availability", options=[1, 0], format_func=lambda x: "Available" if x == 1 else "Busy")
            if st.button("Update Availability"):
                update_doctor_availability(doctor_id, availability)
                st.success("Availability updated!")

        elif doctor_choice == "Upcoming Appointments":
            st.subheader("Upcoming Appointments")
            doctor_id = st.session_state.user["id"]
            upcoming_appointments = get_upcoming_appointments(doctor_id)
            if upcoming_appointments:
                st.dataframe(pd.DataFrame(upcoming_appointments))
            else:
                st.write("No upcoming appointments.")

        elif doctor_choice == "Prescribe Medication":
            st.subheader("Prescribe Medication")
            doctor_id = st.session_state.user["id"]
            
            # Select patient for prescription
            patients = get_patients()
            patient_options = [(p['id'], f"{p['name']}") for p in patients]
            patient_id = st.selectbox("Select Patient", patient_options, format_func=lambda x: x[1])[0]

            medication = st.text_input("Medication Name")
            dosage = st.text_input("Dosage Amount")
            frequency = st.selectbox("Intake Frequency", ["Once a day", "Twice a day", "Every 6 hours", "As needed"])

            if st.button("Prescribe"):
                prescribe_medication(doctor_id, patient_id, medication, dosage, frequency)
                st.success("Prescription successfully created!")

    # Patient Dashboard
    elif st.session_state.role == "patient":
        st.sidebar.title("Patient Dashboard")
        patient_menu = ["View Medical History", "Book Appointment", "Download Medical Summary", "Ask AI", "Notifications"]
        patient_choice = st.sidebar.selectbox("Patient Menu", patient_menu)

        if patient_choice == "View Medical History":
            st.subheader("Medical History")
            patient_id = st.session_state.user["id"]
            conn = create_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM patients WHERE id = %s", (patient_id,))
            patient_data = cursor.fetchone()
            st.write(patient_data["medical_history"])

        elif patient_choice == "Book Appointment":
            st.subheader("Available Doctors")
            doctors = get_doctors(only_available=True)
            doctor_options = [(d['id'], f"{d['name']} ({d['specialty']})") for d in doctors]
            doctor_id = st.selectbox("Select Doctor", options=doctor_options, format_func=lambda x: x[1])[0]
            appointment_date = st.date_input("Appointment Date")
            appointment_time = st.time_input("Appointment Time")
            if st.button("Book Appointment"):
                appointment_datetime = datetime.combine(appointment_date, appointment_time)
                book_appointment(st.session_state.user["id"], doctor_id, appointment_datetime)
                st.success("Appointment booked successfully!")

        elif patient_choice == "Download Medical Summary":
            st.subheader("Download Medical Summary")
            patient_id = st.session_state.user["id"]
            conn = create_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM patients WHERE id = %s", (patient_id,))
            patient_data = cursor.fetchone()
            medical_summary = f"Patient Name: {patient_data['name']}\nMedical History:\n{patient_data['medical_history']}"
            st.download_button("Download Medical Summary", data=medical_summary, file_name="medical_summary.txt")

        elif patient_choice == "Ask AI":
            st.subheader("This is your personal AI assistant for your medical needs")
            question = st.text_input("Ask your question here:")
            if st.button("Ask AI"):
                if question:
                    response = LLM_Response(question)
                    for word in response:
                        st.text(word.text)
                else:
                    st.warning("Please enter a question.")

        elif patient_choice == "Notifications":
            st.subheader("Notifications")

            # Display upcoming appointments
            st.write("### Upcoming Appointments")
            patient_id = st.session_state.user["id"]
            appointments = get_patient_appointments(patient_id)
            if appointments:
                st.dataframe(pd.DataFrame(appointments))
            else:
                st.write("No upcoming appointments.")

            # Display prescriptions
            st.write("### Prescriptions")
            prescriptions = get_patient_prescriptions(patient_id)
            if prescriptions:
                st.dataframe(pd.DataFrame(prescriptions))
            else:
                st.write("No prescriptions found.")

    # Logout
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.success("Logged out successfully.")
