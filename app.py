import streamlit as st
import subprocess
import datetime
import calendar
import pandas as pd

# Set the page configuration to widescreen format (Crucial for Dashboard Designs)
st.set_page_config(
    page_title="5-Star Presentation Rater Dashboard", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# =====================================================================
# SIDEBAR: SYSTEM & MAINTENANCE CONTROLS
# =====================================================================
with st.sidebar:
    st.image("https://icons8.com", width=60)
    st.title("System Control Panel")
    st.markdown("---")
    
    # Existing Tool isolated cleanly inside an expander so it stays out of the dashboard workspace
    with st.expander("🛠️ Confluence Data Lifecycle", expanded=False):
        st.caption("Manage Keep / Archive / Delete workflows below:")
        if st.button("Start Data Management", use_container_width=True):
            result = subprocess.run(["python", "start_data_management.py"])
            if result.returncode == 0:
                st.success("Excel generated.")
            else:
                st.error("Process failed.")

        if st.button("Complete Data Management", use_container_width=True):
            result = subprocess.run(["python", "complete_data_management.py"])
            if result.returncode == 0:
                st.success("Completed.")
            else:
                st.error("Process failed.")
                
    st.markdown("---")
    st.caption("v1.0.0 • Connected to Hostinger via GitHub")

# =====================================================================
# MAIN WORKSPACE: INSTRUCTOR DASHBOARD
# =====================================================================

# Title & Subtitle Banner
st.title("🎓 Instructor Dashboard")
st.markdown(
    "Welcome! From here, you can enter your course, view presentations, "
    "manage groups, review ratings, and export grades."
)
st.markdown("---")

# Mock Database Tables
mock_courses = pd.DataFrame({
    "Course No.": [1, 2, 3],
    "Course Code": ["COMP101", "DATA202", "PROG303"],
    "Course Section": ["A", "B", "C"],
    "Course Date": ["Mon/Wed", "Tue/Thu", "Friday"]
})

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

# ---------------------------------------------------------------------
# ROW 1: TOP EXECUTIVE METRIC CARDS
# ---------------------------------------------------------------------
m_col1, m_col2, m_col3, m_col4 = st.columns(4)
with m_col1:
    st.metric(label="Active Courses", value=str(len(mock_courses)), delta="Semester Peak")
with m_col2:
    st.metric(label="Total Scheduled Presentations", value="5 Dates", delta="2 Completed")
with m_col3:
    st.metric(label="Global Presentation Rating", value="4.80 / 5.0", delta="0.25 ⭐ Increase")
with m_col4:
    st.metric(label="Pending Peer Reviews", value="14 Reviews", delta="-8 Today", delta_color="inverse")

st.markdown("---")

# ---------------------------------------------------------------------
# ROW 2: SPLIT SCREEN (Left: Courses Data | Right: Smart Calendar)
# ---------------------------------------------------------------------
left_panel, right_panel = st.columns([3, 2])

with left_panel:
    st.subheader("📚 Your Active Courses")
    st.dataframe(mock_courses, use_container_width=True, hide_index=True)

with right_panel:
    st.subheader("📅 Participation Calendar")
    selected_course = st.selectbox(
        "Select a course to search schedule database:", 
        options=mock_courses["Course Code"].tolist(),
        label_visibility="collapsed"
    )
    
    course_schedule = mock_schedule_db.get(selected_course, [])
    scheduled_dates = [item["date"] for item in course_schedule]
    
    # Inline dashboard alerts highlighting active dates immediately
    if scheduled_dates:
        date_strings = ", ".join([d.strftime('%b %d') for d in scheduled_dates])
        st.info(f"⚡ **Presentations found on:** {date_strings}")
    else:
        st.warning("⚠️ No active dates found for this course.")

    # Contextual date picker interaction row
    c_col1, c_col2 = st.columns([3, 2])
    with c_col1:
        default_date = scheduled_dates[0] if scheduled_dates else datetime.date.today()
        selected_date = st.date_input("Target Date Lookup:", default_date, label_visibility="collapsed")
    with c_col2:
        # Dialog Popup implementation
        @st.dialog("Presentation Details")
        def show_presentation_details(course, date, schedule_list):
            match = next((item for item in schedule_list if item["date"] == date), None)
            st.write(f"### 📋 Details for {course}")
            st.write(f"**Date:** {date.strftime('%B %d, %Y')}")
            st.markdown("---")
            if match:
                st.success("🟢 Presentation Active")
                st.write(f"**Scheduled Teams:** {match['teams']}")
                st.write(f"**Topics:** {match['topics']}")
                st.metric(label="Current Class 5-Star Rating", value="4.8 ⭐")
            else:
                st.error("🔴 Empty Slot")
                st.write("No presentations scheduled for this specific date.")

        if st.button("👁️ View Details", use_container_width=True):
            show_presentation_details(selected_course, selected_date, course_schedule)

st.markdown("---")

# ---------------------------------------------------------------------
# ROW 3: MANAGEMENT CONTROL TABS
# ---------------------------------------------------------------------
st.subheader("⚙️ Control & Operations Console")

tab1, tab2 = st.tabs(["📂 1. Courses and Class Setup", "⭐ 2. Presentations and Ratings"])

with tab1:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("➕ Add Course", use_container_width=True):
            st.toast("Add course menu initiated!")
    with col2:
        if st.button("❌ View / Delete Course", use_container_width=True):
            st.toast("Course directory pulled.")
    with col3:
        if st.button("📈 View Contributions", use_container_width=True):
            st.toast("Analytics dashboard loaded.")
    with col4:
        if st.button("🔄 Import Brightspace Students", use_container_width=True):
            st.toast("Roster sync initiated.")

with tab2:
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        if st.button("👥 Load Presentations & Groups", use_container_width=True):
            st.toast("Group roster data updated.")
    with col2:
        if st.button("📝 Load Peer Ratings", use_container_width=True):
            st.toast("Importing peer raw files...")
    with col3:
        if st.button("🏅 Grade Presentations", use_container_width=True):
            st.toast("Grading interface open.")
    with col4:
        if st.button("📊 View Grades", use_container_width=True):
            st.toast("Calculating student averages...")
    with col5:
        if st.button("📥 Download Brightspace CSV", use_container_width=True):
            st.toast("Exporting CSV file...")
