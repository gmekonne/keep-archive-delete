import streamlit as st
import subprocess
import datetime
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

