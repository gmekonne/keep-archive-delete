import streamlit as st
import pymysql
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def get_mysql_connection():
    return pymysql.connect(
        host=st.secrets["mysql"]["host"],
        user=st.secrets["mysql"]["user"],
        password=st.secrets["mysql"]["password"],
        database=st.secrets["mysql"]["database"],
        port=st.secrets["mysql"].get("port", 3306),
        cursorclass=pymysql.cursors.DictCursor
    )

# =====================================================================
# SMTP AUTOMATED MAIL ENGINE
# =====================================================================
def send_group_confirmation_email(recipient_email, group_id, group_name, course_label):
    """Logs into your outbound SMTP server and delivers group tracking parameters to the user."""
    try:
        sender = st.secrets["email"]["sender_email"]
        password = st.secrets["email"]["sender_password"]
        server_host = st.secrets["email"]["smtp_server"]
        server_port = int(st.secrets["email"]["smtp_port"])
        
        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = recipient_email
        msg['Subject'] = "🎓 5-Star Presentation Rater - Group Registration Confirmed"
        
        body = f"""Hello,

Your presentation team roster has been successfully registered and synced with your instructor's course tracker!

Here are your official group tracking parameters:
-------------------------------------------------------------
📚 Course Track: {course_label}
👥 Group Name:   {group_name}
🆔 System Group ID: {group_id}
-------------------------------------------------------------

⚠️ IMPORTANT: Keep your Group ID safe! Your team members will need to input this exact ID number when scheduling presentation dates or viewing peer feedback profiles.

Best regards,
The 5-Star Presentation Rater Automation Engine
"""
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        try:
            with smtplib.SMTP_SSL(server_host, server_port, timeout=7) as server:
                server.login(sender, password)
                server.sendmail(sender, recipient_email, msg.as_string())
            return True
        except Exception:
            fallback_port = 587 if server_port == 465 else 465
            with smtplib.SMTP(server_host, fallback_port, timeout=7) as server:
                server.starttls()
                server.login(sender, password)
                server.sendmail(sender, recipient_email, msg.as_string())
            return True
            
    except Exception as mail_err:
        st.sidebar.warning(f"Notification engine skipped: {mail_err}")
        return False

# =====================================================================
# UI LAYOUT INTERFACE
# =====================================================================
st.title("👥 Student Registration & Group Portal")
st.write("Register a new presentation team or update an existing team roster.")
st.markdown("---")

TERM_LABELS = {"1": "Fall", "2": "Winter", "3": "Summer"}

def fetch_available_courses():
    try:
        conn = get_mysql_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT courseID, courseCode, courseSection, courseTerm, courseDate FROM course")
            courses = cursor.fetchall()
        conn.close()
        return courses
    except Exception as e:
        st.error(f"Failed to fetch classroom listings: {e}")
        return []

all_courses = fetch_available_courses()
tab_create, tab_modify = st.tabs(["➕ Register New Group", "🔄 Modify Existing Group"])

# --- TAB 1: CREATE GROUP ---
with tab_create:
    if not all_courses:
        st.warning("⚠️ No active courses are registered. Registration is offline.")
    else:
        course_options = {}
        for c in all_courses:
            raw_term = str(c["courseTerm"])
            term_text = TERM_LABELS.get(raw_term, f"Term {raw_term}")
            
            year_text = "N/A"
            if c["courseDate"]:
                if isinstance(c["courseDate"], (datetime.date, datetime.datetime)):
                    year_text = str(c["courseDate"].year)
                else:
                    year_text = str(c["courseDate"]).split("-")[0]
            
            unique_label = f"{c['courseCode']} - Section {c['courseSection']} ({term_text} {year_text})"
            course_options[unique_label] = c['courseID']
            
        selected_course_label = st.selectbox("Select Your Course Track *", options=list(course_options.keys()), key="reg_course_sel")
        target_course_id = course_options[selected_course_label]
        
        g_name = st.text_input("Enter your group's name *", placeholder="e.g., Team Alpha", key="reg_g_name")
        g_students_text = st.text_area("Enter group member names in separate lines *", placeholder="John Smith\nJane Doe", height=120, key="reg_students_text")
        g_email = st.text_input("Enter email to receive group # and name *", placeholder="contact@domain.com", key="reg_email")
        st.markdown("---")
        
        if st.button("Save New Group Profile", width="stretch", key="btn_save_group"):
            if not g_name or not g_students_text or not g_email:
                st.error("All starred fields are required.")
            else:
                try:
                    conn = get_mysql_connection()
                    with conn.cursor() as cursor:
                        group_sql = "INSERT INTO presentationgroup (groupName, courseID, email_address) VALUES (%s, %s, %s)"
                        cursor.execute(group_sql, (g_name.strip(), int(target_course_id), g_email.strip()))
                        new_group_id = cursor.lastrowid
                        
                        student_sql = "INSERT INTO student (studentName, FirstName, LastName, groupID, courseID) VALUES (%s, %s, %s, %s, %s)"
                        raw_lines = g_students_text.split("\n")
                        added_students_count = 0
                        
                        for line in raw_lines:
                            clean_full_name = line.strip()
                            if clean_full_name:
                                name_parts = clean_full_name.split(" ", 1)
                                f_name = name_parts[0].strip() if len(name_parts) > 0 else ""
                                l_name = name_parts[1].strip() if len(name_parts) > 1 else ""
                                
                                cursor.execute(student_sql, (clean_full_name, f_name, l_name, int(new_group_id), int(target_course_id)))
                                added_students_count += 1
                    conn.commit()
                    conn.close()

                    # Disable email sending temporarily
                    # mail_sent = send_group_confirmation_email(g_email.strip(), new_group_id, g_name.strip(), selected_course_label)
                    mail_sent = False
                    
                    if mail_sent:
                        st.success(f"🎉 Success! Group registered. ID: **{new_group_id}**. Confirmation sent to {g_email}.")
                    else:
                        st.success(f"🎉 Roster saved successfully! System Group ID: **{new_group_id}**.")
                    st.rerun()
                except Exception as tx_err:
                    st.error(f"Database registration failure: {tx_err}")

# --- TAB 2: MODIFY GROUP ---
with tab_modify:
    st.subheader("🛠️ Modify an Already Entered Group")
    mod_group_id = st.number_input("Enter Group ID *", min_value=1, step=1, key="mod_id_input")
    confirm_checkbox = st.checkbox("Confirm editing group entry", value=False, key="mod_chk_confirm")
    st.markdown("---")
    
    if st.button("Fetch Group Information to Edit", width="stretch", key="btn_fetch_mod"):
        if not confirm_checkbox:
            st.warning("You must check the confirmation box.")
        else:
            try:
                conn = get_mysql_connection()
                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM presentationgroup WHERE groupID = %s", (int(mod_group_id),))
                    group_meta = cursor.fetchone()
                conn.close()
                if not group_meta:
                    st.error(f"No group found matching ID '{mod_group_id}'.")
                else:
                    st.session_state["target_mod_group_id"] = mod_group_id
                    st.session_state["cached_group_meta"] = group_meta
                    st.rerun()
            except Exception as e:
                st.error(f"Lookup failure: {e}")

    if "target_mod_group_id" in st.session_state and st.session_state["target_mod_group_id"] == mod_group_id:
        cached_meta = st.session_state["cached_group_meta"]
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
