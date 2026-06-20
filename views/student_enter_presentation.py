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

def query_huggingface_llm(prompt_text, system_instruction="You are a concise academic writing assistant."):
    try:
        hf_token = st.secrets["huggingface"]["api_token"]
        model_url = "https://huggingface.co"
        headers = {"Authorization": f"Bearer {hf_token}", "Content-Type": "application/json"}
        payload = {
            "inputs": f"<s>[SYSTEM] {system_instruction} [/SYSTEM] [USER] {prompt_text} [/USER] </s>",
            "parameters": {"temperature": 0.2, "max_new_tokens": 500}
        }
        response = requests.post(model_url, headers=headers, json=payload, timeout=25)
        response_json = response.json()
        if isinstance(response_json, list) and len(response_json) > 0:
            return response_json.get("generated_text", "AI response parsing failed.")
        elif isinstance(response_json, dict) and "generated_text" in response_json:
            return response_json["generated_text"]
        else:
            return f"Unexpected AI Response Structure: {response_json}"
    except Exception as e:
        return f"AI connection error details: {e}"

st.title("🎤 Schedule & Enter My Presentation Details")
st.write("Input your System Assigned Group ID to review available calendar tracks and claim your slot.")
st.markdown("---")

input_group_id = st.number_input("Enter your Group ID *", min_value=1, step=1, key="pres_group_id_lookup")

if st.button("Fetch My Group & Course Details", width="stretch"):
    try:
        conn = get_cached_mysql_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT groupID, groupName, courseID FROM presentationgroup WHERE groupID = %s", (int(input_group_id),))
            group_record = cursor.fetchone()
            
            if not group_record:
                st.error(f"❌ Verification Failed: No registered group found matching ID '{input_group_id}'.")
                st.session_state["active_student_group_id"] = None
            else:
                cursor.execute("SELECT courseCode, courseSection, courseTerm, courseDate FROM course WHERE courseID = %s", (int(group_record["courseID"]),))
                course_record = cursor.fetchone()
                
                if not course_record:
                    st.error("❌ Linkage Error: Your group points to a course track that no longer exists.")
                else:
                    TERM_LABELS = {"1": "Fall", "2": "Winter", "3": "Summer"}
                    raw_term = str(course_record["courseTerm"])
                    term_text = TERM_LABELS.get(raw_term, f"Term {raw_term}")
                    
                    year_text = "N/A"
                    if course_record["courseDate"]:
                        if isinstance(course_record["courseDate"], (datetime.date, datetime.datetime)):
                            year_text = str(course_record["courseDate"].year)
                        else:
                            year_text = str(course_record["courseDate"]).split("-")

                    st.session_state["active_student_group_id"] = group_record["groupID"]
                    st.session_state["active_student_group_name"] = group_record["groupName"]
                    st.session_state["active_student_course_id"] = group_record["courseID"]
                    st.session_state["active_student_course_label"] = f"{course_record['courseCode']} - Section {course_record['courseSection']} ({term_text} {year_text})"
                    st.rerun()
    except Exception as e:
        st.error(f"Server lookup connection failure: {e}")
