import streamlit as st
import datetime
import pymysql

# Reference variables inherited from the global instructor session state
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

st.title("➕ Add New Course to Profile")
st.write("Enter course configurations and presentation dates below.")
st.markdown("---")

# 1. Course Name / Code Input
c_code = st.text_input("Course Name/Code *", placeholder="e.g., COMP101")

# 2. Course Year & Start Date Picker
c_start_date = st.date_input("Course Year & Start Date *", datetime.date.today())

# 3. Course Term Dropdown Selector
c_term_options = {"First": "1", "Second": "2", "Third": "3"}
c_term_label = st.selectbox("Course Term *", options=list(c_term_options.keys()))
c_term_val = c_term_options[c_term_label]

# 4. Class Section Alphabetical Dropdown Selection Row
alphabet_sections = [chr(i) for i in range(ord('A'), ord('Z')+1)]
c_sec = st.selectbox("Class Section *", options=alphabet_sections)

# 5. Course Outline / Syllabus Textarea
c_syllabus = st.text_area(
    "Paste Course Outline or Syllabus", 
    placeholder="Paste the course description, objectives, and weekly topics here...",
    height=200
)

# 6. Presentation Guidelines Textarea
c_instruct = st.text_area(
    "Guidelines of Presentation (students will view them when entering their presentation).",
    placeholder="e.g., Topic selection, presentation duration, rewards for best presentation(s), etc.",
    height=150
)

# 7. MULTI-DATE CALENDAR SELECTION (FIXED)
c_presentation_dates = st.date_input(
    "Choose Presentation Date(s) *",
    value=datetime.date.today(),
    format="YYYY-MM-DD"
)

# 8. Number of Presentations Per Day Counter Selector
num_pres_day = st.selectbox(
    "Number of Presentations per Day", 
    options=[i for i in range(1, 11)], 
    index=0
)

st.markdown("---")

# --- SUBMISSION TRANSACTION RUNNER ---
if st.button("Save Course and Schedule Matrix", width="stretch"):
    if not c_code or not c_presentation_dates:
        st.error("Course Name/Code and at least one Selected Presentation Date are strictly required.")
    else:
        try:
            conn = get_mysql_connection()
            with conn.cursor() as cursor:
                # STEP 1: Insert the main course profile parameters
                course_sql = """
                    INSERT INTO course 
                    (courseSection, courseCode, courseTitle, courseDate, instruction, courseTerm, userID, ratingType, syllabus_text) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(course_sql, (
                    c_sec, 
                    c_code.strip(), 
                    c_code.strip(), 
                    c_start_date.strftime('%Y-%m-%d'), 
                    c_instruct.strip() if c_instruct else "None", 
                    c_term_val, 
                    int(current_uid), 
                    "5-Star", 
                    c_syllabus.strip() if c_syllabus else "Syllabus pending..."
                ))
                
                new_course_id = cursor.lastrowid
                
                # STEP 2: Loop through selected calendar days to write to presentationdate table
                pres_date_sql = """
                    INSERT INTO presentationdate (courseID, pdate) 
                    VALUES (%s, %s)
                """
                
                inserted_slots_count = 0
                target_dates_list = c_presentation_dates if isinstance(c_presentation_dates, (list, tuple)) else [c_presentation_dates]
                
                for selected_day in target_dates_list:
                    formatted_day_str = selected_day.strftime('%Y-%m-%d')
                    for _ in range(int(num_pres_day)):
                        cursor.execute(pres_date_sql, (new_course_id, formatted_day_str))
                        inserted_slots_count += 1
                        
            conn.commit()
            conn.close()
            st.success(f"🎉 Course saved! Added {inserted_slots_count} active presentation slots to 'presentationdate'.")
            st.rerun()
        except Exception as database_transaction_error:
            st.error(f"Failed to record course data matrices: {database_transaction_error}")
