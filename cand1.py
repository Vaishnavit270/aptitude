import pandas as pd
import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.pdfgen import canvas
import os
import random
import pymysql

# SMTP Configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = "vaishnavit22hcompe@student.mes.ac.in"  # Change this
EMAIL_PASSWORD = "elfc tfvx abuf vdzp"  # Change this

# Database connection
conn = pymysql.connect(
    host="localhost",
    user="root",  # Change this
    password="Vaish@27",  # Change this
    database="random_no",  # Change this
    cursorclass=pymysql.cursors.DictCursor
)
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS candidates (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255),
        email VARCHAR(255) UNIQUE,
        job_title VARCHAR(255),
        company_name VARCHAR(255),
        unique_code INT
    )
""")
conn.commit()

def create_offer_letter(candidate_name, job_title, company_name):
    pdf_filename = f"Offer_Letter_{candidate_name.replace(' ', '_')}.pdf"
    
    c = canvas.Canvas(pdf_filename, pagesize=letter)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(200, 750, f"{company_name}")
    
    c.setFont("Helvetica", 12)
    c.setFillColor(colors.black)
    c.line(50, 740, 550, 740)
    
    c.drawString(50, 720, "Date: _______________")
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, 690, f"Dear {candidate_name},")
    
    c.setFont("Helvetica", 12)
    text = f"""
    We are delighted to offer you the position of {job_title} at {company_name}.
    
    Your skills and experience have impressed us, and we believe you will be 
    a valuable addition to our team. Please find below the key details 
    regarding your employment:

    - Position: {job_title}
    - Company: {company_name}
    - Start Date: _______________
    - Salary: _______________

    Please sign and return this letter as confirmation of your acceptance.
    
    Welcome to the team!

    Best regards,
    HR Team,
    {company_name}
    """
    
    text_lines = text.split("\n")
    y_position = 670
    for line in text_lines:
        c.drawString(50, y_position, line.strip())
        y_position -= 20
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y_position - 40, "___________________________")
    c.drawString(50, y_position - 55, "Authorized Signatory")
    c.drawString(50, y_position - 70, f"{company_name}")
    
    c.save()
    return pdf_filename

def generate_unique_code():
    return random.randint(100000, 999999)

def save_candidate_to_db(name, email, job_title, company_name, unique_code):
    cursor.execute("""
        INSERT INTO candidates (name, email, job_title, company_name, unique_code)
        VALUES (%s, %s, %s, %s, %s)
    """, (name, email, job_title, company_name, unique_code))
    conn.commit()

def send_email(to_email, candidate_name, job_title, company_name):
    if pd.isna(to_email) or not to_email.strip():
        st.warning(f"Skipping {candidate_name} due to missing email.")
        return False

    unique_code = generate_unique_code()
    save_candidate_to_db(candidate_name, to_email, job_title, company_name, unique_code)
    
    aptitude_test_link = "http://yourwebsite.com/aptitude_test.html"
    interview_link = "http://yourwebsite.com/interview.py"
    
    subject = f"Job Selection Notification from {company_name}"
    
    body = f"""Dear {candidate_name},

Congratulations! You have been selected for the {job_title} position at {company_name}.

As part of the hiring process, you will need to complete the following rounds:

[1] **Aptitude Round:** Complete the test at the link below:
    {aptitude_test_link}
    
[2] **Interview Round:** You will have a technical interview conducted via our automated system:
    {interview_link}
    
[3] **HR Round:** If you pass the first two rounds, you will be invited for a final HR interview. The venue details will be provided upon clearing the previous rounds.

Your unique code for this process: **{unique_code}**

Best regards,  
HR Team  
{company_name}
"""
    
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    
    pdf_filename = create_offer_letter(candidate_name, job_title, company_name)
    with open(pdf_filename, "rb") as attachment:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f"attachment; filename={pdf_filename}")
        msg.attach(part)
    
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, to_email, msg.as_string())
        server.quit()
        os.remove(pdf_filename)
        return True
    except Exception as e:
        st.error(f"Error sending email to {candidate_name} ({to_email}): {e}")
        return False

def main():
    st.title("Candidate Selection System")
    
    company_name = st.text_input("Enter Your Company Name")
    if not company_name.strip():
        st.warning("Please enter your company name before proceeding.")
    
    uploaded_file = st.file_uploader("Upload CSV File", type=["csv"])
    job_requirements = st.text_input("Enter Job Requirements (e.g., Data Science, Marketing)")
    
    if uploaded_file and job_requirements and company_name.strip():
        df = pd.read_csv(uploaded_file)
        if "Name" not in df.columns or "Mail" not in df.columns:
            st.error("CSV file must contain 'Name' and 'Mail' columns.")
            return
        
        selected_candidates = st.multiselect("Select Candidates to Notify", df['Name'].tolist())
        
        if st.button("Notify Selected Candidates"):
            for candidate in selected_candidates:
                candidate_row = df[df['Name'] == candidate].iloc[0]
                email = candidate_row['Mail']
                
                if send_email(email, candidate, job_requirements, company_name):
                    st.success(f"Email sent to {candidate} ({email}) with Offer Letter")
                else:
                    st.error(f"Failed to send email to {candidate}")
    
if __name__ == "__main__":
    main()