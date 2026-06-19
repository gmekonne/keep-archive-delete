import streamlit as st
import pymysql

# Dictionary lookups inherited from main module state
TERM_LABELS = {"1": "Fall", "2": "Winter", "3": "Summer"}

def get_mysql_connection():
    return pymysql.connect(
        host=st.secrets["mysql"]["host"],
        user=st.secrets["mysql"]["user"],
        password=st.secrets["mysql"]["password"],
        database=st.secrets["mysql"]["database"],
        port=st.secrets["mysql"].get("port", 3306),
        cursorclass=pymysql.cursors.DictCursor
    )

cached_meta = st.session_state["cached_group_meta"]
mod_group_id = st.session_state["target_mod_group_id"]

with st.container(border=True):
    st.info(f"✏️ Modifying Parameters for Group ID: **{mod_group_id}**")
    up_g_name = st.text_input("Group Name", value=cached_meta["groupName"], key="up_g_name")
    up_g_email = st.text_input("Contact Email Address", value=cached_meta["email_address"], key="up_g_email")
    up_g_students = st.text_area("Roster Names (one per line)", placeholder="John Smith", height=120, key="up_students_text")
    
    if st.button("Commit Group Modifications", width="stretch", key="btn_save_mod_group"):
        if not up_g_name or not up_g_email or not up_g_students:
            st.error("All fields are required.")
        else:
            try:
                conn = get_mysql_connection()
                with conn.cursor() as cursor:
                    cursor.execute("UPDATE presentationgroup SET groupName = %s, email_address = %s WHERE groupID = %s", (up_g_name.strip(), up_g_email.strip(), int(mod_group_id)))
                    cursor.execute("DELETE FROM student WHERE groupID = %s", (int(mod_group_id),))
                    
                    student_sql = "INSERT INTO student (studentName, FirstName, LastName, groupID, courseID) VALUES (%s, %s, %s, %s, %s)"
                    raw_lines = up_g_students.split("\n")
                    for line in raw_lines:
                        clean_full_name = line.strip()
                        if clean_full_name:
                            name_parts = clean_full_name.split(" ", 1)
                            f_name = name_parts[0].strip() if len(name_parts) > 0 else ""
                            l_name = name_parts[1].strip() if len(name_parts) > 1 else ""
                            cursor.execute(student_sql, (clean_full_name, f_name, l_name, int(mod_group_id), int(cached_meta["courseID"])))
                conn.commit()
                conn.close()
                st.session_state["target_mod_group_id"] = None
                st.session_state["cached_group_meta"] = None
                st.success("Group modifications applied successfully!")
                st.rerun()
            except Exception as ex:
                st.error(f"Failed to record modifications: {ex}")
