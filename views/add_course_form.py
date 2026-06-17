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
    height=150
)

# 6. Presentation Guidelines Textarea
c_instruct = st.text_area(
    "Guidelines of Presentation (students will view them when entering their presentation).",
    placeholder="e.g., Topic selection, presentation duration, rewards for best presentation(s), etc.",
    height=120
)

# 7. MULTI-DATE ACCUMULATOR FIELD (Generates a dynamic list of calendar dates)
st.markdown("##### Choose Date(s) *")
today = datetime.date.today()
# Generate a rolling list of the next 120 calendar days (covering a full semester)
semester_calendar_days = [today + datetime.timedelta(days=x) for x in range(120)]
date_options_strings = [d.strftime("%Y-%m-%d (%A)") for d in semester_calendar_days]

selected_date_strings = st.multiselect(
    "Click below to select and highlight all presentation dates for the semester:",
    options=date_options_strings,
    placeholder="Select multiple dates..."
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
    if not c_code:
        st.error("Course Name/Code field is strictly required.")
    elif not selected_date_strings:
        st.error("You must select at least one presentation date for the semester field.")
    else:
        try:
            conn = get_mysql_connection()
            current_timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
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
                
                # STEP 2: Loop through the selected date strings to write to presentationdate
                # Using your exact column schema: presDate, date_entered, courseID, courseSection, termID, userID
                pres_date_sql = """
                    INSERT INTO presentationdate 
                    (presDate, date_entered, courseID, courseSection, termID, userID) 
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                
                inserted_slots_count = 0
                for date_str in selected_date_strings:
                    # Extract the raw 'YYYY-MM-DD' segment back out of our formatted string selection
                    raw_date_iso = date_str.split(" ")[0]
                    
                    # Duplicate slot insertion loop matching your presentations count limit per day
                    for _ in range(int(num_pres_day)):
                        cursor.execute(pres_date_sql, (
                            raw_date_iso,
                            current_timestamp,
                            new_course_id,
                            c_sec,
                            int(c_term_val),
                            int(current_uid)
                        ))
                        inserted_slots_count += 1
                        
            conn.commit()
            conn.close()
            st.success(f"🎉 Course saved! Added {inserted_slots_count} active presentation slots to 'presentationdate'.")
            st.rerun()
            
        except Exception as database_transaction_error:
            st.error(f"Failed to record course data matrices: {database_transaction_error}")
