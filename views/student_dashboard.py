import streamlit as st

st.set_page_config(page_title="Student Participation Hub", layout="wide")

st.title("🎓 Student Participation Hub")
st.subheader("Welcome! Access your presentation ratings, group structures, and class activities below.")
st.markdown("---")

# ---------------------------------------------------------------------
# ROW 1: TOP HIGHLIGHT METRICS (Optional Student Context)
# ---------------------------------------------------------------------
m1, m2, m3 = st.columns(3)
with m1:
    st.metric(label="Global Presentation Average", value="4.72 / 5.0 ⭐")
with m2:
    st.metric(label="Active Class Trackers", value="Open")
with m3:
    st.metric(label="Your Participation Status", value="Verified")

st.markdown("---")
st.subheader("⚙️ Available Student Operations")

# Layout Configuration: Organize the 7 operations into clean visual quadrants
col1, col2 = st.columns(2)

# --- QUADRANT 1: EVALUATIONS & FEEDBACK ---
with col1:
    st.markdown("### 📝 Presentation & Peer Reviews")
    
    # Operation 1
    if st.button("⭐ 1. Rate a Peer Presentation", use_container_width=True):
        st.info("Form to submit a live 5-star presentation evaluation initiated.")
        
    # Operation 2
    if st.button("📊 2. View My Presentation Scores", use_container_width=True):
        st.info("Pulling personal grade distribution sheets from the database...")
        
    # Operation 3
    if st.button("💬 3. Read Peer Feedback Comments", use_container_width=True):
        st.info("Loading anonymized text feedback reports.")
        
    # Operation 4
    if st.button("📋 4. Access Grading Rubrics", use_container_width=True):
        st.info("Displaying official 5starpresentationrater.com core evaluation criteria.")

# --- QUADRANT 2: GROUPS & CALENDARS ---
with col2:
    st.markdown("### 👥 Schedules & Team Assets")
    
    # Operation 5
    if st.button("👥 5. Check My Assigned Group", use_container_width=True):
        st.info("Loading group roster listings for the current academic semester.")
        
    # Operation 6
    if st.button("📅 6. View Upcoming Schedule Timeline", use_container_width=True):
        st.info("Displaying presentation dates and scheduled team order.")
        
    # Operation 7
    if st.button("📥 7. Download Syllabus & Course Materials", use_container_width=True):
        st.info("Streaming files from host database matrix...")
