import streamlit as st
import traceback


import socket


st.title("Network Diagnostic Test")

try:
    # Attempt to open a raw network socket to the database on port 3306
    # Timeout after 5 seconds so the app doesn't freeze permanently
    socket.create_connection(("31.97.208.88", 3306), timeout=5)
    st.success("🚀 Success! The cloud server CAN reach the MySQL port.")
except socket.timeout:
    st.error("❌ Network Timeout: The database firewall is blocking your cloud server.")
except Exception as e:
    st.error(f"❌ Connection failed: {e}")


# Setup global application authorization tracker states
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
