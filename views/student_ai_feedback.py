import streamlit as st
import pymysql
import datetime
import requests

def get_mysql_connection():
    """Establishes a real-time uncached connection straight to Hostinger."""
    return pymysql.connect(
        host=st.secrets["mysql"]["host"],
        user=st.secrets["mysql"]["user"],
        password=st.secrets["mysql"]["password"],
        database=st.secrets["mysql"]["database"],
        port=st.secrets["mysql"].get("port", 3306),
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )

def query_huggingface_llm(prompt_text, system_instruction="You are an expert university presentation evaluator."):
    """Outbound payload connector to Hugging Face's free serverless inference tier."""
    try:
        if "huggingface" not in st.secrets or "api_token" not in st.secrets["huggingface"]:
            return "<p style='color:orange;'>⚠️ Configuration Error: Hugging Face api_token is missing from your secrets panel.</p>"
            
        hf_token = str(st.secrets["huggingface"]["api_token"]).strip()
        
        # 🟢 CHANGED ENDPOINT: Swapped to an un-gated, highly available model to instantly bypass 403 license blocks
        model_url = "https://huggingface.co"
        headers = {"Authorization": f"Bearer {hf_token}", "Content-Type": "application/json"}
        
        payload = {
            "inputs": f"<|im_start|>system\n{system_instruction}<|im_end|>\n<|im_start|>user\n{prompt_text}<|im_end|>\n<|im_start|>assistant\n",
            "parameters": {"temperature": 0.3, "max_new_tokens": 500}
        }
        
        response = requests.post(model_url, headers=headers, json=payload, timeout=25)
        
        if response.status_code == 403:
            return f"<p style='color:orange;'>⚠️ Hugging Face Block (403): The token works, but this specific model path requires account-level permissions. Details: {response.text}</p>"
        elif response.status_code != 200:
            return f"<p style='color:orange;'>⚠️ AI Processor Notice: Server returned status {response.status_code}. Details: {response.text}</p>"
            
        response_json = response.json()
        if isinstance(response_json, list) and len(response_json) > 0:
            text_out = response_json[0].get("generated_text", "")
            if "assistant\n" in text_out:
                text_out = text_out.split("assistant\n")[-1]
            return text_out
        elif isinstance(response_json, dict) and "generated_text" in response_json:
            return response_json["generated_text"]
        return str(response_json)
    except Exception as e:
        return f"<p style='color:red;'>❌ AI engine processing is temporarily offline: {e}</p>"

st.title("🤖 AI-Generated Presentation Synthesis & Feedback")
st.write("Leverage advanced language models to synthesize peer review data into structured improvement hints.")
st.markdown("---")

# 1. User Identity Lookup Panel Interface
input_group_id = st.number_input("Enter your Group ID *", min_value=1, step=1, key="student_ai_synthesis_lookup")

if st.button("Generate My AI Feedback Analysis", use_container_width=True):
    try:
        conn = get_mysql_connection()
        with conn.cursor() as cursor:
            # Step 1: Resolve Group to fetch presentation keys
            sql_check = """
                SELECT p.presID, p.presTitle, g.groupName 
                FROM presentation p
                JOIN presentationgroup g ON p.groupID = g.groupID
                WHERE p.groupID = %s 
                ORDER BY p.presID DESC LIMIT 1
            """
            cursor.execute(sql_check, (int(input_group_id),))
            pres_meta = cursor.fetchone()
            
            if not pres_meta:
                st.error(f"❌ Record Error: No evaluated presentation rows found matching Group ID '{input_group_id}'.")
                st.session_state["ai_eval_ready"] = False
            else:
                p_id = pres_meta["presID"]
                
                # Step 2: Calculate numeric average and group all raw peer comments text rows
                cursor.execute("SELECT FORMAT(AVG(rating_number), 1) as avg_score, COUNT(rating_number) as total_votes FROM rating WHERE presentation_id = %s", (int(p_id),))
                metrics = cursor.fetchone()
                
                cursor.execute("SELECT feedback FROM rating WHERE presentation_id = %s AND feedback IS NOT NULL", (int(p_id),))
                comments_data = cursor.fetchall()
                comments_list = [f"- {c['feedback'].strip()}" for c in comments_data if c['feedback'].strip() and c['feedback'].lower() != "none"]
                
                # Cache the results to session memory strings safely
                st.session_state["ai_eval_ready"] = True
                st.session_state["ai_eval_gid"] = input_group_id
                st.session_state["ai_eval_gname"] = pres_meta["groupName"]
                st.session_state["ai_eval_title"] = pres_meta["presTitle"]
                st.session_state["ai_eval_score"] = metrics["avg_score"] if metrics["avg_score"] else "0.0"
                st.session_state["ai_eval_count"] = metrics["total_votes"] if metrics["total_votes"] else 0
                st.session_state["ai_eval_comments"] = "\n".join(comments_list) if comments_list else "No text comments provided."
                st.rerun()
        conn.close()
    except Exception as server_err:
        st.error(f"Failed to query baseline data tracks: {server_err}")
