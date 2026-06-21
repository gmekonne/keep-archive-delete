import streamlit as st
import pymysql
import datetime
import pandas as pd
import requests
import secrets

def get_mysql_connection():
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
            "inputs": f"<|im_start|>system\n{system_instruction}<|im_end|>\n<|im_start|>user\n{prompt_text}<|im_end|>\n<|im_start|>assistant\n",
            "parameters": {"temperature": 0.3, "max_new_tokens": 400}
        }
        response = requests.post(model_url, headers=headers, json=payload, timeout=25)
        if response.status_code != 200:
            return f"<p style='color:orange;'>⚠️ AI server notice: {response.text}</p>"
        response_json = response.json()
        if isinstance(response_json, list) and len(response_json) > 0:
            text_out = response_json[0].get("generated_text", "")
            if "assistant\n" in text_out:
                text_out = text_out.split("assistant\n")[-1]
            return text_out
        elif isinstance(response_json, dict) and "generated_text" in response_json:
            return response_json["generated_text"]
        return "AI review processed successfully."
    except Exception as e:
        return f"AI processing temporarily offline: {e}"

st.title("🎤 Schedule & Enter My Presentation Details")
st.write("Input your System Assigned Group ID to review available calendar tracks and claim your slot.")
st.markdown("---")

input_group_id = st.number_input("Enter your Group ID *", min_value=1, step=1, key="pres_group_id_lookup")

if st.button("Fetch My Group & Course Details", use_container_width=True):
    try:
        conn = get_mysql_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT groupID, groupName, courseID FROM presentationgroup WHERE groupID = %s", (int(input_group_id),))
            group_record = cursor.fetchone()
            
            if not group_record:
                st.error(f"❌ Verification Failed: No registered group found matching ID '{input_group_id}'.")
                st.session_state["active_student_group_id"] = None
            else:
                # Fetch full data metrics including courseSection and parent userID
                cursor.execute("SELECT courseCode, courseSection, courseTerm, courseDate, userID FROM course WHERE courseID = %s", (int(group_record["courseID"]),))
                course_record = cursor.fetchone()
                
                if not course_record:
                    st.error("❌ Linkage Error: Your group points to a course track that no longer exists.")
                else:
                    TERM_LABELS = {"1": "Fall", "2": "Winter", "3": "Summer"}
                    raw_term = str(course_record["courseTerm"])
                    term_text = TERM_LABELS.get(raw_term, f"Term {raw_term}")
                    year_text = str(course_record["courseDate"].year) if isinstance(course_record["courseDate"], (datetime.date, datetime.datetime)) else "N/A"

                    st.session_state["active_student_group_id"] = group_record["groupID"]
                    st.session_state["active_student_group_name"] = group_record["groupName"]
                    st.session_state["active_student_course_id"] = group_record["courseID"]
                    st.session_state["active_student_course_label"] = f"{course_record['courseCode']} - Section {course_record['courseSection']} ({term_text} {year_text})"
                    st.session_state["active_student_course_section"] = course_record["courseSection"]
                    st.session_state["active_student_instructor_id"] = course_record["userID"]
                    st.rerun()
        conn.close()
    except Exception as e:
        st.error(f"Server lookup connection failure: {e}")
