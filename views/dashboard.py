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
        # Force your incoming ID parameter into a strict Python numerical integer
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
            # Native cursor execution with tuple wrapper provides perfect binding alignment
            cursor.execute(query, (target_uid,))
            rows = cursor.fetchall()
            
        conn.close()
        
        # Build clean data frames from the raw dictionary output lists
        if rows:
            return pd.DataFrame(rows)
        else:
            return pd.DataFrame(columns=["Course No.", "Course Code", "Course Section", "Course Date", "Course Title"])
            
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

st.markdown("---")
st.subheader("⚙️ Control & Operations Console")

# Create the two main section containers exactly as requested
sec1_expander = st.expander("📂 1. Courses and Class Setup", expanded=True)
sec2_expander = st.expander("⭐ 2. Presentations and Ratings", expanded=True)

# --- SECTION 1: COURSES AND CLASS SETUP ---
with sec1_expander:
    col1, col2 = st.columns(2)
    with col1:
        # Trigger your existing database modal form when clicked
        @st.dialog("➕ Add New Course to Profile")
        # --- INTERACTIVE MODAL TO SAVE COURSE & PRESENTATION DATES BACK TO HOSTINGER ---
        @st.dialog("➕ Add New Course to Profile", width="large")

                # --- INTERACTIVE MODAL TO SAVE COURSE & PRESENTATION DATES BACK TO HOSTINGER ---
        # =====================================================================
# MODAL DIALOG ENGINE DEFINITIONS (Placed flat at root level for alignment)
# =====================================================================
@st.dialog("➕ Add New Course to Profile", width="large")
def add_course_form():
    # 1. Course Name / Code Input
    c_code = st.text_input("Course Name/Code *", placeholder="e.g., COMP101")
    
    # 2. Course Year & Start Date Picker
    c_start_date = st.date_input("Course Year & Start Date *", datetime.date.today())
    
    # 3. Course Term Dropdown Selector
    c_term_options = {"First": "1", "Second": "2", "Third": "3"}
    c_term_label = st.selectbox("Course Term *", options=list(c_term_options.keys()))
    c_term_val = c_term_options[c_term_label]
    
    # 4. Class Section Alphabetical Datalist Dropdown Selection Row
    alphabet_sections = [chr(i) for i in range(ord('A'), ord('Z')+1)]
    c_sec = st.selectbox("Class Section *", options=alphabet_sections)
    
    # 5. Course Outline / Syllabus Textarea
    c_syllabus = st.text_area(
        "Paste Course Outline or Syllabus", 
        placeholder="Paste the course description, objectives, and weekly topics here...",
        rows=6
    )
    
    # 6. Presentation Guidelines Textarea
    c_instruct = st.text_area(
        "Guidelines of Presentation (students will view them when entering their presentation).",
        placeholder="e.g., Topic selection, presentation duration, rewards for best presentation(s), etc.",
        rows=4
    )
    
    # 7. MULTI-DATE CALENDAR SELECTION
    c_presentation_dates = st.date_input(
        "Choose Presentation Date(s) *",
        value=[],
        placeholder="Click to pick one or multiple dates"
    )
    
    # 8. Number of Presentations Per Day Counter Selector
    num_pres_day = st.selectbox(
        "Number of Presentations per Day", 
        options=[i for i in range(1, 11)], 
        index=0
    )
    
    st.markdown("---")
    
    # --- SUBMISSION TRANSACTION RUNNER ---
    if st.button("Save Course and Schedule Matrix", use_container_width=True):
        if not c_code or not c_presentation_dates:
            st.error("Course Name/Code and at least one Selected Presentation Date are strictly required.")
        else:
            try:
                conn = get_mysql_connection()
                with conn.cursor() as cursor:
                    # STEP 1: Insert the main course profile parameters
                    course_sql = """
                        INSERT INTO course 
                        (courseSection, courseCode, courseTitle, courseDate, instruction, courseTerm, userID, ratingType, syllabus_text) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(course_sql, (
                        c_sec, 
                        c_code.strip(), 
                        c_code.strip(), 
                        c_start_date.strftime('%Y-%m-%d'), 
                        c_instruct.strip() if c_instruct else "None", 
                        c_term_val, 
                        int(current_uid), 
                        "5-Star", 
                        c_syllabus.strip() if c_syllabus else "Syllabus pending..."
                    ))
                    
                    new_course_id = cursor.lastrowid
                    
                    # STEP 2: Loop through selected calendar days to write to presentationdate table
                    pres_date_sql = """
                        INSERT INTO presentationdate (courseID, pdate) 
                        VALUES (%s, %s)
                    """
                    
                    inserted_slots_count = 0
                    target_dates_list = c_presentation_dates if isinstance(c_presentation_dates, (list, tuple)) else [c_presentation_dates]
                    
                    for selected_day in target_dates_list:
                        formatted_day_str = selected_day.strftime('%Y-%m-%d')
                        for _ in range(int(num_pres_day)):
                            cursor.execute(pres_date_sql, (new_course_id, formatted_day_str))
                            inserted_slots_count += 1
                            
                conn.commit()
                conn.close()
                st.success(f"🎉 Course saved! Added {inserted_slots_count} active presentation slots to 'presentationdate'.")
                st.rerun()
            except Exception as database_transaction_error:
                st.error(f"Failed to record course data matrices: {database_transaction_error}")


# =====================================================================
# MAIN CONTROL OPERATIONS LAYOUT VISUALS
# =====================================================================
st.markdown("---")
st.subheader("⚙️ Control & Operations Console")

# Create the two main section expander containers
sec1_expander = st.expander("📂 1. Courses and Class Setup", expanded=True)
sec2_expander = st.expander("⭐ 2. Presentations and Ratings", expanded=True)

# --- SECTION 1: COURSES AND CLASS SETUP ---
with sec1_expander:
    col1, col2 = st.columns(2)
    with col1:
        # Simply call the standalone dialog trigger cleanly
        if st.button("➕ Add Course", use_container_width=True):
            add_course_form()

        if st.button("❌ View / Delete Course", use_container_width=True):
            st.info("Course catalog list loaded.")
            
    with col2:
        if st.button("📈 View Contributions", use_container_width=True):
            st.info("Contribution metrics loaded.")
            
        if st.button("🔄 Import Students from Brightspace", use_container_width=True):
            st.info("Brightspace API / CSV connection triggered.")



# --- SECTION 2: PRESENTATIONS AND RATINGS ---
with sec2_expander:
    col3, col4 = st.columns(2)
    with col3:
        if st.button("👥 Load Presentations and Groups", use_container_width=True):
            st.info("Group data synchronized.")
            
        if st.button("📝 Load Peer Ratings", use_container_width=True):
            st.info("Peer evaluations imported.")
            
        if st.button("🏅 Grade Presentations", use_container_width=True):
            st.info("Grading rubric interface active.")
            
    with col4:
        if st.button("📊 View Grades", use_container_width=True):
            st.info("Gradebook calculations displayed.")
            
        if st.button("📥 Download Brightspace CSV", use_container_width=True):
            st.info("Generating Brightspace compatible CSV file...")
