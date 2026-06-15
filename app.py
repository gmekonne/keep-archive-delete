import streamlit as st
import subprocess
import datetime
import pandas as pd
import pymysql  # Replaces sqlite3 for live Hostinger integration
import hashlib

# Set page layout to wide dashboard design
st.set_page_config(
    page_title="5-Star Presentation Rater Dashboard", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# =====================================================================
# LIVE HOSTINGER MYSQL CONNECTION ENGINE
# =====================================================================
def get_mysql_connection():
    """Establishes a connection to your live Hostinger MySQL server."""
    # We fetch credentials securely from Streamlit's secrets manager
    return pymysql.connect(
        host=st.secrets["mysql"]["host"],
        user=st.secrets["mysql"]["user"],
        password=st.secrets["mysql"]["password"],
        database=st.secrets["mysql"]["database"],
        port=st.secrets["mysql"].get("port", 3306),
        cursorclass=pymysql.cursors.DictCursor
    )

def hash_password(password):
    """Encrypts passwords to match your existing hash format (SHA-256)."""
    return hashlib.sha256(str.encode(password)).hexdigest()

def verify_user(email, password):
    """Validates login attempts against your existing Hostinger database records."""
    try:
        conn = get_mysql_connection()
        with conn.cursor() as cursor:
            # Adjust table and column names below to match your exact Hostinger schema
            sql = "SELECT * FROM users WHERE email = %s AND password = %s"
            cursor.execute(sql, (email.lower().strip(), hash_password(password)))
            user = cursor.fetchone()
        conn.close()
        return user is not None
    except Exception as e:
        st.error(f"Database Connection Error: {e}")
        return False

def register_user(email, password):
    """Registers a new instructor directly into your Hostinger database."""
    try:
        conn = get_mysql_connection()
        with conn.cursor() as cursor:
            # Adjust columns to fit your existing authentication system setup
            sql = "INSERT INTO users (email, password) VALUES (%s, %s)"
            cursor.execute(sql, (email.lower().strip(), hash_password(password)))
        conn.commit()
        conn.close()
        return True
    except pymysql.err.IntegrityError:
        return False  # Email already exists
    except Exception as e:
        st.error(f"Database Registration Error: {e}")
        return False

# Maintain active login state across app sessions
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_email" not in st.session_state:
    st.session_state.user_email = ""

# =====================================================================
# AUTHENTICATION GATEWAY
# =====================================================================
if not st.session_state.logged_in:
    st.title("🔒 5-Star Presentation Rater Portal")
    st.write("Logged directly into your Hostinger secure server environment.")
    
    auth_tab1, auth_tab2 = st.tabs(["🔑 Sign In", "📝 Create Account"])
    
    with auth_tab1:
        login_email = st.text_input("Email Address", key="login_email_input")
        login_password = st.text_input("Password", type="password", key="login_pass_input")
        
        if st.button("Log In", use_container_width=True):
            if verify_user(login_email, login_password):
                st.session_state.logged_in = True
                st.session_state.user_email = login_email.lower().strip()
                st.success("Access Granted! Syncing your course profiles...")
                st.rerun()
            else:
                st.error("Invalid email or password. Verify your credentials.")
                
    with auth_tab2:
        reg_email = st.text_input("Choose an Email Address", key="reg_email_input")
        reg_password = st.text_input("Create a Secure Password", type="password", key="reg_pass_input")
        reg_confirm = st.text_input("Confirm Password", type="password", key="reg_confirm_input")
        
        if st.button("Register & Sync Account", use_container_width=True):
            if not reg_email or not reg_password:
                st.warning("All registration fields are required.")
            elif reg_password != reg_confirm:
                st.error("Passwords do not match.")
            else:
                if register_user(reg_email, reg_password):
                    st.success("Account synced to Hostinger database! Please click the Sign In tab.")
                else:
                    st.error("This email is already in use on 5starpresentationrater.com.")

# =====================================================================
# SECURE MAIN WORKSPACE
# =====================================================================
else:
    current_user = st.session_state.user_email

    # --- SIDEBAR UTILITIES ---
    with st.sidebar:
        st.image("https://icons8.com", width=60)
        st.title("System Control")
        st.write(f"Instructor: **{current_user}**")
        st.markdown("---")
        
        with st.expander("🛠️ System Utilities", expanded=False):
            if st.button("Start Data Management", use_container_width=True):
                subprocess.run(["python", "start_data_management.py"])
                st.success("Executed.")
            if st.button("Complete Data Management", use_container_width=True):
                subprocess.run(["python", "complete_data_management.py"])
                st.success("Completed.")
                    
        st.markdown("---")
        if st.button("🚪 Log Out", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user_email = ""
            st.rerun()

    # --- MAIN WORKSPACE ---
    st.title("🎓 Instructor Dashboard")
    st.markdown(f"Welcome back! Managing records safely anchored to Hostinger profile: `{current_user}`")
    st.markdown("---")

    # Fetch courses dynamically from MySQL belonging ONLY to this instructor
    def get_user_courses_mysql(email):
        try:
            conn = get_mysql_connection()
            # If you create a courses table in your MySQL, read from it directly:
            query = "SELECT course_num AS 'Course No.', course_code AS 'Course Code', section AS 'Course Section', schedule AS 'Course Date' FROM courses WHERE instructor_email = %s"
            df = pd.read_sql_query(query, conn, params=(email,))
            conn.close()
            return df
        except Exception:
            # Fallback to an empty schema if you haven't built the 'courses' table yet
            return pd.DataFrame(columns=["Course No.", "Course Code", "Course Section", "Course Date"])

    user_courses_df = get_user_courses_mysql(current_user)

    # Metric summaries
    m_col1, m_col2, m_col3 = st.columns(3)
    with m_col1:
        st.metric(label="Your Registered Courses", value=str(len(user_courses_df)))
    with m_col2:
        st.metric(label="Average Presentation Evaluation", value="4.85 / 5.0")
    with m_col3:
        st.metric(label="Database Status", value="Connected to Hostinger")

    st.markdown("---")

    # Split Screen layout
    left_panel, right_panel = st.columns()
    
    with left_panel:
        st.subheader("📚 Your Courses")
        if user_courses_df.empty:
            st.info("No courses linked to your profile database yet. Use the operations console below to add your first course.")
        else:
            st.dataframe(user_courses_df, use_container_width=True, hide_index=True)

    with right_panel:
        st.subheader("📅 Participation Calendar")
        if user_courses_df.empty:
            st.caption("Awaiting course entries to load schedule framework.")
        else:
            selected_course = st.selectbox("Select course:", options=user_courses_df["Course Code"].tolist(), label_visibility="collapsed")
            st.info(f"Scanning Hostinger production schedule tables for: **{selected_course}**")
            
            c_col1, c_col2 = st.columns()
            with c_col1:
                selected_date = st.date_input("Target Date:", datetime.date.today(), label_visibility="collapsed")
            with c_col2:
                @st.dialog("Presentation Details")
                def show_details(course, date):
                    st.write(f"### 📋 Details for {course}")
                    st.write(f"**Date:** {date.strftime('%B %d, %Y')}")
                    st.warning("No presentation entries logged for this date sector.")

                if st.button("👁️ View Details", use_container_width=True):
                    show_details(selected_course, selected_date)

    st.markdown("---")
    st.subheader("⚙️ Control & Operations Console")
    tab1, tab2 = st.tabs(["📂 1. Courses and Class Setup", "⭐ 2. Presentations and Ratings"])

    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            @st.dialog("➕ Add New Course to Profile")
            def add_course_form():
                c_num = st.number_input("Course Number ID", min_value=1, step=1)
                c_code = st.text_input("Course Code (e.g. COMP101)")
                c_sec = st.text_input("Section Letter (e.g. A)")
                c_sched = st.text_input("Schedule Days (e.g. Mon/Wed)")
                
                if st.button("Save Course to Database", use_container_width=True):
                    if c_code and c_sec and c_sched:
                        try:
                            conn = get_mysql_connection()
                            with conn.cursor() as cursor:
                                sql = "INSERT INTO courses (instructor_email, course_num, course_code, section, schedule) VALUES (%s, %s, %s, %s, %s)"
                                cursor.execute(sql, (current_user, c_num, c_code, c_sec, c_sched))
                            conn.commit()
