import streamlit as st
import subprocess
import datetime
import calendar
import pandas as pd
# =====================================================================
# SECTION 1: EXISTING CODE (Confluence Data Lifecycle Manager)
# =====================================================================
st.title("Confluence Data Lifecycle Manager")
st.write("Manage Keep / Archive / Delete workflow")

if st.button("Start Data Management"):
    result = subprocess.run(["python", "start_data_management.py"])
    if result.returncode == 0:
        st.success("Excel file generated successfully.")
    else:
        st.error("Process failed.")

if st.button("Complete Data Management"):
    result = subprocess.run(["python", "complete_data_management.py"])
    if result.returncode == 0:
        st.success("Data management completed.")
    else:
        st.error("Process failed.")

# Add a visual divider between your original tool and the new dashboard
st.markdown("---")

# =====================================================================
# SECTION 2: NEW INSTRUCTOR DASHBOARD
# =====================================================================

# 1. Title and Subtitle
st.title("Instructor Dashboard")
st.subheader("Welcome!")
st.write(
    "From here, you can enter your course, view presentations, "
    "manage groups, review ratings, and export grades."
)


# Mock data for demonstration - replace this with your real database query later
mock_courses = pd.DataFrame({
    "Course No.": [1, 2, 3],
    "Course Code": ["COMP101", "DATA202", "PROG303"],
    "Course Section": ["A", "B", "C"],
    "Course Date": ["Mon/Wed", "Tue/Thu", "Friday"]
})



# 2. Your Courses Section
st.markdown("### Your Courses")
st.dataframe(mock_courses, use_container_width=True)

# 3. Participation Calendar
st.markdown("### Participation Calendar")
selected_course = st.selectbox(
    "Select a course to view calendar and presentation information:", 
    options=mock_courses["Course Code"].tolist()
)

# Basic calendar mock implementation
selected_date = st.date_input("View schedule for date:", datetime.date.today())

# Simulation of a "popup window" presentation information using Streamlit Dialogs
@st.dialog("Presentation Details")
def show_presentation_details(course, date):
    st.write(f"**Course:** {course}")
    st.write(f"**Date:** {date}")
    st.write("**Scheduled Teams:** Group 3, Group 5")
    st.write("**Topics:** LLM System Architectures, GitHub Deployments")
    st.metric(label="Current 5-Star Rating", value="4.8 ⭐")

if st.button("👁️ View Presentation Details for Selected Date"):
    show_presentation_details(selected_course, selected_date)

st.markdown("---")

# 4. Dashboard Action Sections
st.markdown("## Management Controls")

