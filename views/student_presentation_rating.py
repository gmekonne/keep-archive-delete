import streamlit as st
import pymysql
import datetime
import requests

def get_mysql_connection():
    """Creates a fresh uncached socket connection straight to Hostinger."""
    return pymysql.connect(
        host=st.secrets["mysql"]["host"],
        user=st.secrets["mysql"]["user"],
        password=st.secrets["mysql"]["password"],
        database=st.secrets["mysql"]["database"],
        port=st.secrets["mysql"].get("port", 3306),
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )

def get_visitor_public_ip():
    """Fetches the student's authentic public IP address to match REMOTE_ADDR constraints."""
    try:
        return requests.get("https://ipify.org", timeout=3).text.strip()
    except Exception:
        return "127.0.0.1"

st.title("⭐ Live Presentation Rating & Feedback Channel")
st.write("Secure Evaluation Portal • Authenticated via anonymous URL routing keys.")
st.markdown("---")

# 1. Capture the randomized link string parameter (Simulates $_GET['postID'])
# url_routing_string = st.text_input("Paste Presentation Secure Key (postID) *", placeholder="e.g., yzj3o8nuxeva")
# =====================================================================
# DYNAMIC GET CONSOLE: SNIFF KEY DIRECTLY FROM THE BROWSER URL BAR
# =====================================================================
# Simulates your exact PHP $_GET['postID'] logic natively in Python
url_params = st.query_params

if "postID" in url_params:
    # Automatically extracts '49973ed8fabefc8e' right out of the incoming link path
    url_routing_string = str(url_params["postID"]).strip()
else:
    # Fallback text input drawer in case a user lands on the page without an entry key
    url_routing_string = st.text_input("Paste Presentation Secure Key (postID) *", placeholder="e.g., 49973ed8fabefc8e")

if url_routing_string:
    target_key = url_routing_string.strip()

    
    # Initialize variables for block scope extraction
    presentation_meta = None
    aggregated_metrics = {"rating_num": 0, "average_rating": "0.0"}
    
    try:
        conn = get_mysql_connection()
        with conn.cursor() as cursor:
            # Query Step 1: Resolve the randomized hash key to find the parent presentation rows
            sql_pres = """
                SELECT presID, ptypeID, courseID, groupID, presTitle, presDescription 
                FROM presentation 
                WHERE random_string = %s AND status = 'scheduled'
            """
            cursor.execute(sql_pres, (target_key,))
            presentation_meta = cursor.fetchone()
            
            if presentation_meta:
                p_id = presentation_meta["presID"]
                
                # Query Step 2: Fetch current aggregate metrics from your rating table (Simulates your PHP summary joins)
                sql_metrics = """
                    SELECT COUNT(rating_number) as rating_num, 
                           FORMAT((SUM(rating_number) / COUNT(rating_number)), 1) as average_rating 
                    FROM rating 
                    WHERE presentation_id = %s 
                    GROUP BY presentation_id
                """
                cursor.execute(sql_metrics, (int(p_id),))
                metrics_res = cursor.fetchone()
                if metrics_res:
                    aggregated_metrics = metrics_res
        conn.close()
    except Exception as err:
        st.error(f"Failed to securely authenticate tracking key pipeline: {err}")

    if not presentation_meta:
        st.warning("⚠️ Invalid Access Key: No scheduled presentation found matching that target parameters track on Hostinger.")
    else:
        # UI DISPLAY: Summary metrics card blocks layout
        m_col1, m_col2 = st.columns(2)
        with m_col1:
            st.metric(label="Current Running Score Average", value=f"★ {aggregated_metrics['average_rating']} / 5.0")
        with m_col2:
            st.metric(label="Total Submitted Peer Evaluations", value=str(aggregated_metrics["rating_num"]))
            
        with st.container(border=True):
            st.subheader(f"🎤 Active Target: {presentation_meta['presTitle']}")
            st.caption(f"**Description Scope Abstract:** {presentation_meta['presDescription']}")
        st.markdown("---")
        st.markdown("##### 📋 Peer Evaluation Input Dashboard")
        st.caption("(*Write your (optional) feedback before selecting a star)")
        
        # Form Layout Elements Rendering Setup
        peer_feedback_text = st.text_area("Write feedback (optional)", placeholder="Type constructive feedback pointers here...", key="peer_feedback_text_widget")
        
        # Array matching the exact horizontal 1-5 selection layout criteria
        star_selection = st.radio(
            "Select Evaluation Star Rating Metric *",
            options=[1, 2, 3, 4, 5],
            index=4, # Defaults selection indicator cursor on 5 stars natively
            horizontal=True,
            key="peer_star_radio_widget"
        )
        
        # HTML Rubric Cards matching your exact PHP framework paragraph strings
        with st.expander("📖 Review Quality Rubric Guideline Metrics Descriptions", expanded=True):
            st.markdown("""
            <div class="rating-box" style="line-height:1.6;">
                <p><strong>★ 1 Star:</strong> The presentation was poorly organized and lacked clarity.</p>
                <p><strong>★★ 2 Stars:</strong> The presentation was somewhat clear but had significant issues and was difficult to follow.</p>
                <p><strong>★★★ 3 Stars:</strong> The presentation was average, with clear moments but also noticeable areas for improvement.</p>
                <p><strong>★★★★ 4 Stars:</strong> The presentation was well-organized and clear, with minor areas that could be improved.</p>
                <p><strong>★★★★★ 5 Stars:</strong> The presentation was exceptional, highly engaging, and very well-organized.</p>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("---")
        
        # SUBMISSION TRANSACTION EXECUTION RUNNER (Simulates presentation_rater.php)
        if st.button("Submit Presentation Rating", use_container_width=True):
            # Capture environmental state parameters
            user_ip_str = get_visitor_public_ip()
            current_datetime_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            pres_id = presentation_meta["presID"]
            ptype_id = presentation_meta["ptypeID"]
            course_id = presentation_meta["courseID"]
            group_id = presentation_meta["groupID"]
            title_str = presentation_meta["presTitle"]
            
            try:
                conn = get_mysql_connection()
                with conn.cursor() as cursor:
                    # STEP 1: Duplicate Submission Protection Constraint Check (Simulates $query_one)
                    sql_check = "SELECT rating_number FROM rating WHERE presentation_id = %s AND user_ip = %s"
                    cursor.execute(sql_check, (int(pres_id), user_ip_str))
                    already_voted = cursor.fetchone()
                    
                    if already_voted:
                        # Status = 2 handling condition logic
                        st.error(f"❌ Submission Rejected: You have already submitted a peer rating evaluation for '{title_str}'.")
                    else:
                        # STEP 2: Write records straight into your exact rating column fields (Simulates $query_two)
                        sql_insert_rating = """
                            INSERT INTO rating 
                            (presentation_id, rating_number, user_ip, submitted, ptypeID, courseID, groupID, feedback) 
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """
                        cursor.execute(sql_insert_rating, (
                            int(pres_id),
                            int(star_selection),
                            user_ip_str,
                            current_datetime_str,
                            int(ptype_id),
                            int(course_id),
                            int(group_id),
                            peer_feedback_text.strip() if peer_feedback_text else "None"
                        ))
                        
                        # Status = 1 success alert tracking overwrite sequence (Simulates jQuery dynamic overwrite)
                        st.balloons()
                        st.success(f"🎉 Thanks! You gave **'{title_str}'** a rating of {star_selection} stars successfully.")
                        st.info("Your feedback metrics have been recorded directly to the instructor's ledger.")
                        
            except Exception as tx_err:
                st.error(f"Failed to record rating payload data row: {tx_err}")
