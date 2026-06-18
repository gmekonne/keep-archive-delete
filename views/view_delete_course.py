import streamlit as st
import pymysql
import datetime

current_uid = st.session_state.user_id

def get_mysql_connection():
    return pymysql.connect(
        host=st.secrets["mysql"]["host"],
        user=st.secrets["mysql"]["user"],
        password=st.secrets["mysql"]["password"],
        database=st.secrets["mysql"]["database"],
        port=st.secrets["mysql"].get("port", 3306),
        cursorclass=pymysql.cursors.DictCursor
    )

st.title("🗂️ Course Catalog Management")
st.write("Modify parameters, overwrite presentation schedules, or remove active tracks.")
st.markdown("---")

TERM_LABELS = {"1": "Fall", "2": "Winter", "3": "Summer"}

def fetch_catalog(uid):
    try:
        conn = get_mysql_connection()
        with conn.cursor() as cursor:
            sql = "SELECT courseID, courseCode, courseSection, courseTitle, courseDate, courseTerm, syllabus_text, instruction FROM course WHERE userID = %s"
            cursor.execute(sql, (int(uid),))
            records = cursor.fetchall()
        conn.close()
        return records
    except Exception as e:
        st.error(f"Failed to fetch catalog: {e}")
        return []

catalog_list = fetch_catalog(current_uid)

if not catalog_list:
    st.info("You do not have any registered courses to administer.")
