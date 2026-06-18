import streamlit as st
import pymysql
import datetime

def get_mysql_connection():
    return pymysql.connect(
        host=st.secrets["mysql"]["host"],
        user=st.secrets["mysql"]["user"],
        password=st.secrets["mysql"]["password"],
        database=st.secrets["mysql"]["database"],
        port=st.secrets["mysql"].get("port", 3306),
        cursorclass=pymysql.cursors.DictCursor
    )

st.title("👥 Student Registration & Group Portal")
st.write("Register a new presentation team or update an existing team roster.")
st.markdown("---")

# --- GLOBAL DATABASE FETCH HELPER ---
def fetch_available_courses():
    try:
        conn = get_mysql_connection()
        with conn.cursor() as cursor:
            # Query active courses to map IDs to friendly visual text dropdowns
            cursor.execute("SELECT courseID, courseCode, courseSection FROM course")
            courses = cursor.fetchall()
        conn.close()
        return courses
    except Exception as e:
        st.error(f"Failed to fetch classroom listings: {e}")
        return []

all_courses = fetch_available_courses()

# Organize the form workspace into separate operational tabs
tab_create, tab_modify = st.tabs(["➕ Register New Group", "🔄 Modify Existing Group"])

# =====================================================================
# TAB 1: REGISTER NEW GROUP SYSTEM
# =====================================================================
with tab_create:
    if not all_courses:
        st.warning("⚠️ No active courses are registered in the system. Registration is currently offline.")
    else:
        # Create a dynamic selection list mapping IDs to course names
        course_options = {f"{c['courseCode']} (Section {c['courseSection']})": c['courseID'] for c in all_courses}
        
        selected_course_label = st.selectbox("Select Your Course Track *", options=list(course_options.keys()), key="reg_course_sel")
        target_course_id = course_options[selected_course_label]
        
        g_name = st.text_input("Enter your group's name *", placeholder="e.g., Team Alpha", key="reg_g_name")
        
        g_students_text = st.text_area(
            "Enter group member names in separate lines *", 
            placeholder="John Smith\nJane Doe\nAlex Johnson",
            height=120,
            key="reg_students_text"
        )
        
        g_email = st.text_input("Enter email to receive group # and name *", placeholder="contact@domain.com", key="reg_email")
        
        st.markdown("---")
        
        if st.button("Save New Group Profile", width="stretch", key="btn_save_group"):
            if not g_name or not g_students_text or not g_email:
                st.error("All starred fields are required to process registration.")
            else:
                try:
                    conn = get_mysql_connection()
                    with conn.cursor() as cursor:
                        # TRANSACTION STEP 1: Insert into parent presentationgroup table
                        group_sql = """
                            INSERT INTO presentationgroup (groupName, courseID, email_address) 
                            VALUES (%s, %s, %s)
                        """
                        cursor.execute(group_sql, (g_name.strip(), int(target_course_id), g_email.strip()))
                        
                        # Retrieve the newly generated groupID auto-increment primary key
                        new_group_id = cursor.lastrowid
                        
                        # TRANSACTION STEP 2: Parse raw student lines, split names, and batch insert
                        student_sql = """
                            INSERT INTO student (studentName, FirstName, LastName, groupID, courseID) 
                            VALUES (%s, %s, %s, %s, %s)
                        """
                        
                        raw_lines = g_students_text.split("\n")
                        added_students_count = 0
                        
                        for line in raw_lines:
                            clean_full_name = line.strip()
                            if clean_full_name:  # Avoid empty lines
                                # Split the name by the first space encounter
                                name_parts = clean_full_name.split(" ", 1)
                                f_name = name_parts[0].strip()
                                l_name = name_parts[1].strip() if len(name_parts) > 1 else ""
                                
                                cursor.execute(student_sql, (
                                    clean_full_name, 
                                    f_name, 
                                    l_name, 
                                    int(new_group_id), 
                                    int(target_course_id)
                                ))
                                added_students_count += 1
                                
                    conn.commit()
                    conn.close()
                    
                    st.success(f"🎉 Success! Group '{g_name}' registered. Assigned Group ID: **{new_group_id}**. Registered {added_students_count} team members.")
                    st.balloons()
                    
                except Exception as tx_err:
                    st.error(f"Database registration failure: {tx_err}")

