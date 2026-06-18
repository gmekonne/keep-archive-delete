import streamlit as st

st.title("💡 Submit Classroom Engagement Contributions")
st.write("Share extra research concepts, helpful study videos, references, or suggestions.")

with st.form("contribution_form"):
    c_course = st.selectbox("Select Destination Course:", options=["COMP101", "DATA202"])
    c_type = st.selectbox("Contribution Content Type:", options=["Research Link/URL", "Idea Text/Suggestion", "Video Tutorial Asset"])
    c_title = st.text_input("Brief Title Descriptor *")
    c_body = st.text_area("Elaborate Your Contribution Concepts or Paste Link Here *")
    
    send_contrib = st.form_submit_button("Submit Contribution Entry", width="stretch")

if send_contrib:
    st.success("Thank you! Your contribution record has been saved for instructor review.")
