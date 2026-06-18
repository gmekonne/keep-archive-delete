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
st.write("Modify properties or remove active tracks assigned to your profile.")
st.markdown("---")

# Dictionary wrapper to convert numeric term IDs back to readable text labels
TERM_LABELS = {"1": "Fall", "2": "Winter", "3": "Summer"}

# --- DATABASE FETCH ENGINE ---
def fetch_catalog(uid):
    conn = get_mysql_connection()
    with conn.cursor() as cursor:
        sql = "SELECT courseID, courseCode, courseSection, courseTitle, courseDate, courseTerm, syllabus_text, instruction FROM course WHERE userID = %s"
        cursor.execute(sql, (int(uid),))
        records = cursor.fetchall()
    conn.close()
    return records

catalog_list = fetch_catalog(current_uid)

if not catalog_list:
    st.info("You do not have any registered courses to administer.")
else:
    # Build clean horizontal header tracking layout with 6 explicit column zones
    h_col1, h_col2, h_col3, h_col4, h_col5, h_col6 = st.columns(6)
    with h_col1: st.markdown("**Course Code**")
    with h_col2: st.markdown("**Section**")
    with h_col3: st.markdown("**Term**")
    with h_col4: st.markdown("**Year**")
    with h_col5: st.markdown("**Course Title**")
    with h_col6: st.markdown("**Actions**")
    st.markdown("---")

    # Initialize tracking key to remember which course is currently expanded for editing
    if "current_edit_course_id" not in st.session_state:
        st.session_state.current_edit_course_id = None

    # Loop through each course record row explicitly
    for course in catalog_list:
        c_id = course["courseID"]
        c_code = course["courseCode"]
        c_sec = course["courseSection"]
        c_title = course["courseTitle"]
        c_term_raw = str(course["courseTerm"])
        
        # 1. Translate numeric term ID to readable text
        c_term_text = TERM_LABELS.get(c_term_raw, f"Term {c_term_raw}")
        
        # 2. Extract the 4-digit Year string directly out of your courseDate column
        c_year_text = "N/A"
        if course["courseDate"]:
            if isinstance(course["courseDate"], (datetime.date, datetime.datetime)):
                c_year_text = str(course["courseDate"].year)
            else:
                c_year_text = str(course["courseDate"]).split("-")[0]
        
        row_id_suffix = f"_{c_id}"
        
        # Output the row grid layout
        row_col1, row_col2, row_col3, row_col4, row_col5, row_col6 = st.columns(6)
        with row_col1: st.write(c_code)
        with row_col2: st.write(c_sec)
        with row_col3: st.write(c_term_text)
        with row_col4: st.write(c_year_text)
        with row_col5: st.write(c_title)
        with row_col6:
            act_col1, act_col2 = st.columns(2)
            
            # --- 1. TOGGLE INLINE EDIT IN-MEMORY STATUS ---
            with act_col1:
                if st.button("✏️", key=f"edit{row_id_suffix}", help="Toggle Inline Modification Drawer", width="stretch"):
                    # Clicking edit toggles the drawer open/closed for that specific row
                    if st.session_state.current_edit_course_id == c_id:
                        st.session_state.current_edit_course_id = None
                    else:
                        st.session_state.current_edit_course_id = c_id
                    st.rerun()
            
            # --- 2. DELETE COURSE BUTTON ---
            with act_col2:
                if st.button("🗑️", key=f"del{row_id_suffix}", help="Permanently Remove Course", width="stretch"):
                    try:
                        conn = get_mysql_connection()
                        with conn.cursor() as cursor:
                            cursor.execute("DELETE FROM presentationdate WHERE courseID = %s", (int(c_id),))
                            cursor.execute("DELETE FROM course WHERE courseID = %s", (int(c_id),))
                        conn.commit()
                        conn.close()
                        st.toast(f"💥 Course '{c_code}' successfully removed from system databases.")
                        st.rerun()
                    except Exception as err:
                        st.error(f"Deletion failed: {err}")
        
        # --- FIXED INLINE EDIT DRAWER AREA (No Nested Dialog Exception Possible) ---
        if st.session_state.current_edit_course_id == c_id:
            with st.container(border=True):
                st.info(f"✏️ Editing Parameters for **{c_code}** ({c_term_text} {c_year_text})")
                
                # Preload existing field texts safely
                up_code = st.text_input("Course Code / Name *", value=c_code, key=f"inp_code{row_id_suffix}")
                up_title = st.text_input("Full Course Title *", value=c_title, key=f"inp_title{row_id_suffix}")
                up_sec = st.text_input("Class Section *", value=c_sec, key=f"inp_sec{row_id_suffix}")
                
                # Dynamic pick option dropdown safely finding current index alignment
                term_keys = ["1", "2", "3"]
                default_idx = term_keys.index(c_term_raw) if c_term_raw in term_keys else 0
                up_term = st.selectbox("Course Term", options=term_keys, index=default_idx, format_func=lambda x: TERM_LABELS.get(x, x), key=f"inp_term{row_id_suffix}")
                
                up_syllabus = st.text_area("Syllabus Guidelines", value=course.get("syllabus_text", "Syllabus details pending..."), height=100, key=f"inp_syll{row_id_suffix}")
                up_instruct = st.text_area("Presentation Guidelines", value=course.get("instruction", "None"), height=100, key=f"inp_inst{row_id_suffix}")
                
                e_col1, e_col2 = st.columns(2)
                with e_col1:
                    if st.button("Save Updates", key=f"btn_save{row_id_suffix}", width="stretch"):
                        try:
                            conn = get_mysql_connection()
                            with conn.cursor() as cursor:
                                sql = """
                                    UPDATE course 
                                    SET courseCode = %s, courseTitle = %s, courseSection = %s, courseTerm = %s, syllabus_text = %s, instruction = %s 
                                    WHERE courseID = %s
                                """
                                cursor.execute(sql, (up_code.strip(), up_title.strip(), up_sec.strip(), up_term, up_syllabus.strip(), up_instruct.strip(), int(c_id)))
                            conn.commit()
                            conn.close()
                            st.session_state.current_edit_course_id = None
                            st.success("Changes pushed directly to Hostinger server!")
                            st.rerun()
                        except Exception as update_err:
                            st.error(f"Failed to update table matrices: {update_err}")
                with e_col2:
                    if st.button("Cancel Changes", key=f"btn_cancel{row_id_suffix}", width="stretch"):
                        st.session_state.current_edit_course_id = None
                        st.rerun()
        
        st.markdown("---")