# =====================================================================
# TAB 2: MODIFY EXISTING GROUP SYSTEM
# =====================================================================
with tab_modify:
    st.subheader("🛠️ Modify an Already Entered Group")
    st.write("To alter members or group designations, input your System Assigned Group ID below.")
    
    mod_group_id = st.number_input("Enter Group ID *", min_value=1, step=1, key="mod_id_input")
    confirm_checkbox = st.checkbox("Confirm editing group entry", value=False, key="mod_chk_confirm")
    
    st.markdown("---")
    
    if st.button("Fetch Group Information to Edit", width="stretch", key="btn_fetch_mod"):
        if not confirm_checkbox:
            st.warning("You must check the confirmation box to authorize data changes.")
        else:
            try:
                conn = get_mysql_connection()
                with conn.cursor() as cursor:
                    # Look up group meta details
                    cursor.execute("SELECT * FROM presentationgroup WHERE groupID = %s", (int(mod_group_id),))
                    group_meta = cursor.fetchone()
                conn.close()
                
                if not group_meta:
                    st.error(f"No existing records found matching Group ID '{mod_group_id}'. Verify the index number.")
                else:
                    st.session_state["target_mod_group_id"] = mod_group_id
                    st.session_state["cached_group_meta"] = group_meta
                    st.rerun()
            except Exception as e:
                st.error(f"Lookup failure: {e}")

    # Render editing fields if a valid group has been loaded into session memory
    if "target_mod_group_id" in st.session_state and st.session_state["target_mod_group_id"] == mod_group_id:
        cached_meta = st.session_state["cached_group_meta"]
        
        with st.container(border=True):
            st.info(f"✏️ Modifying Parameters for Group ID: **{mod_group_id}**")
            
            up_g_name = st.text_input("Group Name", value=cached_meta["groupName"], key="up_g_name")
            up_g_email = st.text_input("Contact Email Address", value=cached_meta["email_address"], key="up_g_email")
            
            # Text explanation block for resetting student lists
            st.caption("⚠️ **Note on Student Lists:** Saving edits below will replace the current student list for this group. Please enter the complete list of team member names below:")
            
            up_g_students = st.text_area(
                "Group Member Names (one per line)", 
                placeholder="John Smith\nJane Doe",
                height=120,
                key="up_students_text"
            )
            
            if st.button("Commit Group Modifications", width="stretch", key="btn_save_mod_group"):
                if not up_g_name or not up_g_email or not up_g_students:
                    st.error("All update fields must be filled out.")
                else:
                    try:
                        conn = get_mysql_connection()
                        with conn.cursor() as cursor:
                            # 1. Update the parent presentationgroup properties
                            cursor.execute(
                                "UPDATE presentationgroup SET groupName = %s, email_address = %s WHERE groupID = %s",
                                (up_g_name.strip(), up_g_email.strip(), int(mod_group_id))
                            )
                            
                            # 2. Clear out older member rosters for this group ID to avoid duplicates
                            cursor.execute("DELETE FROM student WHERE groupID = %s", (int(mod_group_id),))
                            
                            # 3. Batch insert the updated roster list
                            student_sql = """
                                INSERT INTO student (studentName, FirstName, LastName, groupID, courseID) 
                                VALUES (%s, %s, %s, %s, %s)
                            """
                            raw_lines = up_g_students.split("\n")
                            for line in raw_lines:
                                clean_full_name = line.strip()
                                if clean_full_name:
                                    name_parts = clean_full_name.split(" ", 1)
                                    f_name = name_parts[0].strip()
                                    l_name = name_parts[1].strip() if len(name_parts) > 1 else ""
