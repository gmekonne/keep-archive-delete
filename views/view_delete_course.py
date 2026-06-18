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

# --- DATABASE FETCH ENGINE ---
def fetch_catalog(uid):
    conn = get_mysql_connection()
    with conn.cursor() as cursor:
        sql = "SELECT courseID, courseCode, courseSection, courseTitle FROM course WHERE userID = %s"
        cursor.execute(sql, (int(uid),))
        records = cursor.fetchall()
    conn.close()
    return records

catalog_list = fetch_catalog(current_uid)

if not catalog_list:
    st.info("You do not have any registered courses to administer.")
else:
    # Build clean horizontal header tracking indicators
    h_col1, h_col2, h_col3, h_col4 = st.columns([2, 2, 4, 3])
    with h_col1: st.markdown("**Course Code**")
    with h_col2: st.markdown("**Section**")
    with h_col3: st.markdown("**Course Title**")
    with h_col4: st.markdown("**Available Actions**")
    st.markdown("---")

    # Loop through each course record row explicitly
    for course in catalog_list:
        c_id = course["courseID"]
        c_code = course["courseCode"]
        c_sec = course["courseSection"]
        c_title = course["courseTitle"]
        
        # Unique tracking keys generated dynamically for each row button
        row_id_suffix = f"_{c_id}"
        
        row_col1, row_col2, row_col3, row_col4 = st.columns([2, 2, 4, 3])
        with row_col1: st.write(c_code)
        with row_col2: st.write(c_sec)
        with row_col3: st.write(c_title)
        with row_col4:
            act_col1, act_col2 = st.columns(2)
            
            # --- 1. EDIT COURSE BUTTON ---
            with act_col1:
                if st.button("✏️ Edit", key=f"edit{row_id_suffix}", width="stretch"):
                    st.session_state[f"active_edit_id"] = c_id
                    st.rerun()
            
            # --- 2. DELETE COURSE BUTTON ---
            with act_col2:
                if st.button("🗑️ Delete", key=f"del{row_id_suffix}", width="stretch"):
                    try:
                        conn = get_mysql_connection()
                        with conn.cursor() as cursor:
                            # Safely drop dependencies across presentation dates before deleting parent record
                            cursor.execute("DELETE FROM presentationdate WHERE courseID = %s", (int(c_id),))
                            cursor.execute("DELETE FROM course WHERE courseID = %s", (int(c_id),))
                        conn.commit()
                        conn.close()
                        st.toast(f"💥 Course '{c_code}' successfully removed from system databases.")
                        st.rerun()
                    except Exception as err:
                        st.error(f"Deletion failed: {err}")

# =====================================================================
# DYNAMIC EDIT INLINE MODAL POPUP
# =====================================================================
if f"active_edit_id" in st.session_state and st.session_state[f"active_edit_id"] is not None:
    edit_target_id = st.session_state[f"active_edit_id"]
    
    # Fetch details for the selected course
    conn = get_mysql_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM course WHERE courseID = %s", (int(edit_target_id),))
        course_details = cursor.fetchone()
    conn.close()
    
    if course_details:
        # Open an overlays configuration dialog automatically using an active fragment check
        @st.dialog("✏️ Modify Course Matrix Settings", width="large")
        def run_edit_dialog(details):
            # Pre-load current server database values cleanly into input fields
            up_code = st.text_input("Course Code / Name *", value=details["courseCode"])
            up_title = st.text_input("Full Course Title *", value=details["courseTitle"])
            up_sec = st.text_input("Class Section *", value=details["courseSection"])
            up_term = st.selectbox("Course Term", options=["1", "2", "3"], index=["1", "2", "3"].index(str(details["courseTerm"])))
            up_syllabus = st.text_area("Syllabus Guidelines", value=details["syllabus_text"], height=120)
            up_instruct = st.text_area("Presentation Guidelines", value=details["instruction"], height=100)
            
            e_col1, e_col2 = st.columns(2)
            with e_col1:
                if st.button("Save Updates", width="stretch"):
                    try:
                        conn = get_mysql_connection()
                        with conn.cursor() as cursor:
                            sql = """
                                UPDATE course 
                                SET courseCode = %s, courseTitle = %s, courseSection = %s, courseTerm = %s, syllabus_text = %s, instruction = %s 
                                WHERE courseID = %s
                            """
                            cursor.execute(sql, (up_code.strip(), up_title.strip(), up_sec.strip(), up_term, up_syllabus.strip(), up_instruct.strip(), int(edit_target_id)))
                        conn.commit()
                        conn.close()
                        st.session_state[f"active_edit_id"] = None
                        st.success("Changes pushed directly to Hostinger server successfully.")
                        st.rerun()
                    except Exception as update_err:
                        st.error(f"Failed to update table matrices: {update_err}")
            with e_col2:
                if st.button("Cancel Changes", width="stretch"):
                    st.session_state[f"active_edit_id"] = None
                    st.rerun()
                    
        run_edit_dialog(course_details)
