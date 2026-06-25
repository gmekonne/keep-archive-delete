import streamlit as st
import pymysql
import datetime

def get_mysql_connection():
    """Establishes a real-time connection straight to Hostinger."""
    return pymysql.connect(
        host=st.secrets["mysql"]["host"],
        user=st.secrets["mysql"]["user"],
        password=st.secrets["mysql"]["password"],
        database=st.secrets["mysql"]["database"],
        port=st.secrets["mysql"].get("port", 3306),
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )

st.title("💡 Submit Classroom Engagement Contributions")
st.write("Share extra research concepts, helpful study resources, videos, or lesson summaries.")
st.markdown("---")

# 1. User-Friendly Identity Verification Block
input_gid = st.number_input("Enter your Group ID *", min_value=1, step=1, key="contrib_gid_lookup")

if st.button("Verify My Profile & Load Submission Form", use_container_width=True):
    try:
        conn = get_mysql_connection()
        with conn.cursor() as cursor:
            # Look up group directly to find attached course parameters safely
            cursor.execute("SELECT groupName, courseID FROM presentationgroup WHERE groupID = %s", (int(input_gid),))
            group_record = cursor.fetchone()
            
            if not group_record:
                st.error(f"❌ Verification Failed: Group ID '{input_gid}' is not currently registered in the system.")
                st.session_state["active_contrib_group_id"] = None
            else:
                # Find the corresponding instructor userID linked to that course ID
                cursor.execute("SELECT userID, courseCode, courseSection FROM course WHERE courseID = %s", (int(group_record["courseID"]),))
                course_record = cursor.fetchone()
                
                # --- NEW PIPELINE: Fetch all individual student roster members belonging to this groupID ---
                cursor.execute("SELECT stuID, studentName FROM student WHERE groupID = %s", (int(input_gid),))
                roster_rows = cursor.fetchall()
                
                if not course_record:
                    st.error("❌ Linkage Error: Your group points to a course record that no longer exists.")
                elif not roster_rows:
                    st.error(f"❌ Roster Error: Group '{group_record['groupName']}' has no individual students registered to it. Please create your student accounts first.")
                else:
                    # Cache layout markers into state memory to feed your fields automatically
                    st.session_state["active_contrib_group_id"] = int(input_gid)
                    st.session_state["active_contrib_group_name"] = group_record["groupName"]
                    st.session_state["active_contrib_course_id"] = int(group_record["courseID"])
                    st.session_state["active_contrib_instructor_id"] = int(course_record["userID"])
                    st.session_state["active_contrib_course_label"] = f"{course_record['courseCode']} (Section {course_record['courseSection']})"
                    
                    # Store a dictionary mapping student names to their true studentID numbers
                    st.session_state["active_contrib_roster_map"] = {r["studentName"]: r["stuID"] for r in roster_rows}
                    st.rerun()
        conn.close()
    except Exception as e:
        st.error(f"Server verification pipeline lookup failure: {e}")
# 2. Workspace Phase: Displays only after identity metrics are verified
if "active_contrib_group_id" in st.session_state and st.session_state["active_contrib_group_id"] == input_gid:
    g_id = st.session_state["active_contrib_group_id"]
    g_name = st.session_state["active_contrib_group_name"]
    c_id = st.session_state["active_contrib_course_id"]
    u_id = st.session_state["active_contrib_instructor_id"]
    c_label = st.session_state["active_contrib_course_label"]
    student_map = st.session_state.get("active_contrib_roster_map", {})
    
    with st.container(border=True):
        st.success(f"🟢 Authenticated: Team **'{g_name}'** linked to course track: `{c_label}`")
        
        # Pull types dynamically straight out of your database rows
        dropdown_type_options = []
        try:
            conn = get_mysql_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT contribType FROM contributionType ORDER BY contribTypeID ASC")
                types_data = cursor.fetchall()
                dropdown_type_options = [t["contribType"] for t in types_data] if types_data else ["Other"]
            conn.close()
        except Exception:
            dropdown_type_options = ["Idea/Insight", "Question", "Resource Link", "Video", "Other"]

        # Form Interface Element Render Rows
        with st.form("participation_submission_form", clear_on_submit=True):
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                # 🟢 NEW HIGHLIGHT: The student selects their individual name from the group roster map dictionary
                chosen_student_name = st.selectbox("Identify Contributor Name *", options=list(student_map.keys()))
                selected_student_id = student_map[chosen_student_name]
            with col_s2:
                selected_type = st.selectbox("Participation Type *", options=dropdown_type_options)
                
            col1, col2 = st.columns(2)
            with col1:
                chosen_date = st.date_input("Date (Optional)", datetime.date.today())
            with col2:
                contrib_tags = st.text_input("Tags / Week / Topic (Optional)", placeholder="e.g., Week 5, AI Ethics")
                
            contrib_title = st.text_input("Title *", placeholder="Short, clear title", max_chars=180)
            contrib_desc = st.text_area(
                "Description / Message *", 
                placeholder="2–6 sentences: what it is, why it matters, and how it relates to the course.",
                height=120
            )
            contrib_link = st.text_input("Link (Optional)", placeholder="https://...")
            
            save_submit = st.form_submit_button("💾 Save Contribution", width="stretch")
            
        if save_submit:
            if not contrib_title or not contrib_desc:
                st.error("All starred fields are required to process your participation entry.")
            elif selected_type in ["Resource Link", "Video"] and not contrib_link:
                st.error(f"⚠️ Validation Notice: A valid URL Link is strictly required when submitting a '{selected_type}' contribution type.")
            else:
                try:
                    conn = get_mysql_connection()
                    current_ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    formatted_date_str = chosen_date.strftime('%Y-%m-%d')
                    
                    with conn.cursor() as cursor:
                        # FIXED: Injects the true dynamic selected_student_id into the studentID column row reference
                        sql_insert = """
                            INSERT INTO contribution 
                            (courseID, groupID, studentID, userID, contributionType, title, description, grade, link, tags, contributionDate, created_at, ai_feedback, ai_score, ai_checked, visibleToClass) 
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """
                        cursor.execute(sql_insert, (
                            int(c_id),                  # courseID
                            int(g_id),                  # groupID
                            int(selected_student_id),   # studentID (Enforced exact contributor ID mapping)
                            int(u_id),                  # userID (instructor reference)
                            selected_type,              # contributionType text selector
                            contrib_title.strip(), 
                            contrib_desc.strip(),
                            None,                       # grade (Null value awaiting review)
                            contrib_link.strip() if contrib_link else "None", 
                            contrib_tags.strip() if contrib_tags else "General", 
                            formatted_date_str,         # contributionDate string
                            current_ts,                 # created_at timestamp
                            None,                       # ai_feedback placeholder
                            0,                          # ai_score
                            0,                          # ai_checked
                            1                           # visibleToClass
                        ))
                        
                    st.success(f"🎉 Success! Individual contribution by {chosen_student_name} for '{contrib_title}' has been permanently recorded to the ledger.")
                    st.balloons()
                except Exception as tx_err:
                    st.error(f"Failed to commit contribution parameters to database server: {tx_err}")
