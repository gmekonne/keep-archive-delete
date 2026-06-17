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

# Initialize session state array to track list of selected dates across re-runs
if "semester_dates_bucket" not in st.session_state:
    st.session_state.semester_dates_bucket = []

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

st.markdown("---")
st.markdown("### 📅 Presentation Schedule Matrix Setup")

# 7. MULTI-DATE ACCUMULATOR INTERFACE (Fixed to allow unlimited non-consecutive picks)
col_date_pick, col_date_btn = st.columns([2, 1])

with col_date_pick:
    picker_date = st.date_input("Pick a Presentation Date", datetime.date.today())
with col_date_btn:
    st.write("##") # Visual alignment padding spacer
    if st.button("➕ Add Date to Schedule", width="stretch"):
        if picker_date not in st.session_state.semester_dates_bucket:
            st.session_state.semester_dates_bucket.append(picker_date)
            # Sort the dates chronologically automatically
            st.session_state.semester_dates_bucket.sort()

# Visual Display showing the instructor exactly what dates have been collected so far
if st.session_state.semester_dates_bucket:
    st.info("📋 **Currently Collected Semester Presentation Dates:**")
    # Display dates as clean visual tag summaries with a button to wipe selection if needed
    for i, date_item in enumerate(st.session_state.semester_dates_bucket):
        st.markdown(f"• **Date #{i+1}:** {date_item.strftime('%A, %B %d, %Y')}")
    
    if st.button("🗑️ Clear All Selected Dates"):
        st.session_state.semester_dates_bucket = []
        st.rerun()
else:
    st.warning("⚠️ No presentation dates have been added to this course matrix yet.")

# 8. Number of Presentations Per Day Counter Selector
num_pres_day = st.selectbox(
    "Number of Presentations per Day for Selected Dates", 
    options=[i for i in range(1, 11)], 
    index=0
)

st.markdown("---")

# --- SUBMISSION TRANSACTION RUNNER ---
if st.button("Save Course and Schedule Matrix", width="stretch"):
    if not c_code:
        st.error("Course Name/Code field is strictly required.")
    elif not st.session_state.semester_dates_bucket:
        st.error("You must accumulate at least one presentation date to establish the schedule.")
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
                
                # STEP 2: Loop through the collected semester dates from session state bucket
                pres_date_sql = """
                    INSERT INTO presentationdate (courseID, pdate) 
                    VALUES (%s, %s)
                """
                
                inserted_slots_count = 0
                for selected_day in st.session_state.semester_dates_bucket:
                    formatted_day_str = selected_day.strftime('%Y-%m-%d')
                    
                    # Duplicate slot insertion matching your exact multi-presentations count limit per day
                    for _ in range(int(num_pres_day)):
                        cursor.execute(pres_date_sql, (new_course_id, formatted_day_str))
                        inserted_slots_count += 1
                        
            conn.commit()
            conn.close()
            
            # Wiping the date accumulator memory clean following a successful insertion task
            st.session_state.semester_dates_bucket = []
            
            st.success(f"🎉 Course saved! Added {inserted_slots_count} active presentation slots to 'presentationdate'.")
            st.rerun()
            
        except Exception as database_transaction_error:
            st.error(f"Failed to record course data matrices: {database_transaction_error}")
