import streamlit as st
import pymysql
import datetime
import pandas as pd
import requests

# =====================================================================
# SECURE CACHED HOSTINGER MYSQL CONFIGURATION ENGINE
# =====================================================================
@st.cache_resource(ttl=300)
def get_cached_mysql_connection():
    return pymysql.connect(
        host=st.secrets["mysql"]["host"],
        user=st.secrets["mysql"]["user"],
        password=st.secrets["mysql"]["password"],
        database=st.secrets["mysql"]["database"],
        port=st.secrets["mysql"].get("port", 3306),
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )

# =====================================================================
# HUGGING FACE INFERENCE ENGINE COMPONENT
# =====================================================================
def query_huggingface_llm(prompt_text, system_instruction="You are a concise academic writing assistant."):
    """Helper function to execute remote inference over Hugging Face's API."""
    try:
        # Fetch your secure API Token from Streamlit Secrets manager
        hf_token = st.secrets["huggingface"]["api_token"]
        
        # Using a highly accurate instructional model well-suited for academic parsing tasks
        model_url = "https://huggingface.co"
        headers = {"Authorization": f"Bearer {hf_token}", "Content-Type": "application/json"}
        
        # Construct the instruction payload structure
        payload = {
            "inputs": f"<s>[SYSTEM] {system_instruction} [/SYSTEM] [USER] {prompt_text} [/USER] </s>",
            "parameters": {"temperature": 0.2, "max_new_tokens": 500}
        }
        
        response = requests.post(model_url, headers=headers, json=payload, timeout=25)
        response_json = response.json()
        
        # Parse output safely based on Hugging Face common return object shapes
        if isinstance(response_json, list) and len(response_json) > 0:
            return response_json[0].get("generated_text", "AI response parsing failed.")
        elif isinstance(response_json, dict) and "generated_text" in response_json:
            return response_json["generated_text"]
        else:
            return f"Unexpected AI Response Structure: {response_json}"
    except Exception as e:
        return f"AI connection error details: {e}"

# =====================================================================
# UI WORKSPACE INTERFACE
# =====================================================================
st.title("🎤 Schedule & Enter My Presentation Details")
st.write("Input your System Assigned Group ID to review available calendar tracks and claim your slot.")
st.markdown("---")

input_group_id = st.number_input("Enter your Group ID *", min_value=1, step=1, key="pres_group_id_lookup")

if st.button("Fetch My Group & Course Details", width="stretch"):
    try:
        conn = get_cached_mysql_connection()
        with conn.cursor() as cursor:
            sql = """
                SELECT g.groupID, g.groupName, g.courseID, c.courseCode, c.courseSection, c.courseTerm, c.courseDate 
                FROM presentationgroup g
                JOIN course c ON g.courseID = c.courseID
                WHERE g.groupID = %s
            """
            cursor.execute(sql, (int(input_group_id),))
            group_record = cursor.fetchone()
        
        if not group_record:
            st.error(f"❌ Verification Failed: No registered group found matching ID '{input_group_id}'.")
            st.session_state["active_student_group_id"] = None
        else:
            TERM_LABELS = {"1": "Fall", "2": "Winter", "3": "Summer"}
            raw_term = str(group_record["courseTerm"])
            term_text = TERM_LABELS.get(raw_term, f"Term {raw_term}")
            year_text = str(group_record["courseDate"].year) if isinstance(group_record["courseDate"], (datetime.date, datetime.datetime)) else "N/A"

            st.session_state["active_student_group_id"] = group_record["groupID"]
            st.session_state["active_student_group_name"] = group_record["groupName"]
            st.session_state["active_student_course_id"] = group_record["courseID"]
            st.session_state["active_student_course_label"] = f"{group_record['courseCode']} - Section {group_record['courseSection']} ({term_text} {year_text})"
            st.rerun()
    except Exception as e:
        st.error(f"Server lookup connection failure: {e}")

