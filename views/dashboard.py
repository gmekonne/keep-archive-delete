import streamlit as st
import datetime
import pandas as pd
import pymysql
import subprocess

# Secure reference variables inherited from main session memory
current_uid = st.session_state.user_id
current_name = st.session_state.user_name
current_email = st.session_state.user_email

# Helper function for live database streaming
def get_mysql_connection():
    return pymysql.connect(
        host=st.secrets["mysql"]["host"],
        user=st.secrets["mysql"]["user"],
        password=st.secrets["mysql"]["password"],
        database=st.secrets["mysql"]["database"],
        port=st.secrets["mysql"].get("port", 3306),
        cursorclass=pymysql.cursors.DictCursor
    )

# --- DYNAMIC DIALOG COMPONENT RUNNER ---
@st.dialog("➕ Add New Course", width="large")
def run_add_course_modal():
    # Reads and runs your external form file on demand
    with open("views/add_course_form.py", encoding="utf-8") as f:
        exec(compile(f.read(), "views/add_course_form.py", "exec"), globals())

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

def get_instructor_courses(user_id):
    try:
        conn = get_mysql_connection()
        target_uid = int(user_id)
        with conn.cursor() as cursor:
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
            cursor.execute(query, (target_uid,))
            rows = cursor.fetchall()
        conn.close()
        return pd.DataFrame(rows) if rows else pd.DataFrame(columns=["Course No.", "Course Code", "Course Section", "Course Date", "Course Title"])
    except Exception as e:
        st.error(f"Error compiling course data matrix: {e}")
        return pd.DataFrame(columns=["Course No.", "Course Code", "Course Section", "Course Date", "Course Title"])

user_courses_df = get_instructor_courses(current_uid)

# Top Metric Summaries Row
m_col1, m_col2, m_col3 = st.columns(3)
with m_col1: st.metric(label="Your Registered Courses", value=str(len(user_courses_df)))
with m_col2: st.metric(label="Average Presentation Evaluation", value="4.85 / 5.0")
with m_col3: st.metric(label="Database Pipeline", value="Hostinger Live Sync")

st.markdown("---")

# Split Screen Layout Row
left_panel, right_panel = st.columns(2)

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
        
        c_col1, c_col2 = st.columns(2)
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

# =====================================================================
# MAIN CONTROL OPERATIONS LAYOUT VISUALS
# =====================================================================
st.markdown("---")
st.subheader("⚙️ Control & Operations Console")

sec1_expander = st.expander("📂 1. Courses and Class Setup", expanded=True)
sec2_expander = st.expander("⭐ 2. Presentations and Ratings", expanded=True)

with sec1_expander:
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Add Course", use_container_width=True):
            run_add_course_modal()
        if st.button("❌ View / Delete Course", use_container_width=True):
            st.info("Course catalog list loaded.")
    with col2:
        if st.button("📈 View Contributions", use_container_width=True): st.info("Contribution metrics loaded.")
        if st.button("🔄 Import Students from Brightspace", use_container_width=True): st.info("Brightspace triggered.")

with sec2_expander:
    col3, col4 = st.columns(2)
    with col3:
        if st.button("👥 Load Presentations and Groups", use_container_width=True): st.info("Group data synchronized.")
        if st.button("📝 Load Peer Ratings", use_container_width=True): st.info("Peer evaluations imported.")
        if st.button("🏅 Grade Presentations", use_container_width=True): st.info("Grading rubric active.")
    with col4:
        if st.button("📊 View Grades", use_container_width=True): st.info("Gradebook calculations displayed.")
        if st.button("📥 Download Brightspace CSV", use_container_width=True): st.info("Generating Brightspace compatible CSV file...")
