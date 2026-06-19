import streamlit as st
import pymysql
import datetime
import pandas as pd

def get_mysql_connection():
    return pymysql.connect(
        host=st.secrets["mysql"]["host"],
        user=st.secrets["mysql"]["user"],
        password=st.secrets["mysql"]["password"],
        database=st.secrets["mysql"]["database"],
        port=st.secrets["mysql"].get("port", 3306),
        cursorclass=pymysql.cursors.DictCursor
    )

st.title("🎤 Schedule & Enter My Presentation Details")
st.write("Input your System Assigned Group ID to review available calendar tracks and claim your slot.")
st.markdown("---")

# 1. Verification Phase: Student types in their unique Group ID
input_group_id = st.number_input("Enter your Group ID *", min_value=1, step=1, key="pres_group_id_lookup")

if st.button("Fetch My Group & Course Details", width="stretch"):
    try:
        conn = get_mysql_connection()
        with conn.cursor() as cursor:
            # Join presentationgroup and course tables to identify the exact section automatically
            sql = """
                SELECT g.groupID, g.groupName, g.courseID, c.courseCode, c.courseSection 
                FROM presentationgroup g
                JOIN course c ON g.courseID = c.courseID
                WHERE g.groupID = %s
            """
            cursor.execute(sql, (int(input_group_id),))
            group_record = cursor.fetchone()
        conn.close()

        with conn.cursor() as cursor:
            # FIXED: Added c.courseTerm and c.courseDate parameters to the SELECT string
            sql = """
                SELECT g.groupID, g.groupName, g.courseID, c.courseCode, c.courseSection, c.courseTerm, c.courseDate 
                FROM presentationgroup g
                JOIN course c ON g.courseID = c.courseID
                WHERE g.groupID = %s
            """
            cursor.execute(sql, (int(input_group_id),))
            group_record = cursor.fetchone()
        conn.close()
        
        if not group_record:
            st.error(f"❌ Verification Failed: No registered group found matching ID '{input_group_id}'.")
            st.session_state["active_student_group_id"] = None
        else:
            # Convert numeric course codes into distinct semester labels
            TERM_LABELS = {"1": "Fall", "2": "Winter", "3": "Summer"}
            raw_term = str(group_record["courseTerm"])
            term_text = TERM_LABELS.get(raw_term, f"Term {raw_term}")
            
            # Safely grab the 4-digit academic year string
            year_text = "N/A"
            if group_record["courseDate"]:
                if isinstance(group_record["courseDate"], (datetime.date, datetime.datetime)):
                    year_text = str(group_record["courseDate"].year)
                else:
                    year_text = str(group_record["courseDate"]).split("-")[0]

            # Cache the highly descriptive unique identifier label into session state
            st.session_state["active_student_group_id"] = group_record["groupID"]
            st.session_state["active_student_group_name"] = group_record["groupName"]
            st.session_state["active_student_course_id"] = group_record["courseID"]
            st.session_state["active_student_course_label"] = f"{group_record['courseCode']} - Section {group_record['courseSection']} ({term_text} {year_text})"
            st.rerun()
    except Exception as e:
        st.error(f"Server lookup connection failure: {e}")

# 2. Workspace Phase: Triggers only after group validation is cached in memory safely
if "active_student_group_id" in st.session_state and st.session_state["active_student_group_id"] == input_group_id:
    g_id = st.session_state["active_student_group_id"]
    g_name = st.session_state["active_student_group_name"]
    c_id = st.session_state["active_student_course_id"]
    c_label = st.session_state["active_student_course_label"]
    
    with st.container(border=True):
        st.success(f"🟢 Verified: Team **'{g_name}'** logged into course track: `{c_label}`")
        
        # Pull only open, unclaimed presentation slots assigned to this specific courseID
        def fetch_open_dates(course_id):
            try:
                conn = get_mysql_connection()
                with conn.cursor() as cursor:
                    # Finds presentationdate tracks where no groupID has been recorded yet
                    sql = """
                        SELECT pres_dateID, presDate 
                        FROM presentationdate 
                        WHERE courseID = %s AND (groupID IS NULL OR groupID = 0)
                        ORDER BY presDate ASC
                    """
                    cursor.execute(sql, (int(course_id),))
                    slots = cursor.fetchall()
                conn.close()
                return slots
            except Exception:
                return []

        open_slots_list = fetch_open_dates(c_id)
        
        if not open_slots_list:
            st.warning("⚠️ Scheduling Restricted: There are currently no open or available presentation slots left for this course track.")
        else:
            # Map available dates cleanly into a readable dropdown text string array selection format
            slot_options = {f"{s['presDate'].strftime('%A, %B %d, %Y')} - (ID: {s['pres_dateID']})": s['pres_dateID'] for s in open_slots_list}
            
            selected_slot_label = st.selectbox("Choose an Available Calendar Presentation Slot *", options=list(slot_options.keys()))
            target_date_id = slot_options[selected_slot_label]
            
            with st.form("student_booking_form"):
                st.markdown("##### 📝 Topic Scope Declaration")
                topic_title = st.text_input("Presentation Topic / Title Name *", placeholder="e.g., Implementing LLMs via Streamlit Frameworks")
                topic_abstract = st.text_area("Provide a Short Abstract / Overview summary", placeholder="Provide a brief explanation of your topic scope here...")
                
                submit_booking = st.form_submit_button("Lock in Presentation Slot & Topic Parameters", width="stretch")
                
            if submit_booking:
                if not topic_title:
                    st.error("You must fill out your Presentation Topic Title to secure your reservation.")
                else:
                    try:
                        conn = get_mysql_connection()
                        with conn.cursor() as cursor:
                            # Update statement mapping your database schema fields: groupID, dateTaken
                            # Assumes topics may be written to additional custom columns or parsed parameters if your schema permits
                            sql_claim = """
                                UPDATE presentationdate 
                                SET groupID = %s, dateTaken = %s
                                WHERE pres_dateID = %s
                            """
                            cursor.execute(sql_claim, (int(g_id), datetime.datetime.now(), int(target_date_id)))
                        conn.commit()
                        conn.close()
                        
                        # Clear tracking state memory on completion to refresh lists smoothly
                        st.session_state["active_student_group_id"] = None
                        st.success("🎉 Presentation confirmed! Your presentation date slot is permanently locked to your group.")
                        st.balloons()
                    except Exception as tx_err:
                        st.error(f"Failed to submit calendar reservation parameters: {tx_err}")
