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
    # Core Landing Information
    home_page = st.Page("views/home.py", title="🏠 Welcome Home", default=True)
    login_page = st.Page("views/login.py", title="🔑 Instructor Sign In")
    
    # Core Instructor Sign Up Pages
    personal_reg = st.Page("views/register_personal.py", title="📝 Register Personal")
    corporate_reg = st.Page("views/register_corporate.py", title="🏢 Register Corporate")
    reset_pass = st.Page("views/reset_password.py", title="🔓 Reset Password")
    
    # Student Zone Workspace Route Identifiers
    st_create_acct = st.Page("views/student_create_account.py", title="👤 1. Create Student Account")
    st_enter_pres  = st.Page("views/student_enter_presentation.py", title="🎤 2. Enter Presentation")
    st_view_dates  = st.Page("views/student_view_dates.py", title="📅 3. View Presentation Dates")
    st_view_inst   = st.Page("views/student_view_instructions.py", title="📋 4. View Presentation Guidelines")
    st_view_rating = st.Page("views/student_view_ratings.py", title="⭐ 5. View Ratings & Feedback")
    st_view_guide  = st.Page("views/student_view_guide.py", title="📖 6. View Student Guide")
    st_enter_contrib = st.Page("views/student_enter_contribution.py", title="💡 7. Enter Class Contributions")
    st_ai_feedback = st.Page("views/student_ai_feedback.py", title="🤖 8. AI-Generated Feedback")
    
    # REGISTER THE RATER FORM AS A REAL PAGE AT THE SYSTEM CORE LEVEL
    # Note: Streamlit uses the python filename without extension as its URL target slug value name
    st_hidden_form = st.Page("views/student_rate_form.py", title="Rate Current Presentation")

    # Check the URL address parameters BEFORE mounting the sidebar menu
    url_params = st.query_params
    
    # --- SMART OVERRIDE INTERCEPTOR ---
    # If a student clicks a Brightspace link targeting our secret rater page, we bypass the sidebar menu rules
    if "page" in url_params and str(url_params["page"]) == "student_rate_form":
        pg = st.navigation([st_hidden_form], position="hidden")
        pg.run()
    else:
        # Construct the normal, organized public sidebar navigation tree layout dictionary
        pg = st.navigation({
            "Information Channel": [home_page],
            "Student Zone Workspace": [
                st_create_acct, st_enter_pres, st_view_dates, st_view_inst, 
                st_view_rating, st_view_guide, st_enter_contrib, st_ai_feedback
            ],
            "Instructor Executive Gate": [login_page, personal_reg, corporate_reg, reset_pass]
        })
        pg.run()

# =====================================================================
# PRIVATE CONFIGURATION: LOCKED SECURE INSTRUCTOR AREA
# =====================================================================
else:
    dashboard_page = st.Page("views/dashboard.py", title="📊 Instructor Overview Console", default=True)
    pg = st.navigation({"Instructor Console": [dashboard_page]})
    pg.run()
