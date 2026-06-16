import streamlit as st

st.title("🚀 ClassParticipation Management System")
st.subheader("Turn Student Presentations into Actionable Analytics")

st.markdown("""
Welcome to the modern hub for tracking, grading, and maximizing student interaction. 
Our platform bridges the gap between classroom presentations and automated gradebooks like Brightspace.

### 🌟 Core Framework Features
* **5-Star Presentation Rater:** Empower peers and instructors to deliver instant structured reviews.
* **Smart Participation Calendar:** View dynamic presentation timelines without digging through emails.
* **Seamless LMS Integrations:** Sync rosters and export grades directly via Brightspace-compatible CSV files.
* **Corporate Roster Mapping:** Institutional support for departments managing multiple course tracks.

---
### 🛠️ Get Started
If you are an active instructor, use the sidebar menu on the left to **Log In** to your executive workspace console, or **Register** a new account.
""")

# Optional visual layout grid on your homepage
col1, col2 = st.columns(2)
with col1:
    st.info("💡 **Did you know?** Peer evaluations can increase classroom engagement by up to 40%.")
with col2:
    st.success("🔒 **Enterprise Security:** Your student rosters are completely isolated and anchored safely to your production database.")