# Render workspace area only if group ID matches
if "active_student_group_id" in st.session_state and st.session_state["active_student_group_id"] == input_group_id:
    g_id = st.session_state["active_student_group_id"]
    g_name = st.session_state["active_student_group_name"]
    c_id = st.session_state["active_student_course_id"]
    c_label = st.session_state["active_student_course_label"]
    
    with st.container(border=True):
        st.success(f"🟢 Verified: Team **'{g_name}'** logged into course track: `{c_label}`")
        
        # --- DATABASE LOOKUP FUNCTIONS ---
        def fetch_open_dates(course_id):
            try:
                conn = get_cached_mysql_connection()
                with conn.cursor() as cursor:
                    sql = "SELECT pres_dateID, presDate FROM presentationdate WHERE courseID = %s AND (groupID IS NULL OR groupID = 0) ORDER BY presDate ASC"
                    cursor.execute(sql, (int(course_id),))
                    slots = cursor.fetchall()
                return slots
            except Exception: return []

        def fetch_presentation_types():
            try:
                conn = get_cached_mysql_connection()
                with conn.cursor() as cursor:
                    # Reads dynamic values straight from your presentationType table rows
                    cursor.execute("SELECT typeName FROM presentationType")
                    types = cursor.fetchall()
                return [t["typeName"] for t in types] if types else ["Standard Presentation"]
            except Exception:
                return ["Standard Presentation"]

        open_slots_list = fetch_open_dates(c_id)
        pres_types_list = fetch_presentation_types()
        
        if not open_slots_list:
            st.warning("⚠️ Scheduling Restricted: There are currently no open slots left for this course track.")
        else:
            slot_options = {f"{s['presDate'].strftime('%A, %B %d, %Y')} - (ID: {s['pres_dateID']})": s['pres_dateID'] for s in open_slots_list}
            selected_slot_label = st.selectbox("Choose an Available Calendar Presentation Slot *", options=list(slot_options.keys()))
            target_date_id = slot_options[selected_slot_label]
            
            st.markdown("---")
            st.markdown("##### 📝 Topic Scope Declaration")
            topic_title = st.text_input("Presentation Topic / Title Name *", placeholder="e.g., Implementing LLMs via Streamlit Frameworks")
            topic_abstract = st.text_area("Provide a Short Abstract / Overview summary", placeholder="Provide a brief explanation of your topic scope here...")
            
            # --- OPERATION A: CHECK TOPIC FIT ENGINE ---
            if st.button("🔍 Check Topic Fit", width="stretch"):
                if not topic_title or not topic_abstract:
                    st.error("Please enter a title and description before executing AI feedback.")
                else:
                    with st.spinner("AI engine checking alignment with course syllabus parameters..."):
                        try:
                            # 1. Fetch parent syllabus text directly from Hostinger
                            conn = get_cached_mysql_connection()
                            with conn.cursor() as cursor:
                                cursor.execute("SELECT syllabus_text FROM course WHERE courseID = %s", (int(c_id),))
                                course_data = cursor.fetchone()
                            syllabus_context = course_data["syllabus_text"] if course_data else "None provided."
                            
                            # 2. Build the context prompt
                            fit_prompt = f"""
                            Review if this proposed student presentation topic fits well within the following course syllabus parameters.
                            
                            --- COURSE SYLLABUS TRACK ---
                            {syllabus_context}
                            
                            --- PROPOSED STUDENT PRESENTATION ---
                            Proposed Title: {topic_title}
                            Proposed Abstract: {topic_abstract}
                            
                            Guidelines:
                            - Provide constructive feedback.
                            - Estimate a score out of 5 stars for syllabus fit.
                            - Return your entire response formatted cleanly as simple HTML using <p> and <ul><li> blocks.
                            """
                            
                            # 3. Call remote inference model
                            feedback_html = query_huggingface_llm(fit_prompt, "You are a constructive university academic curriculum advisor.")
                            
                            st.info("📊 **AI Syllabus Alignment Feedback**")
                            # Renders the HTML block beautifully on screen cleanly
                            st.markdown(feedback_html, unsafe_allow_html=True) [21]
                        except Exception as err:
                            st.error(f"Failed to compile syllabus criteria metrics: {err}")
            
            st.markdown("---")
            
            # --- CHOOSE PRESENTATION TYPE DROP-DOWN CONSOLE ---
            selected_type = st.selectbox("Select Presentation Type *", options=pres_types_list)
