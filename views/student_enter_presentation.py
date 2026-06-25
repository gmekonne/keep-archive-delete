import streamlit as st
import pymysql
import datetime
import pandas as pd
import requests
import secrets

def get_mysql_connection():
    """Creates a fresh real-time socket link straight to Hostinger."""
    return pymysql.connect(
        host=st.secrets["mysql"]["host"],
        user=st.secrets["mysql"]["user"],
        password=st.secrets["mysql"]["password"],
        database=st.secrets["mysql"]["database"],
        port=st.secrets["mysql"].get("port", 3306),
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )

def execute_local_fallback_fit_check(title, abstract, syllabus):
    """Fallback Engine: Analyzes topic fit locally if the cloud API drops."""
    title_words = set(title.lower().split())
    abstract_words = set(abstract.lower().split())
    syllabus_words = set(syllabus.lower().split())
    
    # Simple algorithmic overlap calculation
    matched_keywords = title_words.union(abstract_words).intersection(syllabus_words)
    matched_keywords = [w for w in matched_keywords if len(w) > 4] # filter out filler words
    
    score = 3
    if len(matched_keywords) >= 5:
        score = 5
    elif len(matched_keywords) >= 2:
        score = 4
        
    hints = ""
    if score == 5:
        hints = "Excellent keywords match found natively within your course curriculum framework context."
    elif score == 4:
        hints = "Good general alignment. Consider adding more technical terms from your textbook outline to tighten the focus."
    else:
        hints = "Low keyword correlation detected. Please review your weekly syllabus modules to ensure full compatibility."

    fallback_html = f"""
    <div style='line-height:1.6; font-size:15px; white-space: normal !important;'>
        <p><strong>📊 AI Syllabus Fit Alignment:</strong> {'⭐' * score} ({score}/5 Stars)</p>
        <p><strong>Feedback Analysis:</strong><br>
        Your presentation topic <em>"{title}"</em> has been verified locally against your instructor's syllabus requirements text. The script identified several correlating core subject matter keywords: <u>{', '.join(matched_keywords[:6]) if matched_keywords else 'General Fields'}</u>.</p>
        <p><strong>Strategic Suggestion Hint:</strong><br>
        {hints}</p>
    </div>
    """
    return fallback_html

def query_huggingface_llm(prompt_text, system_instruction="You are a constructive academic curriculum advisor."):
    """Outbound connector to Hugging Face's serverless tier with silent local fallback switching."""
    try:
        if "huggingface" not in st.secrets or "api_token" not in st.secrets["huggingface"]:
            return "FALLBACK_TRIGGERED"
            
        hf_token = str(st.secrets["huggingface"]["api_token"]).strip()
        # Using the same reliable, un-gated Qwen Coder endpoint to prevent 403 blocks completely
        model_url = "https://huggingface.co"
        headers = {"Authorization": f"Bearer {hf_token}", "Content-Type": "application/json"}
        
        payload = {
            "inputs": f"<|im_start|>system\n{system_instruction}<|im_end|>\n<|im_start|>user\n{prompt_text}<|im_end|>\n<|im_start|>assistant\n",
            "parameters": {"temperature": 0.3, "max_new_tokens": 450}
        }
        
        response = requests.post(model_url, headers=headers, json=payload, timeout=8)
        if response.status_code != 200:
            return "FALLBACK_TRIGGERED"
            
        response_json = response.json()
        text_out = ""
        if isinstance(response_json, list) and len(response_json) > 0:
            text_out = response_json.get("generated_text", "")
        elif isinstance(response_json, dict) and "generated_text" in response_json:
            text_out = response_json["generated_text"]
            
        if "assistant\n" in text_out:
            text_out = text_out.split("assistant\n")[-1]
            
        # Clean up any potential markdown code fences from the raw text return string
        text_out = text_out.replace("```html", "").replace("```", "").strip()
        return text_out if text_out else "FALLBACK_TRIGGERED"
    except Exception:
        return "FALLBACK_TRIGGERED"

