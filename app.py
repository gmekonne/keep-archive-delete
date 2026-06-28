import streamlit as st
import traceback

# Setup global application authorization tracker states
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# Global wide dashboard structure settings
st.set_page_config(page_title="ClassParticipation Hub", layout="wide", initial_sidebar_state="expanded")

# =====================================================================
# PUBLIC CONFIGURATION: LANDING PAGES & STUDENT HUBS (NO LOGIN REQUIRED)
# =====================================================================
if not st.session_state.logged_in:
    # Core Landing Information (Left at the absolute top)
    home_page = st.Page("views/home.py", title="🏠 Welcome Home", default=True)
    
    # Core Instructor Sign In & Registration Pages
    login_page = st.Page("views/login.py", title="🔑 Instructor Sign In")
    personal_reg = st.Page("views/register_personal.py", title="📝 Register Personal")
    corporate_reg = st.Page("views/register_corporate.py", title="🏢 Register Corporate")
    reset_pass = st.Page("views/reset_password.py", title="🔓 Reset Password")
    
    # Student Zone Workspace Route Identifiers (Cleaned: Numbers completely removed)
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

    # Check the URL address parameters BEFORE mounting the sidebar menu layout tree
    url_params = st.query_params
    
    # --- SMART OVERRIDE INTERCEPTOR ---
    if "page" in url_params and str(url_params["page"]) == "student_rate_form":
        pg = st.navigation([st_hidden_form], position="hidden")
        pg.run()
    else:
        # --- FIXED ALIGNMENT: Welcome Top, Instructor Second, Clean Student Third ---
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
