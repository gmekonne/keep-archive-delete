import streamlit as st
import traceback


import pymysql
import socket


# Place this at the very top of app.py, right below your imports


st.title("System Diagnostics")

# Use a container to display the live database status
with st.status("Testing database availability...", expanded=True) as status:
    try:
        connection = pymysql.connect(
            host="31.97.208.88",
            user="your_username",
            password="your_password",
            database="your_db_name",
            connect_timeout=5  # Fast timeout keeps the app responsive
        )
        status.update(label="🚀 Database Connected Successfully!", state="complete", expanded=False)
        connection.close()
    except Exception as e:
        status.update(label="❌ Database Connection Timeout", state="error", expanded=True)
        st.error(f"Failed to execute pre-flight database scans: {e}")
        st.info("The server firewall is dropping traffic from the cloud network. Please verify port 3306 rules.")


########## Setup global application authorization tracker states
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# Global wide dashboard structure settings
st.set_page_config(page_title="ClassParticipation Hub", layout="wide", initial_sidebar_state="expanded")

# =====================================================================
# PUBLIC CONFIGURATION: LANDING PAGES & STUDENT HUBS (NO LOGIN REQUIRED)
# =====================================================================
if not st.session_state.logged_in:
    # Core Landing Information
    home_page = st.Page("views/home.py", title="🏠 Welcome Home", default=True)
    
    # Core Instructor Sign In & Registration Pages
    login_page = st.Page("views/login.py", title="🔑 Instructor Sign In")
    personal_reg = st.Page("views/register_personal.py", title="📝 Register Personal")
    corporate_reg = st.Page("views/register_corporate.py", title="🏢 Register Corporate")
    reset_pass = st.Page("views/reset_password.py", title="🔓 Reset Password")
    
    # Student Zone Workspace Route Identifiers (Cleaned)
    st_create_acct = st.Page("views/student_create_account.py", title="👤 Create Student Account")
    st_enter_pres  = st.Page("views/student_enter_presentation.py", title="🎤 Enter Presentation")
    st_view_dates  = st.Page("views/student_view_dates.py", title="📅 View Presentation Dates")
    st_view_inst   = st.Page("views/student_view_instructions.py", title="📋 View Presentation Guidelines")
    st_view_rating = st.Page("views/student_view_ratings.py", title="⭐ View Ratings & Feedback")
    st_view_guide  = st.Page("views/student_view_guide.py", title="📖 View Student Guide")
    st_enter_contrib = st.Page("views/student_enter_contribution.py", title="💡 Enter Class Contributions")
    st_ai_feedback = st.Page("views/student_ai_feedback.py", title="🤖 AI-Generated Feedback")
    
    # Register the hidden evaluation form page at system core root level
    st_hidden_form = st.Page("views/student_rate_form.py", title="Rate Current Presentation")

    # --- FIXED: STANDARD ROUTING TREE PLACEMENT ---
    # We include corporate_reg and st_hidden_form natively within their respective sections
    # This prevents the server from dropping connections when query strings hit the URL
    pg = st.navigation({
        "Information Channel": [home_page],
        "Instructor Executive Gate": [login_page, personal_reg, corporate_reg, reset_pass],
        "Student Zone Workspace": [
            st_create_acct, st_enter_pres, st_view_dates, st_view_inst, 
            st_view_rating, st_view_guide, st_enter_contrib, st_ai_feedback
        ]
    })
    pg.run()

# =====================================================================
# PRIVATE CONFIGURATION: LOCKED SECURE INSTRUCTOR AREA
# =====================================================================
else:
    dashboard_page = st.Page("views/dashboard.py", title="📊 Instructor Overview Console", default=True)
    pg = st.navigation({"Instructor Console": [dashboard_page]})
    pg.run()
