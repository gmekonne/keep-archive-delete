import streamlit as st

# Setup global wide page layout configuration
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# =====================================================================
# DYNAMIC ROUTING NAVIGATION CONTROLLER
# =====================================================================
if not st.session_state.logged_in:
    # Defining individual navigation pages for unauthenticated flows
    login_page = st.Page("app.py", title="🔑 Log In Portal", default=True)
    personal_reg = st.Page("views/register_personal.py", title="📝 Register Personal")
    corporate_reg = st.Page("views/register_corporate.py", title="🏢 Register Corporate")
    reset_pass = st.Page("views/reset_password.py", title="🔓 Reset Password")
    
    # Bundle together inside public authentication options layout
    pg = st.navigation({
        "Authentication Gateway": [login_page, personal_reg, corporate_reg, reset_pass]
    })
    
    # If the user is on the main landing page, render the login form structure
    if pg.title == "🔑 Log In Portal":
        st.set_page_config(page_title="5-Star Portal Login", layout="wide")
        st.title("🔒 5-Star Presentation Rater Portal")
        st.write("Secure Instructor Gateway • Connected directly to Hostinger production servers.")
        
        import pymysql, bcrypt
        # Re-importing connection layout helper internally
        def get_mysql_connection():
            return pymysql.connect(
                host=st.secrets["mysql"]["host"],
                user=st.secrets["mysql"]["user"],
                password=st.secrets["mysql"]["password"],
                database=st.secrets["mysql"]["database"],
                port=st.secrets["mysql"].get("port", 3306),
                cursorclass=pymysql.cursors.DictCursor
            )

        login_email = st.text_input("Email Address", key="login_email_input")
        login_password = st.text_input("Password", type="password", key="login_pass_input")
        
        if st.button("Log In to Dashboard", use_container_width=True):
            try:
                conn = get_mysql_connection()
                with conn.cursor() as cursor:
                    sql = "SELECT userID, fname, lname, password FROM user WHERE email = %s"
                    cursor.execute(sql, (login_email.lower().strip(),))
                    user_record = cursor.fetchone()
                conn.close()
                
                if user_record and bcrypt.checkpw(login_password.encode('utf-8'), user_record["password"].encode('utf-8')):
                    st.session_state.logged_in = True
                    st.session_state.user_id = user_record["userID"]
                    st.session_state.user_name = f"{user_record['fname']} {user_record['lname']}"
                    st.session_state.user_email = login_email.lower().strip()
                    st.success("Access Granted!")
                    st.rerun()
                else:
                    st.error("Invalid email or password.")
            except Exception as ex:
                st.error(f"Database connection error: {ex}")
    else:
        # Otherwise execute and display the chosen views sub-file registration/reset script layout
        pg.run()


else:
    # =====================================================================
    # AUTHENTICATED WORKSPACE: RUNS FULL DASHBOARD FROM VIEWS FOLDER
    # =====================================================================
    # Use python's built-in execution runner to render your dashboard file natively
    with open("views/dashboard.py", encoding="utf-8") as f:
        code = compile(f.read(), "views/dashboard.py", "exec")
        exec(code, globals())
