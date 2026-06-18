import streamlit as st

st.title("👤 Student Registration Portal")
st.write("Create your profile to participate in evaluations and submit links.")

with st.form("student_reg_form"):
    st_id = st.text_input("Student Institutional ID (Required) *")
    email = st.text_input("Institutional Email Address *")
    password = st.text_input("Create Password", type="password")
    fname = st.text_input("First Name")
    lname = st.text_input("Last Name")
    
    st.info("💡 Your instructor will provide the exact Code below to lock you to the class roster:")
    target_course_code = st.text_input("Enter Classroom Access Code (e.g., COMP101-SecA)")
    
    submit = st.form_submit_button("Create Account Profile", width="stretch")

if submit:
    st.warning("Database insert module pending connectivity setup.")