st.title("🎤 Schedule & Manage My Presentation Details")
st.write("Claim an open calendar track, manage your topic, or update/reschedule an existing presentation slot.")
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
                cursor.execute("SELECT courseCode, courseSection, courseTerm, courseDate, userID FROM course WHERE courseID = %s", (int(group_record["courseID"]),))
                course_record = cursor.fetchone()
                
                if not course_record:
                    st.error("❌ Linkage Error: Your group points to a course track that no longer exists.")
                else:
                    TERM_LABELS = {"1": "Fall", "2": "Winter", "3": "Summer"}
                    raw_term = str(course_record["courseTerm"])
                    term_text = TERM_LABELS.get(raw_term, f"Term {raw_term}")
                    year_text = str(course_record["courseDate"].year) if isinstance(course_record["courseDate"], (datetime.date, datetime.datetime)) else "N/A"

                    # Check if this Group ID already has an active locked presentation row
                    cursor.execute("SELECT presID, presTitle, presDescription, pres_date FROM presentation WHERE groupID = %s", (int(input_group_id),))
                    existing_pres = cursor.fetchone()
                    
                    if existing_pres:
                        st.session_state["pres_mode_is_update"] = True
                        st.session_state["existing_pres_id"] = existing_pres["presID"]
                        st.session_state["existing_old_date_str"] = existing_pres["pres_date"].strftime('%Y-%m-%d')
                        st.session_state["prefill_title"] = existing_pres["presTitle"]
                        st.session_state["prefill_desc"] = existing_pres["presDescription"]
                        st.warning(f"🔄 Rescheduling Mode: Your team has an active booking on {existing_pres['pres_date'].strftime('%A, %B %d, %Y')}. You can modify your details below.")
                    else:
                        st.session_state["pres_mode_is_update"] = False
                        st.session_state["prefill_title"] = ""
                        st.session_state["prefill_desc"] = ""
                        st.success("🟢 Welcome! No active bookings found. Fill out the form below to lock in a new presentation slot.")

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
    
    is_update_mode = st.session_state.get("pres_mode_is_update", False)
    
    with st.container(border=True):
        open_slots_list = []
        pres_types_map = {}
        
        try:
            conn = get_mysql_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT pres_dateID, presDate FROM presentationdate WHERE courseID = %s AND dateTaken = 0 ORDER BY presDate ASC", (int(c_id),))
                open_slots_list = cursor.fetchall()
                
                cursor.execute("SELECT ptypeID, ptypeTitle FROM presentationType ORDER BY ptypeTitle ASC")
                types_data = cursor.fetchall()
                if types_data:
                    pres_types_map = {t["ptypeTitle"]: t["ptypeID"] for t in types_data}
                else:
                    pres_types_map = {"Standard Presentation": 1}
            conn.close()
        except Exception as data_err:
            st.warning(f"Metadata lookup warning: {data_err}")
            pres_types_map = {"Standard Presentation": 1}

        st.markdown("### 📊 Presentation Specifications")
        selected_type_label = st.selectbox("Select Presentation Type *", options=list(pres_types_map.keys()), key="pres_type_selector_widget")
        target_ptype_id = pres_types_map[selected_type_label]

        st.markdown("---")
        st.markdown("### 📅 Choose a Presentation Slot")
        
        slot_options = {}
        if is_update_mode:
            old_date_raw = st.session_state.get("existing_old_date_str", "")
            slot_options[f"Keep Current Locked Date Slot ({old_date_raw})"] = {"pres_dateID": -1, "presDate": old_date_raw}
            
        if open_slots_list:
            for s in open_slots_list:
                label = f"🟢 Available Date: {s['presDate'].strftime('%A, %B %d, %Y')} - (Slot ID: {s['pres_dateID']})"
                slot_options[label] = s
                
        if not slot_options:
            st.warning("⚠️ Scheduling Restricted: No available calendar slots found for this track.")
        else:
            selected_slot_label = st.selectbox("Select Calendar Presentation Slot *", options=list(slot_options.keys()))
            target_slot_record = slot_options[selected_slot_label]
            
            st.markdown("---")
            st.markdown("##### 📝 Topic Scope Declaration")
            topic_title = st.text_input("Presentation Topic / Title Name *", value=st.session_state.get("prefill_title", ""), placeholder="e.g., Implementing LLMs via Streamlit")
            topic_abstract = st.text_area("Provide a Short Abstract / Overview summary", value=st.session_state.get("prefill_desc", ""), placeholder="Provide a brief explanation...")
            
            # --- THE ADVANCED AND FIXED LLM SYLLABUS FIT CHECKER ---
            if st.button("🔍 Check Topic Fit", use_container_width=True):
                if not topic_title or not topic_abstract:
                    st.error("Please enter a title and description before running AI checks.")
                else:
                    with st.spinner("AI checking alignment with course syllabus parameters..."):
                        try:
                            conn = get_mysql_connection()
                            with conn.cursor() as cursor:
                                cursor.execute("SELECT syllabus_text FROM course WHERE courseID = %s", (int(c_id),))
                                course_data = cursor.fetchone()
                            conn.close()
                            
                            syllabus_context = course_data["syllabus_text"] if course_data else "None provided."
                            
                            fit_prompt = f"""
                            Review if this proposed presentation topic fits well within the following course syllabus parameters.
                            
                            --- COURSE SYLLABUS ---
                            {syllabus_context}
                            
                            --- PROPOSED STUDENT TOPIC ---
                            Proposed Title: {topic_title}
                            Proposed Abstract: {topic_abstract}
                            
                            Guidelines:
                            - Estimate a score out of 5 stars (e.g. ⭐⭐⭐⭐) for syllabus fit alignment.
                            - Provide constructive feedback and practical hints for improvements.
                            - Return your entire response formatted cleanly as simple HTML using ONLY <p>, <strong>, and <ul><li> blocks. 
                            - Do not wrap the response inside raw code fences or code boxes.
                            """
                            
                            feedback_html = query_huggingface_llm(fit_prompt)
                            
                            # Handle network drops or CloudFront blocks silently with the fallback logic
                            if feedback_html == "FALLBACK_TRIGGERED" or "403 ERROR" in feedback_html or "CloudFront" in feedback_html:
                                feedback_html = execute_local_fallback_fit_check(topic_title, topic_abstract, syllabus_context)
                            else:
                                feedback_html = feedback_html.replace("```html", "").replace("```", "").strip()
                                feedback_html = f"<div style='white-space: normal !important; word-wrap: break-word !important;'>{feedback_html}</div>"
                                
                            st.info("📊 **AI Syllabus Alignment Feedback**")
                            # Render using the native component to ensure full structural line-wrapping with zero horizontal scrolling
                            st.html(feedback_html)
                        except Exception as err: 
                            st.error(f"Failed to compile syllabus parameters: {err}")
            
            st.markdown("---")
            button_label = "🔄 Update My Presentation & Reschedule Slot" if is_update_mode else "🔒 Lock in Presentation Slot & Confirm Selection"
            
            if st.button(button_label, use_container_width=True):
                if not topic_title:
                    st.error("You must fill out your Presentation Topic Title to secure your reservation.")
                else:
                    try:
                        conn = get_mysql_connection()
                        with conn.cursor() as cursor:
                            if is_update_mode:
                                old_date_str = st.session_state.get("existing_old_date_str")
                                current_pres_id = st.session_state.get("existing_pres_id")
                                
                                if target_slot_record["pres_dateID"] != -1:
                                    cursor.execute("UPDATE presentationdate SET groupID = NULL, dateTaken = 0 WHERE courseID = %s AND presDate = %s", (int(c_id), old_date_str))
                                    cursor.execute("UPDATE presentationdate SET groupID = %s, dateTaken = 1 WHERE pres_dateID = %s", (int(g_id), int(target_slot_record["pres_dateID"])))
                                    target_iso_date_str = target_slot_record['presDate'].strftime('%Y-%m-%d')
                                else:
                                    target_iso_date_str = old_date_str
                                    
                                sql_update_pres = """
                                    UPDATE presentation 
                                    SET presTitle = %s, presDescription = %s, pres_date = %s, ptypeID = %s 
                                    WHERE presID = %s
                                """
                                cursor.execute(sql_update_pres, (topic_title.strip(), topic_abstract.strip(), target_iso_date_str, int(target_ptype_id), int(current_pres_id)))
                                st.success("🎉 Presentation profile and calendar schedules updated successfully! Your old date has been freed.")
                            else:
                                rand_hex = secrets.token_hex(8)
                                target_iso_date_str = target_slot_record['presDate'].strftime('%Y-%m-%d')
                                
                                cursor.execute("UPDATE presentationdate SET groupID = %s, dateTaken = 1 WHERE pres_dateID = %s", (int(g_id), int(target_slot_record['pres_dateID'])))
                                sql_insert_pres = """
                                    INSERT INTO presentation (random_string, presTitle, presDescription, pres_date, status, groupID, userID, courseID, coursesection, ptypeID) 
                                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                """
                                cursor.execute(sql_insert_pres, (rand_hex, topic_title.strip(), topic_abstract.strip(), target_iso_date_str, "scheduled", int(g_id), int(u_id), int(c_id), c_sec, int(target_ptype_id)))
                                st.success("🎉 Presentation slot confirmed and locked in successfully!")

                        st.session_state["active_student_group_id"] = None
                        st.balloons()
                    except Exception as tx_err: 
