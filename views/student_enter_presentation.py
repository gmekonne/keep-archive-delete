import streamlit as st

st.title("🎤 Schedule & Enter My Presentation Details")
st.write("Secure an open calendar slot and record your topic description outline.")

# Future DB lookup placeholder for course selections
course_sel = st.selectbox("Select Your Enrolled Course Track:", options=["Pick a Course...", "COMP101 (Sec A)", "DATA202 (Sec B)"])

if course_sel != "Pick a Course...":
    st.info("📅 Checking available assignment slots from 'presentationdate' table...")
    
    # Future query row select mapping list
    available_slots = ["2026-09-15 - Slot #1 (Open)", "2026-09-15 - Slot #2 (Open)", "2026-09-22 - Slot #1 (Open)"]
    chosen_slot = st.selectbox("Choose an Available Calendar Presentation Slot *", options=available_slots)
    
    with st.form("presentation_details_form"):
        group_id = st.text_input("Your Assigned Team/Group Number (Optional)")
        pres_title = st.text_input("Presentation Topic / Title Name *")
        pres_summary = st.text_area("Provide a Short Abstract / Overview summary")
        
        save_pres = st.form_submit_button("Lock in Presentation Slot", width="stretch")
        
    if save_pres:
        st.warning("Presentation parameters ready for SQL submission.")
