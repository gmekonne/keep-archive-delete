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

st.subheader(f"🏅 Instructor Presentation Grading: {selected_course_code}")
st.write("Review presentation materials and log final evaluation marks straight to the ledger.")
st.markdown("---")

target_course_id = st.session_state.get("active_dashboard_last_cid", 0)

if target_course_id == 0:
    st.info("💡 Please select an active course code option from the dashboard selector first.")
else:
    presentations_list = []
    rubric_options_map = {}
    
    try:
        conn = get_mysql_connection()
        with conn.cursor() as cursor:
            # 1. Fetch all active presentations matching this specific course ID
            sql_load_pres = """
                SELECT p.presID, p.presTitle, p.presGrade, g.groupName 
                FROM presentation p
                INNER JOIN presentationgroup g ON p.groupID = g.groupID
                WHERE p.courseID = %s AND p.status = 'scheduled'
                ORDER BY g.groupName ASC
            """
            cursor.execute(sql_load_pres, (int(target_course_id),))
            presentations_list = cursor.fetchall()
            
            # 2. Fetch the structural grading rubrics configuration criteria weights
            # Targets fields from your 'grading_rubric' schema table layout
            cursor.execute("SELECT rubricID, rubricDescription, maxPoints FROM grading_rubric ORDER BY rubricID ASC")
            rubric_rows = cursor.fetchall()
            if rubric_rows:
                # Map titles to their exact weights for clear guidance context prompts
                rubric_options_map = {f"📝 {r['rubricDescription']} (Max: {r['maxPoints']} Points)": r for r in rubric_rows}
                
        conn.close()
    except Exception as e:
        st.error(f"Failed to load presentation grading parameters: {e}")

    if not presentations_list:
        st.warning(f"ℹ️ No active scheduled presentations found under course section track '{selected_course_code}'.")
    else:
        # Create an options dictionary mapping team profiles to their records
        pres_options_map = {f"👥 Group: {p['groupName']} — Topic: \"{p['presTitle']}\"": p for p in presentations_list}
        selected_target_label = st.selectbox("Select target student group presentation to grade:", options=list(pres_options_map.keys()))
        
        chosen_pres = pres_options_map[selected_target_label]
        target_pres_id = chosen_pres["presID"]
        current_saved_grade = chosen_pres["presGrade"]
        
        st.markdown("---")
        
        # Display Rubric Reference Dropdown Box for fast guidelines review
        if rubric_options_map:
            st.caption("📖 Instructor Rubric Evaluation Guidelines Tracker Reference Panel:")
            st.selectbox("Review class rubric rules and criteria weights:", options=list(rubric_options_map.keys()), index=0, label_visibility="collapsed", key="grading_rubric_ref_selector")
            st.markdown("---")
            
        # 3. Grading Input Form Component Layout
        with st.form(f"executive_grading_form_{target_pres_id}", clear_on_submit=False):
            st.markdown(f"##### 📝 Score Allocator Card: **{chosen_pres['groupName']}**")
            st.write(f"**Presentation Title:** *\"{chosen_pres['presTitle']}\"*")
            
            initial_grade_value = float(current_saved_grade) if current_saved_grade is not None else 0.0
            display_status_label = f"★ Current Grade: **{current_saved_grade}**" if current_saved_grade is not None else "⏳ Status: Awaiting Score Allocation"
            st.caption(display_status_label)
            
            # Numeric mark entry widget box row
            assigned_points = st.number_input("Input Final Presentation Grade Points *", min_value=0.0, max_value=100.0, value=initial_grade_value, step=0.5)
            save_grade_btn = st.form_submit_button("💾 Save Grade to Ledger", width="stretch")
            
        if save_grade_btn:
            try:
                conn = get_mysql_connection()
                with conn.cursor() as cursor:
                    # Enforced Transactional Save Rule: Commits the metric straight to the presentation table row
                    sql_commit_grade = "UPDATE presentation SET presGrade = %s WHERE presID = %s"
                    cursor.execute(sql_commit_grade, (float(assigned_points), int(target_pres_id)))
                    
                st.success(f"🎉 Success! A final presentation mark of **{assigned_points}** has been securely recorded for team **'{chosen_pres['groupName']}'**.")
                st.balloons()
                conn.close()
                st.rerun()
            except Exception as tx_err:
                st.error(f"Failed to write presentation grade payload cell: {tx_err}")
                
    st.markdown("---")
