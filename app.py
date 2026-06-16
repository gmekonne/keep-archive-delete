import streamlit as st

# Setup global application authorization tracker states
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# =====================================================================
# PUBLIC CONFIGURATION: AVAILABLE TO ALL VISITORS (NO LOGIN REQUIRED)
# =====================================================================
if not st.session_state.logged_in:
    # Public Information & Login Pages
    home_page = st.Page("views/home.py", title="🏠 Welcome Home", default=True)
    login_page = st.Page("views/login.py", title="🔑 Instructor Sign In")
    personal_reg = st.Page("views/register_personal.py", title="📝 Register Personal")
    corporate_reg = st.Page("views/register_corporate.py", title="🏢 Register Corporate")
    reset_pass = st.Page("views/reset_password.py", title="🔓 Reset Password")
    
    # NEW PUBLIC LINK: Student Portal (Does not require login)
    student_page = st.Page("views/student_dashboard.py", title="🎓 Student Hub Portal")
    
    # Group the public pages into clean categories in the left sidebar menu
    pg = st.navigation({
        "Information": [home_page],
        "Student Zone": [student_page],
        "Instructor Account Gateway": [login_page, personal_reg, corporate_reg, reset_pass]
    })
    
    # Natively render the selected public view file script
    pg.run()

# =====================================================================
# PRIVATE CONFIGURATION: LOCKED SECURE INSTRUCTOR AREA
# =====================================================================
else:
    # Once an instructor logs in, switch the entire sidebar to the private workspace view
    dashboard_page = st.Page("views/dashboard.py", title="📊 Instructor Overview Console", default=True)
    
    pg = st.navigation({
        "Instructor Console": [dashboard_page]
    })
    
    pg.run()
