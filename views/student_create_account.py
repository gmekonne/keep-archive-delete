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

def send_group_confirmation_email(recipient_email, group_id, group_name, course_label):
    try:
        sender = st.secrets["email"]["sender_email"]
        password = st.secrets["email"]["sender_password"]
        server_host = st.secrets["email"]["smtp_server"]
        server_port = int(st.secrets["email"]["smtp_port"])
        
        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = recipient_email
        msg['Subject'] = "🎓 5-Star Presentation Rater - Group Registration Confirmed"
        
        body = f"Hello,\n\nYour team has been registered successfully.\nGroup Name: {group_name}\nGroup ID: {group_id}\nCourse: {course_label}"
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        with smtplib.SMTP_SSL(server_host, server_port, timeout=4) as server:
            server.login(sender, password)
            server.sendmail(sender, recipient_email, msg.as_string())
        return True
    except Exception as e:
        st.sidebar.warning(f"Mail delivery skipped: {e}")
        return False

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
            year_text = str(c["courseDate"].year) if isinstance(c["courseDate"], (datetime.date, datetime.datetime)) else "N/A"
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
                        for line in raw_lines:
                            clean_full_name = line.strip()
                            if clean_full_name:
                                name_parts = clean_full_name.split(" ", 1)
                                f_name = name_parts[0].strip() if len(name_parts) > 0 else ""
                                l_name = name_parts[1].strip() if len(name_parts) > 1 else ""
                                cursor.execute(student_sql, (clean_full_name, f_name, l_name, int(new_group_id), int(target_course_id)))
                    conn.commit()
                    conn.close()
                    
                    send_group_confirmation_email(g_email.strip(), new_group_id, g_name.strip(), selected_course_label)
                    st.success(f"🎉 Success! Group registered. Your System Group ID is: **{new_group_id}**.")
                    st.balloons()
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
        # FIXED: Loads the separate script drawer file to prevent file truncation completely
        with open("views/student_modify_group.py", encoding="utf-8") as f:
            exec(compile(f.read(), "views/student_modify_group.py", "exec"), globals())
