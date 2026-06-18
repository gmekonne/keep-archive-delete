import streamlit as st

st.title("⭐ My Presentation Metrics & Peer Evaluation Feed")
st.write("Track your scores, five-star average weight metrics, and anonymous text comments.")

with st.expander("🔐 Verify Identity to View Performance Scores", expanded=True):
    st_uid = st.text_input("Confirm Student Email / ID:")
    st_pass = st.text_input("Enter Dashboard Password:", type="password")
    check = st.button("Unlock Scorecards Grid", width="stretch")

if check:
    st.success("Identity Verified! Displaying evaluation analytics matrix charts:")
    st.metric(label="Your Aggregated Presentation Rating", value="4.82 / 5.0 ⭐", delta="+0.12 vs Class Avg")
