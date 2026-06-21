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

st.title("📅 My Upcoming Presentation Schedule")
st.write("Lookup your team's assigned presentation date, topic parameters, and timeline metrics.")
st.markdown("---")

# 1. User-Friendly Input Interface
input_gid = st.number_input("Enter your Group ID *", min_value=1, step=1, key="student_date_lookup_val")

if st.button("Fetch My Presentation Schedule", use_container_width=True):
    try:
        conn = get_mysql_connection()
        with conn.cursor() as cursor:
            # Step 1: Check if the presentation records exist for this group ID
            sql_pres = """
                SELECT p.presTitle, p.presDescription, p.pres_date, p.status, g.groupName, p.courseID, p.coursesection
                FROM presentation p
                JOIN presentationgroup g ON p.groupID = g.groupID
                WHERE p.groupID = %s
                ORDER BY p.presID DESC LIMIT 1
            """
            cursor.execute(sql_pres, (int(input_gid),))
            pres_record = cursor.fetchone()
            
            if not pres_record:
                # Fallback Step 1.2: Check if the group name exists but hasn't booked an appointment slot yet
                cursor.execute("SELECT groupName FROM presentationgroup WHERE groupID = %s", (int(input_gid),))
                group_exists = cursor.fetchone()
                
                if group_exists:
                    st.warning(f"⚠️ Team **'{group_exists['groupName']}'** is registered, but you have not reserved a calendar slot yet.")
                    st.info("💡 **Next Step:** Navigate to the **🎤 2. Enter Presentation** workspace page on the left menu to lock in your date slot!")
                else:
                    st.error(f"❌ Record Not Found: No group is currently assigned to Group ID '{input_gid}'. Please check your registration confirmation receipt.")
            
            else:
                # Step 2: Fetch the complete member roster checklist for this group ID
                cursor.execute("SELECT studentName FROM student WHERE groupID = %s", (int(input_gid),))
                roster_data = cursor.fetchall()
                roster_names = [r["studentName"] for r in roster_data] if roster_data else ["None Registered"]
                roster_string = ", ".join(roster_names)
                
                # Step 3: Fetch course parameters for context matching
                cursor.execute("SELECT courseCode FROM course WHERE courseID = %s", (int(pres_record["courseID"]),))
                course_data = cursor.fetchone()
                c_code = course_data["courseCode"] if course_data else "Unknown"

                # 2. Render Clean, Responsive Student Information Cards Layout
                st.balloons()
                with st.container(border=True):
                    st.subheader(f"🎉 Scheduled Date: {pres_record['pres_date'].strftime('%A, %B %d, %Y')}")
                    st.markdown("---")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"📚 **Course Track:** `{c_code} (Section {pres_record['coursesection']})`")
                        st.markdown(f"👥 **Group Name:** **{pres_record['groupName']}** (ID: {input_gid})")
                        st.markdown(f"📋 **Team Roster:** *{roster_string}*")
                    
                    with col2:
                        st.markdown(f"🎤 **Presentation Title:** **{pres_record['presTitle']}**")
                        status_color = "green" if pres_record["status"] == "scheduled" else "orange"
                        st.markdown(f"⚙️ **Status:** : {pres_record['status'].upper()}")
                    
                    st.markdown("---")
                    st.markdown(f"📝 **Topic Abstract Summary:**\n*{pres_record['presDescription']}*")
                    
        conn.close()
    except Exception as server_error:
        st.error(f"Server data retrieval failure: {server_error}")