# Layout Section 1: Courses and Class Setup
with st.expander("📂 1. Courses and Class Setup", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Add Course"):
            st.info("Form to add course clicked.")
        if st.button("❌ View / Delete Course"):
            st.info("Course catalog list loaded.")
    with col2:
        if st.button("📈 View Contributions"):
            st.info("Contribution metrics loaded.")
        if st.button("🔄 Import Students from Brightspace"):
            st.info("Brightspace API / CSV connection triggered.")

# Layout Section 2: Presentations and Ratings
with st.expander("⭐ 2. Presentations and Ratings", expanded=True):
    col3, col4 = st.columns(2)
    with col3:
        if st.button("👥 Load Presentations and Groups"):
            st.info("Group data synchronized.")
        if st.button("📝 Load Peer Ratings"):
            st.info("Peer evaluations imported.")
        if st.button("🏅 Grade Presentations"):
            st.info("Grading rubric interface active.")
    with col4:
        if st.button("📊 View Grades"):
            st.info("Gradebook calculations displayed.")
        if st.button("📥 Download Brightspace CSV"):
            st.info("Generating Brightspace compatible CSV file...")




# =====================================================================
# SECTION 2: NEW INSTRUCTOR DASHBOARD
# =====================================================================

st.title("Instructor Dashboard")
st.subheader("Welcome!")
st.write(
    "From here, you can enter your course, view presentations, "
    "manage groups, review ratings, and export grades."
)

# Mock Course Database Table
mock_courses = pd.DataFrame({
    "Course No.": [1, 2, 3],
    "Course Code": ["COMP101", "DATA202", "PROG303"],
    "Course Section": ["A", "B", "C"],
    "Course Date": ["Mon/Wed", "Tue/Thu", "Friday"]
})

st.markdown("### Your Courses")
st.dataframe(mock_courses, use_container_width=True)

# ---------------------------------------------------------------------
# FIX: PROACTIVE PARTICIPATION CALENDAR (Database Search Simulation)
# ---------------------------------------------------------------------
st.markdown("### Participation Calendar")
selected_course = st.selectbox(
    "Select a course to check scheduled presentations:", 
    options=mock_courses["Course Code"].tolist()
)

# This dictionary simulates your future database containing scheduled presentation dates
# Using hardcoded dates within June 2026 for simulation
mock_schedule_db = {
    "COMP101": [
        {"date": datetime.date(2026, 6, 15), "teams": "Group 1, Group 2", "topics": "Intro to Git"},
        {"date": datetime.date(2026, 6, 22), "teams": "Group 3, Group 4", "topics": "Python Basics"}
    ],
    "DATA202": [
        {"date": datetime.date(2026, 6, 16), "teams": "Group A", "topics": "Pandas Dataframes"},
        {"date": datetime.date(2026, 6, 18), "teams": "Group B", "topics": "Data Visualizations"}
    ],
    "PROG303": [
        {"date": datetime.date(2026, 6, 19), "teams": "Group Omega", "topics": "LLM Feasibility Studies"}
    ]
}

# 1. Fetch scheduled entries for the chosen course from our simulated database
course_schedule = mock_schedule_db.get(selected_course, [])

# 2. Extract just the dates so we can alert the instructor immediately
scheduled_dates = [item["date"] for item in course_schedule]

if scheduled_dates:
    # Build a clean visual notification listing all active presentation dates
    st.info(f"📅 **Upcoming Presentations found for {selected_course} on:**")
    for s_date in scheduled_dates:
        st.markdown(f"• **{s_date.strftime('%A, %B %d, %Y')}**")
else:
    st.warning("⚠️ No presentations are currently scheduled for this course.")

# 3. Allow user to input a date to view popup details, default loading the first active schedule date
default_date = scheduled_dates[0] if scheduled_dates else datetime.date.today()
selected_date = st.date_input("Select a date below to view full dashboard popup details:", default_date)

# Simulation of a "popup window" presentation information using Streamlit Dialogs
@st.dialog("Presentation Details")
def show_presentation_details(course, date, schedule_list):
    # Search the active presentation list for a matching date
    match = next((item for item in schedule_list if item["date"] == date), None)
    
    st.write(f"### 📋 Details for {course}")
    st.write(f"**Selected Date:** {date.strftime('%B %d, %Y')}")
    st.markdown("---")
    
    if match:
        st.success("🟢 Presentation Scheduled")
        st.write(f"**Scheduled Teams:** {match['teams']}")
        st.write(f"**Topics:** {match['topics']}")
        st.metric(label="Current Class 5-Star Rating", value="4.8 ⭐")
    else:
        st.error("🔴 No Presentation Scheduled")
        st.write("There are no presentations logged in the database for this specific date.")

if st.button("👁️ Open Presentation Details Popup"):
    show_presentation_details(selected_course, selected_date, course_schedule)

st.markdown("---")

# =====================================================================
# SECTION 3: DASHBOARD ACTION SECTIONS
# =====================================================================
st.markdown("## Management Controls")

with st.expander("📂 1. Courses and Class Setup", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Add Course"):
            st.info("Form to add course clicked.")
        if st.button("❌ View / Delete Course"):
            st.info("Course catalog list loaded.")
    with col2:
        if st.button("📈 View Contributions"):
            st.info("Contribution metrics loaded.")
        if st.button("🔄 Import Students from Brightspace"):
            st.info("Brightspace API / CSV connection triggered.")

with st.expander("⭐ 2. Presentations and Ratings", expanded=True):
    col3, col4 = st.columns(2)
    with col3:
        if st.button("👥 Load Presentations and Groups"):
            st.info("Group data synchronized.")
        if st.button("📝 Load Peer Ratings"):
            st.info("Peer evaluations imported.")
        if st.button("🏅 Grade Presentations"):
            st.info("Grading rubric interface active.")
    with col4:
        if st.button("📊 View Grades"):
            st.info("Gradebook calculations displayed.")
        if st.button("📥 Download Brightspace CSV"):
            st.info("Generating Brightspace compatible CSV file...")
