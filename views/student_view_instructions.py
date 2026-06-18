import streamlit as st

st.title("📋 Instructor Presentation Guidelines")
st.write("Review grading rubrics, presentation expectations, and rules set by the professor.")

target_course = st.selectbox("Select Classroom Track Guidelines:", options=["COMP101", "DATA202"])
st.markdown("---")

st.subheader("📢 Guidelines & Grading Rubrics")
st.info("These rules are streamed live from the instructor's 'instruction' table column on Hostinger:")
st.markdown("""
* **Duration:** 10 Minutes flat + 3 minutes peer Q&A loop.
* **Rubrics Matrix:** Topic clarity, slide formatting, delivery cadence, and peer response depth.
""")
