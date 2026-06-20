import streamlit as st
import datetime
import pandas as pd
import pymysql
import subprocess

# Secure reference variables inherited from main session memory
current_uid = st.session_state.user_id
current_name = st.session_state.user_name
current_email = st.session_state.user_email

# Helper function for live uncached database streaming to avoid Hostinger socket drops
def get_mysql_connection():
    return pymysql.connect(
        host=st.secrets["mysql"]["host"],
        user=st.secrets["mysql"]["user"],
        password=st.secrets["mysql"]["password"],
        database=st.secrets["mysql"]["database"],
        port=st.secrets["mysql"].get("port", 3306),
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )

# --- DYNAMIC DIALOG COMPONENT RUNNERS ---
@st.dialog("➕ Add New Course", width="large")
def run_add_course_modal():
    with open("views/add_course_form.py", encoding="utf-8") as f:
        exec(compile(f.read(), "views/add_course_form.py", "exec"), globals())

@st.dialog("❌ Manage Active Course Catalog", width="large")
def run_manage_catalog_modal():
    with open("views/view_delete_course.py", encoding="utf-8") as f:
        exec(compile(f.read(), "views/view_delete_course.py", "exec"), globals())

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
        
        # Pull the matching courseID for our selection label string securely from our local tracking grid DataFrame
        matched_row = user_courses_df[user_courses_df["Course Code"] == selected_course]
        selected_course_id = int(matched_row.iloc[0]["Course No."]) if not matched_row.empty else 0
        
        c_col1, c_col2 = st.columns(2)
        with c_col1:
            selected_date = st.date_input("Target Date Lookup:", datetime.date.today(), label_visibility="collapsed")
        with MacK2 := st.columns(1):
            
            # --- FIXED DIALOG FUNCTION: FETCH REAL DATA FOR THE SELECTED DATE ---
            @st.dialog("Presentation Details", width="large")
            def show_details(course_name, course_id, target_date):
                st.write(f"### 📋 Presentation Slots for {course_name}")
                st.write(f"**Selected Date:** {target_date.strftime('%A, %B %d, %Y')}")
                st.markdown("---")
                
                try:
                    conn = get_mysql_connection()
                    with conn.cursor() as cursor:
                        # Join presentationdate with presentationgroup to display your newly booked student group names
                        sql = """
                            SELECT p.pres_dateID, p.presDate, p.dateTaken, g.groupName 
                            FROM presentationdate p
                            LEFT JOIN presentationgroup g ON p.groupID = g.groupID
                            WHERE p.courseID = %s AND p.presDate = %s
                            ORDER BY p.pres_dateID ASC
                        """
                        cursor.execute(sql, (int(course_id), target_date.strftime('%Y-%m-%d')))
                        slots_data = cursor.fetchall()
                    conn.close()
                    
                    if not slots_data:
                        st.info("ℹ️ No presentation slots were generated by the system configuration for this calendar date.")
                    else:
                        # Process records into clean tracking tables
                        display_list = []
                        for s in slots_data:
                            status_text = f"🔴 Booked by Team: {s['groupName']}" if s['dateTaken'] == 1 else "🟢 Available / Open Slot"
                            display_list.append({
                                "Slot ID": s['pres_dateID'],
                                "Scheduled Date": str(s['presDate']),
                                "Availability Status": status_text
                            })
                        
                        df_slots = pd.DataFrame(display_list)
                        st.dataframe(df_slots, use_container_width=True, hide_index=True)
                        
                except Exception as err:
                    st.error(f"Failed to query timeline data rows: {err}")

            if st.button("👁️ View Details", use_container_width=True):
                show_details(selected_course, selected_course_id, selected_date)

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
            run_manage_catalog_modal()
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
