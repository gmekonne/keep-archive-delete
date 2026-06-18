import streamlit as st

st.title("📅 Course Presentation Calendar Timeline")
st.write("Review the scheduled running order for student presentations across the semester.")

target_course = st.selectbox("Choose Course Matrix to View Timeline:", options=["COMP101", "DATA202"])
st.markdown("---")

# Placeholder dataframe grid simulation mapping future table queries
st.subheader(f"📊 Running Order Schedule for {target_course}")
st.caption("Below are the locked and available time blocks tracked on Hostinger:")
st.write("🔍 [Data Grid Query Layout Placeholder Table to stream from database]")
