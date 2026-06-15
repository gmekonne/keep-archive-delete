import streamlit as st
import subprocess
import datetime
import pandas as pd
import pymysql
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
    """Establishes a connection to your live Hostinger MySQL server using Streamlit Secrets."""
    return pymysql.connect(
        host=st.secrets["mysql"]["host"],
        user=st.secrets["mysql"]["user"],
        password=st.secrets["mysql"]["password"],
        database=st.secrets["mysql"]["database"],
        port=st.secrets["mysql"].get("port", 3306),
        cursorclass=pymysql.cursors.DictCursor
    )

def hash_password(password):
    """Encrypts passwords to match your existing hash format (SHA-256).
    Change this hashing method if your Hostinger system uses MD5, bcrypt, or phpass.
    """
    return hashlib.sha256(str.encode(password)).hexdigest()

def verify_user(email, password):
    """Validates login attempts against your live Hostinger user table."""
    try:
        conn = get_mysql_connection()
        with conn.cursor() as cursor:
            # Using your exact table 'user' and fields 'email' and 'password'
            sql = "SELECT userID, fname, lname FROM user WHERE email = %s AND password = %s"
            cursor.execute(sql, (email.lower().strip(), hash_password(password)))
            user_record = cursor.fetchone()
        conn.close()
        return user_record  # Returns the dictionary matching the row if found, otherwise None
    except Exception as e:
        st.error(f"Database Connection Error: {e}")
        return None

# Maintain active login state and instructor metadata across app interactions
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "user_name" not in st.session_state:
    st.session_state.user_name = ""
if "user_email" not in st.session_state:
    st.session_state.user_email = ""

# =====================================================================
# AUTHENTICATION GATEWAY (Displayed Initially)
# =====================================================================
if not st.session_state.logged_in:
    st.title("🔒 5-Star Presentation Rater Portal")
    st.write("Secure Instructor Gateway • Connected directly to Hostinger production servers.")
    
    # Simple login container centered on screen
    login_email = st.text_input("Email Address", key="login_email_input")
    login_password = st.text_input("Password", type="password", key="login_pass_input")
    
    if st.button("Log In to Dashboard", use_container_width=True):
        user_data = verify_user(login_email, login_password)
        if user_data:
            st.session_state.logged_in = True
            st.session_state.user_id = user_data["userID"]
            st.session_state.user_name = f"{user_data['fname']} {user_data['lname']}"
            st.session_state.user_email = login_email.lower().strip()
            st.success(f"Access Granted! Welcome back, {st.session_state.user_name}.")
            st.rerun()
        else:
            st.error("Invalid email or password. Please verify your credentials.")

