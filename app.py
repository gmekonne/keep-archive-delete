import streamlit as st
import traceback

# Setup global application authorization tracker states
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# Global wide dashboard structure settings
st.set_page_config(page_title="ClassParticipation Hub", layout="wide", initial_sidebar_state="expanded")

# =====================================================================
# DYNAMIC ROUTING NAVIGATION BLUEPRINT
# =====================================================================
try:
    if not st.session_state.logged_in:
        # Public Information & Login Pages
        home_page = st.Page("views/home.py", title="🏠 Welcome Home", default=True)
        login_page = st.Page("views/login.py", title="🔑 Instructor Sign In")
        personal_reg = st.Page("views/register_personal.py", title="📝 Register Personal")
        corporate_reg = st.Page("views/register_corporate.py", title="🏢 Register Corporate")
        reset_pass = st.Page("views/reset_password.py", title="🔓 Reset Password")
        student_page = st.Page("views/student_dashboard.py", title="🎓 Student Hub Portal")
        
        # Group the public pages into clean categories in the left sidebar menu
        pg = st.navigation({
            "Information": [home_page],
            "Student Zone": [student_page],
            "Instructor Account Gateway": [login_page, personal_reg, corporate_reg, reset_pass]
        })
        pg.run()

    else:
        # Once an instructor logs in, switch the entire sidebar to the private workspace view
        dashboard_page = st.Page("views/dashboard.py", title="📊 Instructor Overview Console", default=True)
        pg = st.navigation({"Instructor Console": [dashboard_page]})
        pg.run()

except Exception as route_error:
    st.error("🚨 Compilation Error Detected in Page Sub-Files!")
    st.write("One of your views contains invalid syntax or an incomplete code block.")
    
    # Extract the precise filename and line error layout context from python internals
    error_details = traceback.format_exc()
    st.code(error_details, language="text")
