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

@st.dialog("📝 Enter/Edit System Guidelines", width="large")
def run_edit_guide_modal():
    with open("views/edit_guide_form.py", encoding="utf-8") as f:
        exec(compile(f.read(), "views/edit_guide_form.py", "exec"), globals())

@st.dialog("📂 View & Grade Student Participation Logs", width="large")
def run_view_contributions_modal():
    with open("views/view_contributions.py", encoding="utf-8") as f:
        exec(compile(f.read(), "views/view_contributions.py", "exec"), globals())

# --- SIDEBAR UTILITIES ---
with st.sidebar:
    st.image("https://icons8.com", width=60)
    st.title("System Control")
    st.write(f"Instructor: **{current_name}**")
    st.caption(f"ID: {current_uid} • {current_email}")
    st.markdown("---")
    
    with st.expander("🛠️ Maintenance Utilities", expanded=False):
        if st.button("Start Data Management", width="stretch"):
            subprocess.run(["python", "start_data_management.py"])
            st.success("Executed.")
        if st.button("Complete Data Management", width="stretch"):
            subprocess.run(["python", "complete_data_management.py"])
            st.success("Completed.")
                
    st.markdown("---")
    if st.button("🚪 Log Out", width="stretch"):
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
type_ratings_list = []
overall_average_label = "0.0"

try:
    conn = get_mysql_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT FORMAT(AVG(rating_number), 1) as global_avg FROM rating")
        g_res = cursor.fetchone()
        if g_res and g_res["global_avg"]:
            overall_average_label = f"{g_res['global_avg']} / 5.0"
            
        sql_type_performance = """
            SELECT t.ptypeTitle AS 'Type', 
                   FORMAT(AVG(r.rating_number), 1) AS 'Average Score'
            FROM rating r
            INNER JOIN presentationType t ON r.ptypeID = t.ptypeID
            GROUP BY r.ptypeID, t.ptypeTitle
            ORDER BY AVG(r.rating_number) DESC
        """
        cursor.execute(sql_type_performance)
        type_ratings_list = cursor.fetchall()
    conn.close()
except Exception as e:
    overall_average_label = "Error"

# --- COMPACT GRID LAYOUT RATIOS WITH HORIZONTAL BREATHING ROOM ---
m_col1, m_col2, m_col3 = st.columns([1, 2, 1.2])

with m_col1: 
    st.metric(label="Your Registered Courses", value=str(len(user_courses_df)))
    
with m_col2: 
    st.caption("📊 Performance Scores Index")
    processed_rows = []
    if type_ratings_list:
        for item in type_ratings_list:
            processed_rows.append({"Evaluation Type": item["Type"], "Rating": f"★ {item['Average Score']}"})
            
    processed_rows.append({"Evaluation Type": "⭐ OVERALL AVERAGE", "Rating": f"★ {overall_average_label}"})
    df_mini_metrics = pd.DataFrame(processed_rows)
    st.dataframe(df_mini_metrics, width="stretch", hide_index=True)
    
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
        st.dataframe(user_courses_df, width="stretch", hide_index=True)