if "active_student_group_id" in st.session_state and st.session_state["active_student_group_id"] == input_group_id:
    g_id = st.session_state["active_student_group_id"]
    g_name = st.session_state["active_student_group_name"]
    c_id = st.session_state["active_student_course_id"]
    c_label = st.session_state["active_student_course_label"]
    c_sec = st.session_state["active_student_course_section"]
    u_id = st.session_state["active_student_instructor_id"]
    
    with st.container(border=True):
        st.success(f"🟢 Verified: Team **'{g_name}'** logged into course track: `{c_label}`")
        
        def fetch_open_dates(course_id):
            try:
                conn = get_mysql_connection()
                with conn.cursor() as cursor:
                    sql = "SELECT pres_dateID, presDate FROM presentationdate WHERE courseID = %s AND dateTaken = 0 ORDER BY presDate ASC"
                    cursor.execute(sql, (int(course_id),))
                    slots = cursor.fetchall()
                return slots
            except Exception: return []

        open_slots_list = fetch_open_dates(c_id)
        pres_types_list = ["Standard Pitch", "Case Defense", "Term Synthesis", "Thesis Review"]
        
        st.markdown("### 📊 Presentation Specifications")
        selected_type = st.selectbox("Select Presentation Type *", options=pres_types_list, key="pres_type_selector_widget")
        
        if st.button("💡 Describe Presentation Type", use_container_width=True):
            with st.spinner(f"AI compiling parameters for type '{selected_type}'..."):
                describe_prompt = f"Provide a brief academic overview definition of the presentation type \"{selected_type}\" with 3 context bullet examples formatted cleanly as simple HTML <p> and <ul><li> tags."
                type_description_html = query_huggingface_llm(describe_prompt)
                st.info(f"📖 **About Type: {selected_type}**")
                st.markdown(type_description_html, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### 📅 Choose a Presentation Slot")
        
        if not open_slots_list:
            st.warning("⚠️ Scheduling Restricted: There are currently no open date slots remaining for this course track.")
        else:
            slot_options = {f"{s['presDate'].strftime('%A, %B %d, %Y')} - (ID: {s['pres_dateID']})": s for s in open_slots_list}
            selected_slot_label = st.selectbox("Choose an Available Calendar Presentation Slot *", options=list(slot_options.keys()))
            target_slot_record = slot_options[selected_slot_label]
            target_date_id = target_slot_record['pres_dateID']
            target_iso_date_str = target_slot_record['presDate'].strftime('%Y-%m-%d')
            
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
                            
                            fit_prompt = f"Review if this proposed presentation topic fits well within the following course syllabus.\nSyllabus:\n{syllabus_context}\n\nProposed Title: {topic_title}\nAbstract: {topic_abstract}\n\nFormat feedback completely as simple HTML using <p> and <ul><li> tags."
                            feedback_html = query_huggingface_llm(fit_prompt, "You are a constructive academic curriculum advisor.")
                            st.info("📊 **AI Syllabus Alignment Feedback**")
                            st.markdown(feedback_html, unsafe_allow_html=True)
                        except Exception as err:
                            st.error(f"Failed to compile syllabus parameters: {err}")
            
            st.markdown("---")
            if st.button("🔒 Lock in Presentation Slot & Confirm Selection", use_container_width=True):
                if not topic_title:
                    st.error("You must fill out your Presentation Topic Title to secure your reservation.")
                else:
                    try:
                        # Generate unique hexadecimal string tracking parameter
                        rand_hex = secrets.token_hex(8)
                        
                        conn = get_mysql_connection()
                        with conn.cursor() as cursor:
                            # TRANSACTION 1: Update schedule slot table
                            sql_claim = "UPDATE presentationdate SET groupID = %s, dateTaken = 1 WHERE pres_dateID = %s"
                            cursor.execute(sql_claim, (int(g_id), int(target_date_id)))
                            
                            # TRANSACTION 2: Insert into presentation table using your exact fields
                            sql_insert_pres = """
                                INSERT INTO presentation 
                                (random_string, presTitle, presDescription, pres_date, status, groupID, userID, courseID, coursesection, ptypeID) 
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """
                            cursor.execute(sql_insert_pres, (
                                rand_hex, topic_title.strip(), topic_abstract.strip(), target_iso_date_str, 
                                "scheduled", int(g_id), int(u_id), int(c_id), c_sec, 1
                            ))
                            
                        st.session_state["active_student_group_id"] = None
                        st.success("🎉 Presentation confirmed! Your slots are now permanently locked in the presentation database matrix.")
                        st.balloons()
                    except Exception as tx_err:
                        st.error(f"Failed to submit calendar reservation: {tx_err}")
        st.markdown("---")
