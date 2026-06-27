import streamlit as st
import pymysql
import pandas as pd

def get_mysql_connection():
    """Fresh uncached link to satisfy Hostinger firewall connection rules."""
    return pymysql.connect(
        host=st.secrets["mysql"]["host"],
        user=st.secrets["mysql"]["user"],
        password=st.secrets["mysql"]["password"],
        database=st.secrets["mysql"]["database"],
        port=st.secrets["mysql"].get("port", 3306),
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )

# Inherit the course context currently highlighted on the main dashboard workspace row
if "dash_course_sel_v2" in st.session_state:
    selected_course_code = st.session_state["dash_course_sel_v2"]
else:
    selected_course_code = "Selected Course"

st.subheader(f"👥 Roster Directory: {selected_course_code}")
st.write("Review all registered student presentation groups and their active team members.")
st.markdown("---")

# Read the validated course ID currently cached in active dashboard memory loop parameters
target_course_id = st.session_state.get("active_dashboard_last_cid", 0)

if target_course_id == 0:
    # Fallback indicator: If the main dashboard hasn't saved the primary key integer yet, pull it dynamically
    try:
        conn = get_mysql_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT courseID FROM course WHERE courseCode = %s LIMIT 1", (selected_course_code,))
            c_row = cursor.fetchone()
            if c_row:
                target_course_id = int(c_row["courseID"])
        conn.close()
    except Exception:
        target_course_id = 0

if target_course_id == 0:
    st.info("💡 Please select an active course code option from the calendar selector box on the main dashboard first.")
else:
    groups_data_matrix = []
    
    try:
        conn = get_mysql_connection()
        with conn.cursor() as cursor:
            # Relational SQL: Group concat sews individual student name strings together separated cleanly by commas
            sql_roster_matrix = """
                SELECT g.groupName AS 'Group Name',
                       GROUP_CONCAT(s.studentName ORDER BY s.studentName ASC SEPARATOR ', ') AS 'Members Summary'
                FROM presentationgroup g
                INNER JOIN student s ON g.groupID = s.groupID
                WHERE g.courseID = %s
                GROUP BY g.groupID, g.groupName
                ORDER BY g.groupName ASC
            """
            cursor.execute(sql_roster_matrix, (int(target_course_id),))
            groups_data_matrix = cursor.fetchall()
        conn.close()
    except Exception as e:
        st.error(f"Failed to compile course group roster matrices: {e}")

    # UI Element Render Table Generation Phase
    if not groups_data_matrix:
        st.warning(f"ℹ️ No registered student groups or rosters found under course section track '{selected_course_code}' yet.")
        st.info("💡 **Next Step:** Instruct your students to create team accounts from their seat, or use the **Brightspace CSV Importer** to bulk-load the roster.")
    else:
        st.success(f"📋 Compiled **{len(groups_data_matrix)}** active presenting groups for this course!")
        
        # Format the data into a clean structure for the visual table grid
        formatted_list = []
        for index, item in enumerate(groups_data_matrix, start=1):
            formatted_list.append({
                "No.": f"{index:02d}",
                "👥 Presentation Group Name": str(item["Group Name"]),
                "🎓 Registered Team Members": str(item["Members Summary"])
            })
            
        df_roster = pd.DataFrame(formatted_list)
        
        # Render a clean, wide spreadsheet grid display with matching structural columns
        st.dataframe(
            df_roster,
            width="stretch",
            hide_index=True,
            use_container_width=True
        )
        
    st.markdown("---")