if "active_student_group_id" in st.session_state and st.session_state["active_student_group_id"] == input_group_id:
    g_id = st.session_state["active_student_group_id"]
    g_name = st.session_state["active_student_group_name"]
    c_id = st.session_state["active_student_course_id"]
    c_label = st.session_state["active_student_course_label"]
    
    with st.container(border=True):
        st.success(f"🟢 Verified: Team **'{g_name}'** logged into course track: `{c_label}`")
        
        def fetch_open_dates(course_id):
            try:
                conn = get_cached_mysql_connection()
                with conn.cursor() as cursor:
                    # FIXED SQL EXPR: Uses your tinyint logic (dateTaken = 0 means available)
                    sql = """
                        SELECT pres_dateID, presDate 
                        FROM presentationdate 
                        WHERE courseID = %s AND dateTaken = 0
                        ORDER BY presDate ASC
                    """
                    cursor.execute(sql, (int(course_id),))
                    slots = cursor.fetchall()
                return slots
            except Exception: return []

        def fetch_presentation_types():
            try:
                conn = get_cached_mysql_connection()
                with conn.cursor() as cursor:
                    cursor.execute("SELECT typeName FROM presentationType")
                    types = cursor.fetchall()
                return [t["typeName"] for t in types] if types else ["Standard Presentation"]
            except Exception: return ["Standard Presentation"]

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
            
            if st.button("🔍 Check Topic Fit", width="stretch"):
                if not topic_title or not topic_abstract:
                    st.error("Please enter a title and description before executing AI feedback.")
                else:
                    with st.spinner("AI engine checking alignment with course syllabus parameters..."):
                        try:
                            conn = get_cached_mysql_connection()
                            with conn.cursor() as cursor:
                                cursor.execute("SELECT syllabus_text FROM course WHERE courseID = %s", (int(c_id),))
                                course_data = cursor.fetchone()
                            syllabus_context = course_data["syllabus_text"] if course_data else "None provided."
                            
                            fit_prompt = f"Review if this proposed student presentation topic fits well within the following course syllabus parameters.\n\n--- COURSE SYLLABUS TRACK ---\n{syllabus_context}\n\n--- PROPOSED STUDENT PRESENTATION ---\nProposed Title: {topic_title}\nProposed Abstract: {topic_abstract}\n\nGuidelines:\n- Provide constructive feedback.\n- Estimate a score out of 5 stars for syllabus fit.\n- Return your entire response formatted cleanly as simple HTML using <p> and <ul/li> blocks."
                            feedback_html = query_huggingface_llm(fit_prompt, "You are a constructive university academic curriculum advisor.")
                            st.info("📊 **AI Syllabus Alignment Feedback**")
                            st.markdown(feedback_html, unsafe_allow_html=True)
                        except Exception as err:
                            st.error(f"Failed to compile syllabus criteria metrics: {err}")
            
            st.markdown("---")
            selected_type = st.selectbox("Select Presentation Type *", options=pres_types_list)
            
            if st.button("💡 Describe Presentation Type", width="stretch"):
                with st.spinner(f"AI compiling parameters for type '{selected_type}'..."):
                    describe_prompt = f"You are helping students quickly understand a selected presentation type.\nIn 80–120 words, provide:\n- A concise definition of the presentation type \"{selected_type}\".\n- 3–5 bullet examples of situations where it is well-suited.\n\nGuidelines:\n- Be neutral, academic, and clear.\n- Use short sentences.\n- Avoid fluff.\n- Return simple HTML with <p> and <ul><li> bullets (no external links, no scripts)."
                    type_description_html = query_huggingface_llm(describe_prompt)
                    st.info(f"📖 **About Type: {selected_type}**")
                    st.markdown(type_description_html, unsafe_allow_html=True)

            st.markdown("---")
            if st.button("🔒 Lock in Presentation Slot & Confirm Selection", width="stretch"):
                if not topic_title:
                    st.error("You must fill out your Presentation Topic Title to secure your reservation.")
                else:
                    try:
                        conn = get_mysql_connection() if "mysql" in st.secrets else get_cached_mysql_connection()
                        with conn.cursor() as cursor:
                            # FIXED: Overwrites groupID and updates dateTaken flag to 1 (taken)
                            sql_claim = """
                                UPDATE presentationdate 
                                SET groupID = %s, dateTaken = 1
                                WHERE pres_dateID = %s
                            """
                            cursor.execute(sql_claim, (int(g_id), int(target_date_id)))
                        st.session_state["active_student_group_id"] = None
                        st.success("🎉 Presentation confirmed! Your slots are now permanently locked in the database matrix.")
                        st.balloons()
                    except Exception as tx_err:
                        st.error(f"Failed to submit calendar reservation: {tx_err}")