# 2. Rendering and LLM Synthesis Phase: Runs after data matrices are loaded
if "ai_eval_ready" in st.session_state and st.session_state["ai_eval_ready"] and st.session_state["ai_eval_gid"] == input_group_id:
    g_name = st.session_state["ai_eval_gname"]
    p_title = st.session_state["ai_eval_title"]
    avg_score = st.session_state["ai_eval_score"]
    total_votes = st.session_state["ai_eval_count"]
    peer_comments_raw = st.session_state["ai_eval_comments"]
    
    st.success(f"🟢 Synchronized: Review dataset compiled for Team **'{g_name}'**.")
    
    # Render short numeric metrics summary card row
    col1, col2 = st.columns(2)
    with col1: st.metric(label="Calculated Rater Average Score", value=f"★ {avg_score} / 5.0")
    with col2: st.metric(label="Total Classroom Evaluators Count", value=str(total_votes))
    
    st.markdown("---")
    
    if int(total_votes) == 0:
        st.info("⏳ Awaiting Classroom Evaluations: No evaluations have been submitted for your presentation yet. AI processing requires logged peer data to run.")
    else:
        with st.spinner("🤖 AI Engine analyzing text feedback logs and synthesizing suggestions..."):
            # Construct the comprehensive prompt payload for the AI model
            ai_prompt = f"""
            Analyze the following presentation metrics data and peer reviews to compile a structured, constructive evaluation report card for the student group.
            
            --- PERFORMANCE METRICS ---
            Team Name: {g_name}
            Presentation Title: {p_title}
            Average Star Rating Score: {avg_score} out of 5 stars
            Total Peer Evaluators: {total_votes}
            
            --- RAW PEER FEEDBACK COMMENTS ---
            {peer_comments_raw}
            
            --- CRITICAL STRUCTURE INSTRUCTIONS ---
            Provide your response formatted cleanly as simple HTML (using only <p>, <strong>, and <ul><li> blocks). Your report MUST be concise and explicitly divided into exactly three sections:
            1. **Introduction**: Acknowledge the topic, the overall classroom performance, and summarize the general atmosphere of the evaluation dataset.
            2. **Content / Improvement Hints**: Synthesize the peer comments to deliver 3-4 highly specific, actionable suggestions/hints for next time (focus on slide layouts, voice clarity, pacing, or structure based on the feedback entries).
            3. **Conclusion**: Provide an encouraging, academically sound summary statement to guide the team forward.
            
            Do not include raw markdown symbols, external links, scripts, or meta headers in your response string. Start your response directly with the HTML blocks.
            """
            
            # Execute outbound web transaction payload call
            ai_synthesis_report_html = query_huggingface_llm(ai_prompt, "You are a professional university curriculum academic development advisor.")
            
            # Render output directly inside a responsive information card block layout
            st.info("📊 **AI Strategic Presentation Evaluation Report**")
            st.markdown(ai_synthesis_report_html, unsafe_allow_html=True)
            
    st.markdown("---")