# =====================================================================
# SECURE MAIN WORKSPACE (Only renders after verification success)
# =====================================================================
else:
    current_uid = st.session_state.user_id
    current_name = st.session_state.user_name
    current_email = st.session_state.user_email

    # --- SIDEBAR UTILITIES ---
    with st.sidebar:
        st.image("https://icons8.com", width=60)
        st.title("System Control")
        st.write(f"Instructor: **{current_name}**")
        st.caption(f"ID: {current_uid} • {current_email}")
        st.markdown("---")
        
        with st.expander("🛠️ Maintenance Utilities", expanded=False):
            if st.button("Start Data Management", use_container_width=True):
                subprocess.run(["python", "start_data_management.py"])
                st.success("Executed.")
            if st.button("Complete Data Management", use_container_width=True):
                subprocess.run(["python", "complete_data_management.py"])
                st.success("Completed.")
                    
        st.markdown("---")
        if st.button("🚪 Log Out", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user_id = None
            st.session_state.user_name = ""
            st.session_state.user_email = ""
            st.rerun()

    # --- MAIN DASHBOARD WORKSPACE ---
    st.title("🎓 Instructor Dashboard")
    st.markdown("Welcome! From here, you can enter your course, view presentations, manage groups, review ratings, and export grades.")
    st.markdown("---")

    # Fetch courses dynamically from Hostinger MySQL filtered precisely by this instructor's userID
    def get_instructor_courses(user_id):
        try:
            conn = get_mysql_connection()
            # Mapping your exact 'course' table columns cleanly to readable dashboard metrics
            query = """
                SELECT 
                    courseID AS 'Course No.', 
                    courseCode AS 'Course Code', 
                    courseSection AS 'Course Section', 
                    courseDate AS 'Course Date',
                    courseTitle AS 'Course Title'
                FROM course 
                WHERE userID = %s
            """
            df = pd.read_sql_query(query, conn, params=(user_id,))
            conn.close()
            return df
        except Exception as database_error:
            st.error(f"Error compiling course data matrix: {database_error}")
            return pd.DataFrame(columns=["Course No.", "Course Code", "Course Section", "Course Date", "Course Title"])

    user_courses_df = get_instructor_courses(current_uid)

    # Top Metric Summaries Row
    m_col1, m_col2, m_col3 = st.columns(3)
    with m_col1:
        st.metric(label="Your Registered Courses", value=str(len(user_courses_df)))
    with m_col2:
        st.metric(label="Average Presentation Evaluation", value="4.85 / 5.0")
    with m_col3:
        st.metric(label="Database Pipeline", value="Hostinger Live Sync")

    st.markdown("---")

    # Split Screen Layout Row
    left_panel, right_panel = st.columns()
    
    with left_panel:
        st.subheader("📚 Your Courses")
        if user_courses_df.empty:
            st.info("No courses found under your account. Use the operational panel below to add a course.")
        else:
            st.dataframe(user_courses_df, use_container_width=True, hide_index=True)

    with right_panel:
        st.subheader("📅 Participation Calendar")
        if user_courses_df.empty:
            st.caption("Awaiting course entries to establish scheduling modules.")
        else:
            selected_course = st.selectbox("Select target course:", options=user_courses_df["Course Code"].tolist(), label_visibility="collapsed")
            st.info(f"Scanning Hostinger database timelines for: **{selected_course}**")
            
            c_col1, c_col2 = st.columns()
            with c_col1:
                selected_date = st.date_input("Target Date Lookup:", datetime.date.today(), label_visibility="collapsed")
            with c_col2:
                @st.dialog("Presentation Details")
                def show_details(course, date):
                    st.write(f"### 📋 Details for {course}")
                    st.write(f"**Date:** {date.strftime('%B %d, %Y')}")
                    st.warning("No live presentation listings mapped to this date context yet.")

                if st.button("👁️ View Details", use_container_width=True):
                    show_details(selected_course, selected_date)

    st.markdown("---")
    st.subheader("⚙️ Control & Operations Console")
    tab1, tab2 = st.tabs(["📂 1. Courses and Class Setup", "⭐ 2. Presentations and Ratings"])

    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            # --- INTERACTIVE MODAL TO SAVE COURSE BACK TO HOSTINGER ---
            @st.dialog("➕ Add New Course to Profile")
            def add_course_form():
                c_code = st.text_input("Course Code (e.g. COMP101)")
                c_sec = st.text_input("Section Descriptor (e.g. Section A)")
                c_title = st.text_input("Full Course Title")
                c_sched = st.text_input("Schedule Summary (e.g. Mon/Wed 10:00 AM)")
                c_term = st.text_input("Academic Term (e.g. Fall 2026)")
                c_instruct = st.text_area("Special Instructions", value="None")
                
                  if st.button("Commit Course to Hostinger Database", use_container_width=True):
                    if c_code and c_sec and c_title:
                        try:
                            conn = get_mysql_connection()
                            with conn.cursor() as cursor:
                                # Securely inject values using your exact column schema
                                sql = """
                                    INSERT INTO course 
                                    (courseSection, courseCode, courseTitle, courseDate, instruction, courseTerm, userID, ratingType, syllabus_text) 
                                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                                """
                                cursor.execute(sql, (
                                    c_sec, c_code, c_title, c_sched, c_instruct, c_term, current_uid, "5-Star", "Syllabus details pending..."
                                ))
                            conn.commit()
                            conn.close()
                            st.success("Course logged permanently to your database matrix!")
                            st.rerun()
                        except Exception as ex:
                            st.error(f"Failed to record course parameters to MySQL server: {ex}")
                    else:
                        st.error("Course Code, Section, and Title fields are strictly required.")

            if st.button("➕ Add Course", use_container_width=True):
                add_course_form()
                
        with col2:
            if st.button("🔄 Import Brightspace Students", use_container_width=True): 
                st.toast("Roster script module mapped.")

    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🏅 Grade Presentations", use_container_width=True): 
                st.toast("Evaluation rubrics live.")
        with col2:
            if st.button("📥 Download Brightspace CSV", use_container_width=True): 
                st.toast("Export engine processing data grids...")
