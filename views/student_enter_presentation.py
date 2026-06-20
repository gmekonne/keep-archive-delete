import streamlit as st
import pymysql
import datetime
import pandas as pd
import requests

def get_mysql_connection():
    """Creates a fresh, completely uncached real-time socket link straight to Hostinger."""
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
        
        # UPDATED: Swapped to a highly available, ultra-fast instruction model to prevent 503/empty returns
        model_url = "https://huggingface.co"
        headers = {"Authorization": f"Bearer {hf_token}", "Content-Type": "application/json"}
        
        payload = {
            "inputs": f"<|im_start|>system\n{system_instruction}<|im_end|>\n<|im_start|>user\n{prompt_text}<|im_end|>\n<|im_start|>assistant\n",
            "parameters": {"temperature": 0.3, "max_new_tokens": 400}
        }
        
        response = requests.post(model_url, headers=headers, json=payload, timeout=25)
        
        # Safety Check: If the server returns a non-200 code, catch the raw text directly
        if response.status_code != 200:
            return f"<p style='color:orange;'>⚠️ Hugging Face Server Message (Status {response.status_code}): {response.text}</p>"
            
        response_json = response.json()
        
        if isinstance(response_json, list) and len(response_json) > 0:
            text_out = response_json[0].get("generated_text", "")
            # Clean up the prompt echoes if the model returns the whole conversation chain
            if "assistant\n" in text_out:
                text_out = text_out.split("assistant\n")[-1]
            return text_out
        elif isinstance(response_json, dict) and "generated_text" in response_json:
            return response_json["generated_text"]
        else:
            return str(response_json)
            
    except Exception as e:
        return f"<p style='color:red;'>❌ AI evaluation processing temporarily offline: {e}</p>"










st.title("🎤 Schedule & Enter My Presentation Details")
st.write("Input your System Assigned Group ID to review available calendar tracks and claim your slot.")
st.markdown("---")

input_group_id = st.number_input("Enter your Group ID *", min_value=1, step=1, key="pres_group_id_lookup")

if st.button("Fetch My Group & Course Details", use_container_width=True):
    try:
        conn = get_mysql_connection()
        with conn.cursor() as cursor:
            # Flat SQL Query 1: Fetch Group Profile
            cursor.execute("SELECT groupID, groupName, courseID FROM presentationgroup WHERE groupID = %s", (int(input_group_id),))
            group_record = cursor.fetchone()
            
            if not group_record:
                st.error(f"❌ Verification Failed: No registered group found matching ID '{input_group_id}'.")
                st.session_state["active_student_group_id"] = None
            else:
                # Flat SQL Query 2: Fetch Parent Course Parameters
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
                            year_text = str(course_record["courseDate"]).split("-")[0]

                    st.session_state["active_student_group_id"] = group_record["groupID"]
                    st.session_state["active_student_group_name"] = group_record["groupName"]
                    st.session_state["active_student_course_id"] = group_record["courseID"]
                    st.session_state["active_student_course_label"] = f"{course_record['courseCode']} - Section {course_record['courseSection']} ({term_text} {year_text})"
                    st.session_state["active_student_course_uid"] = group_record["courseID"]
                    st.rerun()
        conn.close()
    except Exception as e:
        st.error(f"Server lookup connection failure: {e}")
if "active_student_group_id" in st.session_state and st.session_state["active_student_group_id"] == input_group_id:
    g_id = st.session_state["active_student_group_id"]
    g_name = st.session_state["active_student_group_name"]
    c_id = st.session_state["active_student_course_id"]
    c_label = st.session_state["active_student_course_label"]
    
    with st.container(border=True):
        st.success(f"🟢 Verified: Team **'{g_name}'** logged into course track: `{c_label}`")
        
        # Real-Time Operational Data Fetch Triggers
        open_slots_list = []
        pres_types_list = []
        
        try:
            conn = get_mysql_connection()
            with conn.cursor() as cursor:
                # Query open calendar tracks based on your tinyint dateTaken = 0 parameter setting
                cursor.execute("SELECT pres_dateID, presDate FROM presentationdate WHERE courseID = %s AND dateTaken = 0 ORDER BY presDate ASC", (int(c_id),))
                open_slots_list = cursor.fetchall()
                
                # Dynamic Query fetching from presentationType table using your exact field 'ptypeTitle'
                cursor.execute("SELECT ptypeTitle FROM presentationType ORDER BY ptypeTitle ASC")
                types_data = cursor.fetchall()
                pres_types_list = [t["ptypeTitle"] for t in types_data] if types_data else ["Standard Presentation"]
            conn.close()
        except Exception as data_err:
            st.warning(f"Metadata synchronizer warning: {data_err}")
            pres_types_list = ["Standard Presentation"]

        st.markdown("### 📊 Presentation Specifications")
        selected_type = st.selectbox("Select Presentation Type *", options=pres_types_list, key="pres_type_selector_widget")
        
        if st.button("💡 Describe Presentation Type", use_container_width=True):
            with st.spinner(f"AI compiling parameters for type '{selected_type}'..."):
                describe_prompt = f"You are helping students quickly understand a selected presentation type.\nIn 80–120 words, provide:\n- A concise definition of the presentation type \"{selected_type}\".\n- 3–5 bullet examples of situations where it is well-suited.\n\nGuidelines:\n- Be neutral, academic, and clear.\n- Use short sentences.\n- Avoid fluff.\n- Return simple HTML with <p> and <ul><li> bullets (no external links, no scripts)."
                type_description_html = query_huggingface_llm(describe_prompt)
                st.info(f"📖 **About Type: {selected_type}**")
                st.markdown(type_description_html, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### 📅 Choose a Presentation Slot")
        
        if not open_slots_list:
            st.warning("⚠️ Scheduling Restricted: There are currently no open date slots remaining for this course section track.")
        else:
            slot_options = {f"{s['presDate'].strftime('%A, %B %d, %Y')} - (ID: {s['pres_dateID']})": s['pres_dateID'] for s in open_slots_list}
            selected_slot_label = st.selectbox("Choose an Available Calendar Presentation Slot *", options=list(slot_options.keys()))
            target_date_id = slot_options[selected_slot_label]
            
            st.markdown("---")
            st.markdown("##### 📝 Topic Scope Declaration")
            topic_title = st.text_input("Presentation Topic / Title Name *", placeholder="e.g., Implementing LLMs via Streamlit Frameworks")
            topic_abstract = st.text_area("Provide a Short Abstract / Overview summary", placeholder="Provide a brief explanation of your topic scope here...")
            
            if st.button("🔍 Check Topic Fit", use_container_width=True):
                if not topic_title or not topic_abstract:
                    st.error("Please enter a title and description before executing AI feedback.")
                else:
                    with st.spinner("AI engine checking alignment with course syllabus parameters..."):
                        try:
                            conn = get_mysql_connection()
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
            if st.button("🔒 Lock in Presentation Slot & Confirm Selection", use_container_width=True):
                if not topic_title:
                    st.error("You must fill out your Presentation Topic Title to secure your reservation.")
                else:
                    try:
                        conn = get_mysql_connection()
                        with conn.cursor() as cursor:
                            # Claim calendar record slot track using your exact tinyint field configuration settings
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
        st.markdown("---")
