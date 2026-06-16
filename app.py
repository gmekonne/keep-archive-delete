import streamlit as st

# Keep track of globally isolated authentication session states
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# Global wide dashboard structure settings
st.set_page_config(page_title="ClassParticipation Hub", layout="wide", initial_sidebar_state="expanded")

# =====================================================================
# PUBLIC VIEW: LANDING PAGES & LOGIN SIDEBAR DIRECTORY
# =====================================================================
if not st.session_state.logged_in:
    # Build clean page route links to your sub-files
    home_page = st.Page("views/home.py", title="🏠 Welcome Home", default=True)
    login_page = st.Page("views/login.py", title="🔑 Log In Portal")
    personal_reg = st.Page("views/register_personal.py", title="📝 Register Personal")
    corporate_reg = st.Page("views/register_corporate.py", title="🏢 Register Corporate")
    reset_pass = st.Page("views/reset_password.py", title="🔓 Reset Password")
    
    # Generate the public facing menu directory navigation map
    pg = st.navigation({
        "Information": [home_page],
        "Instructor Account Gateway": [login_page, personal_reg, corporate_reg, reset_pass]
    })
    
    # Render whatever page view file the user selects from the sidebar menu
    pg.run()



else:
    # =====================================================================
    # PRIVATE VIEW: WORKSPACE CONSOLE AREA
    # =====================================================================
    # Define your dashboard view file as the single, active application page routing map
    dashboard_page = st.Page("views/dashboard.py", title="🎓 Instructor Workspace", default=True)
    
    # Passing an empty list to previous sections completely wipes the login/registration links from the left menu
    pg = st.navigation([dashboard_page])
    
    # Natively run the script to display your wide dashboard grids, metric cards, and controls
    pg.run()

