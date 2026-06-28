import streamlit as st
import pymysql
import pandas as pd

def get_mysql_connection():
    """Fresh real-time link straight to Hostinger."""
    return pymysql.connect(
        host=st.secrets["mysql"]["host"],
        user=st.secrets["mysql"]["user"],
        password=st.secrets["mysql"]["password"],
        database=st.secrets["mysql"]["database"],
        port=st.secrets["mysql"].get("port", 3306),
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )

# Inherit course code from the main dashboard selector row
if "dash_course_sel_v2" in st.session_state:
    selected_course_code = st.session_state["dash_course_sel_v2"]
else:
    selected_course_code = "Selected Course"

st.subheader(f"📊 Class Gradebook Ledger: {selected_course_code}")
st.write("Review final recorded presentation grades allocated across all registered class groups.")
st.markdown("---")

target_course_id = st.session_state.get("active_dashboard_last_cid", 0)

if target_course_id == 0:
    st.info("💡 Please select an active course code option from the dashboard selector first.")
else:
    grades_matrix = []
    
    try:
        conn = get_mysql_connection()
        with conn.cursor() as cursor:
            # Relational SQL: Extracts group name, topic title, and numeric score parameters cleanly
            sql_grades = """
                SELECT g.groupName AS 'Group Name',
                       p.presTitle AS 'Presentation Title',
                       p.presGrade AS 'Grade'
                FROM presentation p
                INNER JOIN presentationgroup g ON p.groupID = g.groupID
                WHERE p.courseID = %s AND p.status = 'scheduled'
                ORDER BY g.groupName ASC
            """
            cursor.execute(sql_grades, (int(target_course_id),))
            grades_matrix = cursor.fetchall()
        conn.close()
    except Exception as e:
        st.error(f"Failed to compile course grade matrix logs: {e}")

    # UI Element Render Table Generation Phase
    if not grades_matrix:
        st.warning(f"ℹ️ No presentation records or recorded grades found under course tracking section '{selected_course_code}' yet.")
    else:
        st.success(f"📋 Compiled **{len(grades_matrix)}** active group score card records!")
        
        # Format rows beautifully into a structured visual grid list layout
        formatted_grades = []
        for index, row in enumerate(grades_matrix, start=1):
            raw_score = row["Grade"]
            # Formatting text markers if a team hasn't been scored by the professor yet
            score_display = f"{float(raw_score):.1f} Pts" if raw_score is not None else "⏳ Pending"
            
            formatted_grades.append({
                "No.": f"{index:02d}",
                "👥 Presentation Group": str(row["Group Name"]),
                "🎤 Registered Topic Title": str(row["Presentation Title"]),
                "🏅 Awarded Grade Mark": score_display
            })
            
        df_gradebook = pd.DataFrame(formatted_grades)
        
        # Render a clean, full-width widescreen spreadsheet block tracker grid table row element
        st.dataframe(
            df_gradebook,
            width="stretch",
            hide_index=True,
            use_container_width=True
        )
        
    st.markdown("---")