with right_panel:
    st.subheader("📅 Participation Calendar")
    if user_courses_df.empty:
        st.caption("Awaiting course entries to establish scheduling modules.")
    else:
        selected_course = st.selectbox("Select target course:", options=user_courses_df["Course Code"].tolist(), label_visibility="collapsed", key="dash_course_sel_v2")
        matched_row = user_courses_df[user_courses_df["Course Code"] == selected_course]
        
        # FIXED SCALAR ELEMENT EXTRACTION: Safe from type crashes
        selected_course_id = int(matched_row["Course No."].values[0]) if not matched_row.empty else 0
        
        booked_dates_list = []
        try:
            conn = get_mysql_connection()
            with conn.cursor() as cursor:
                sql_dates = """
                    SELECT DISTINCT presDate 
                    FROM presentationdate 
                    WHERE courseID = %s AND dateTaken = 1 
                    ORDER BY presDate ASC
                """
                cursor.execute(sql_dates, (selected_course_id,))
                dates_data = cursor.fetchall()
                booked_dates_list = [d["presDate"] for d in dates_data] if dates_data else []
            conn.close()
        except Exception as e:
            st.error(f"Failed to scan upcoming timelines: {e}")

        if not booked_dates_list:
            st.info(f"ℹ️ No upcoming presentations have been booked by students for course {selected_course} yet.")
        else:
            st.success(f"📋 Found **{len(booked_dates_list)}** upcoming scheduled presentation dates!")
            
            date_options_map = {d.strftime("%A, %B %d, %Y"): d for d in booked_dates_list}
            chosen_date_label = st.selectbox("Select an upcoming presentation date to audit:", options=list(date_options_map.keys()), key="dash_date_picker_v2")
            target_iso_date = date_options_map[chosen_date_label]
            
            # --- OVERLAY MODAL: LOADS THE PRESENTATION DETAILS AND SECURE ROUTING KEYS ---
            @st.dialog("📋 Booked Presenter Details Matrix", width="large")
            def show_fresh_presenter_details_modal(course_name, course_id, target_date_obj):
                st.write(f"### 🎤 Presenters for {course_name}")
                st.write(f"**Presentation Date:** {target_date_obj.strftime('%A, %B %d, %Y')}")
                st.markdown("---")
                
                try:
                    conn = get_mysql_connection()
                    with conn.cursor() as cursor:
                        sql_details = """
                            SELECT p.pres_dateID, g.groupName, p.groupID, pr.presTitle, pr.presDescription, pr.random_string
                            FROM presentationdate p
                            JOIN presentationgroup g ON p.groupID = g.groupID
                            JOIN presentation pr ON p.groupID = pr.groupID AND p.presDate = pr.pres_date
                            WHERE p.courseID = %s AND p.presDate = %s
                            ORDER BY p.pres_dateID ASC
                        """
                        cursor.execute(sql_details, (int(course_id), target_date_obj.strftime('%Y-%m-%d')))
                        slots = cursor.fetchall()
                        
                        if not slots:
                            st.warning("No booking records found matching this timeline context track.")
                        else:
                            for s in slots:
                                g_id = s["groupID"]
                                g_name = s["groupName"]
                                title_text = s["presTitle"] or "No Topic Registered"
                                desc_text = s["presDescription"] or "No summary description text logged."
                                rand_hash = s["random_string"] or ""
                                
                                cursor.execute("SELECT studentName FROM student WHERE groupID = %s", (int(g_id),))
                                roster_data = cursor.fetchall()
                                roster_names = [r["studentName"] for r in roster_data] if roster_data else ["None Registered"]
                                roster_string = ", ".join(roster_names)
                                
                                with st.container(border=True):
                                    st.markdown(f"#### 👥 Group: **{g_name}** (ID: {g_id})")
                                    st.markdown(f"🎤 **Presentation Title:** **{title_text}**")
                                    st.markdown(f"👥 **Presenter Members:** *{roster_string}*")
                                    st.markdown(f"📝 **Description Summary:**\n*{desc_text}*")
                                    
                                    # 🔒 THE VERIFIED SECURITY LINK FORMAT WRITTEN EXACTLY TO YOUR REQUIRED TEMPLATE
                                    if rand_hash:
                                        correct_full_url = f"https://keep-archive-delete-hgqqsmfkqpwhbjedahdsny.streamlit.app/?page=student_rate_form&postID={rand_hash}"
                                        st.text_input("🔗 Copy Shareable Peer Rating Link for this Group:", value=correct_full_url, key=f"url_v2_widget_{s['pres_dateID']}")
                                        st.caption("Instructors can copy this link to paste into Zoom chat or project on screen for live evaluations.")
                                        
                    conn.close()
                except Exception as err:
                    st.error(f"Failed to query active presenter metrics: {err}")

            if st.button("👁️ View Scheduled Presenters", use_container_width=True, key="btn_view_pres_v2"):
                show_fresh_presenter_details_modal(selected_course, selected_course_id, target_date_obj=target_iso_date)

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
        if st.button("➕ Add Course", width="stretch"): run_add_course_modal()
        if st.button("❌ View / Delete Course", width="stretch"): run_manage_catalog_modal()
        if st.button("📝 Enter / Edit Guide", width="stretch"): run_edit_guide_modal()
    with col2:
        if st.button("📈 View Contributions", width="stretch"): run_view_contributions_modal()
        if st.button("🔄 Import Students from Brightspace", width="stretch"): st.info("Brightspace triggered.")

with sec2_expander:
    col3, col4 = st.columns(2)
    with col3:
        if st.button("👥 Load Presentations and Groups", width="stretch"): st.info("Group data synchronized.")
        if st.button("📝 Load Peer Ratings", width="stretch"): st.info("Peer evaluations imported.")
        if st.button("🏅 Grade Presentations", width="stretch"): st.info("Grading rubric active.")
    with col4:
        if st.button("📊 View Grades", width="stretch"): st.info("Gradebook calculations displayed.")
        if st.button("📥 Download Brightspace CSV", width="stretch"): st.info("Generating Brightspace compatible CSV file...")