else:
    h_col1, h_col2, h_col3, h_col4, h_col5, h_col6 = st.columns(6)
    with h_col1: st.markdown("**Course Code**")
    with h_col2: st.markdown("**Section**")
    with h_col3: st.markdown("**Term**")
    with h_col4: st.markdown("**Year**")
    with h_col5: st.markdown("**Course Title**")
    with h_col6: st.markdown("**Actions**")
    st.markdown("---")

    if "current_edit_course_id" not in st.session_state:
        st.session_state.current_edit_course_id = None

    for course in catalog_list:
        c_id = course["courseID"]
        c_code = course["courseCode"]
        c_sec = course["courseSection"]
        c_title = course["courseTitle"]
        c_term_raw = str(course["courseTerm"])
        c_term_text = TERM_LABELS.get(c_term_raw, f"Term {c_term_raw}")
        
        c_year_text = "N/A"
        if course["courseDate"]:
            if isinstance(course["courseDate"], (datetime.date, datetime.datetime)):
                c_year_text = str(course["courseDate"].year)
            else:
                c_year_text = str(course["courseDate"]).split("-")[0]
        
        row_id_suffix = f"_{c_id}"
        
        row_col1, row_col2, row_col3, row_col4, row_col5, row_col6 = st.columns(6)
        with row_col1: st.write(c_code)
        with row_col2: st.write(c_sec)
        with row_col3: st.write(c_term_text)
        with row_col4: st.write(c_year_text)
        with row_col5: st.write(c_title)
        with row_col6:
            act_col1, act_col2 = st.columns(2)
            with act_col1:
                # FIXED: Removed st.rerun() so clicking does not drop the parent pop-up window
                if st.button("✏️", key=f"edit{row_id_suffix}", width="stretch"):
                    st.session_state.current_edit_course_id = None if st.session_state.current_edit_course_id == c_id else c_id
            with act_col2:
                if st.button("🗑️", key=f"del{row_id_suffix}", width="stretch"):
                    try:
                        conn = get_mysql_connection()
                        with conn.cursor() as cursor:
                            cursor.execute("DELETE FROM presentationdate WHERE courseID = %s", (int(c_id),))
                            cursor.execute("DELETE FROM course WHERE courseID = %s", (int(c_id),))
                        conn.commit()
                        conn.close()
                        st.toast(f"💥 Course '{c_code}' successfully removed.")
                        st.rerun()
                    except Exception as err:
                        st.error(f"Deletion failed: {err}")
        if st.session_state.current_edit_course_id == c_id:
            with st.container(border=True):
                st.info(f"✏️ Editing Parameters and Presentation Calendar Slots for: **{c_code}**")
                
                up_code = st.text_input("Course Code / Name *", value=c_code, key=f"inp_code{row_id_suffix}")
                up_title = st.text_input("Full Course Title *", value=c_title, key=f"inp_title{row_id_suffix}")
                up_sec = st.text_input("Class Section *", value=c_sec, key=f"inp_sec{row_id_suffix}")
                
                term_keys = ["1", "2", "3"]
                default_idx = term_keys.index(c_term_raw) if c_term_raw in term_keys else 0
                up_term = st.selectbox("Course Term", options=term_keys, index=default_idx, format_func=lambda x: TERM_LABELS.get(x, x), key=f"inp_term{row_id_suffix}")
                
                up_syllabus = st.text_area("Syllabus Guidelines", value=course.get("syllabus_text", "None"), height=80, key=f"inp_syll{row_id_suffix}")
                up_instruct = st.text_area("Presentation Guidelines", value=course.get("instruction", "None"), height=80, key=f"inp_inst{row_id_suffix}")
                
                st.markdown("##### 📅 Overwrite Semester Presentation Schedule")
                today = datetime.date.today()
                semester_days = [today + datetime.timedelta(days=x) for x in range(120)]
                calendar_options = [d.strftime("%Y-%m-%d (%A)") for d in semester_days]
                
                up_date_strings = st.multiselect(
                    "Highlight new presentation days for this semester track:",
                    options=calendar_options,
                    key=f"inp_multi_dates{row_id_suffix}"
                )
                
                up_num_pres = st.selectbox(
                    "Number of Presentations per Day for New Dates", 
                    options=[i for i in range(1, 11)], 
                    index=0,
                    key=f"inp_pres_day{row_id_suffix}"
                )
                
                e_col1, e_col2 = st.columns(2)
                with e_col1:
                    if st.button("Save Updates", key=f"btn_save{row_id_suffix}", width="stretch"):
                        try:
                            conn = get_mysql_connection()
                            current_ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            
                            with conn.cursor() as cursor:
                                sql_update_course = """
                                    UPDATE course 
                                    SET courseCode = %s, courseTitle = %s, courseSection = %s, courseTerm = %s, syllabus_text = %s, instruction = %s 
                                    WHERE courseID = %s
                                """
                                cursor.execute(sql_update_course, (up_code.strip(), up_title.strip(), up_sec.strip(), up_term, up_syllabus.strip(), up_instruct.strip(), int(c_id)))
                                
                                if up_date_strings:
                                    cursor.execute("DELETE FROM presentationdate WHERE courseID = %s", (int(c_id),))
                                    sql_insert_pres_date = """
                                        INSERT INTO presentationdate 
                                        (presDate, date_entered, courseID, courseSection, termID, userID) 
                                        VALUES (%s, %s, %s, %s, %s, %s)
                                    """
                                    for date_str in up_date_strings:
                                        raw_date_iso = date_str.split(" ")[0]
                                        for _ in range(int(up_num_pres)):
                                            cursor.execute(sql_insert_pres_date, (
                                                raw_date_iso, current_ts, int(c_id), up_sec.strip(), int(up_term), int(current_uid)
                                            ))
                                            
                            conn.commit()
                            conn.close()
                            st.session_state.current_edit_course_id = None
                            st.toast("Course details and schedule updated successfully!")
                            st.rerun()
                        except Exception as update_err:
                            st.error(f"Failed to update table matrices: {update_err}")
                with e_col2:
                    # FIXED: Removed st.rerun() from cancel to stop the window from shutting down unexpectedly
                    if st.button("Cancel Changes", key=f"btn_cancel{row_id_suffix}", width="stretch"):
                        st.session_state.current_edit_course_id = None
        st.markdown("---")
