import streamlit as st
import pymysql
import datetime
import pandas as pd

def get_mysql_connection():
    """Creates a fresh uncached real-time socket link straight to Hostinger."""
    return pymysql.connect(
        host=st.secrets["mysql"]["host"],
        user=st.secrets["mysql"]["user"],
        password=st.secrets["mysql"]["password"],
        database=st.secrets["mysql"]["database"],
        port=st.secrets["mysql"].get("port", 3306),
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )

st.title("⭐ My Presentation Performance Ratings & Feedback")
st.write("Input your System Assigned Group ID to review your performance metrics and view anonymous peer comments.")
st.markdown("---")

# 1. User Input Field Panel Matrix
input_group_id = st.number_input("Enter your Group ID *", min_value=1, step=1, key="ratings_group_lookup_input")

if st.button("Fetch My Evaluation Profile", use_container_width=True):
    try:
        conn = get_mysql_connection()
        with conn.cursor() as cursor:
            # SQL Step 1: Verify the group exists and check if they have an active scheduled presentation profile row
            sql_check_pres = """
                SELECT p.presID, p.presTitle, p.presDescription, g.groupName 
                FROM presentation p
                JOIN presentationgroup g ON p.groupID = g.groupID
                WHERE p.groupID = %s 
                ORDER BY p.presID DESC LIMIT 1
            """
            cursor.execute(sql_check_pres, (int(input_group_id),))
            pres_meta = cursor.fetchone()
            
            if not pres_meta:
                # Secondary Fallback Check: Check if they are a group but simply haven't done their presentation task yet
                cursor.execute("SELECT groupName FROM presentationgroup WHERE groupID = %s", (int(input_group_id),))
                group_exists = cursor.fetchone()
                
                if group_exists:
                    st.warning(f"⚠️ Team **'{group_exists['groupName']}'** is registered, but no evaluation scores have been logged under your project track yet.")
                else:
                    st.error(f"❌ ID Not Found: No group matching ID '{input_group_id}' was located inside the classroom database registration matrices.")
                    
                st.session_state["active_ratings_pres_id"] = None
            else:
                # Cache parameters safely into session context state boundaries
                st.session_state["active_ratings_pres_id"] = pres_meta["presID"]
                st.session_state["active_ratings_title"] = pres_meta["presTitle"]
                st.session_state["active_ratings_group_name"] = pres_meta["groupName"]
                st.session_state["active_ratings_desc"] = pres_meta["presDescription"]
                st.session_state["active_ratings_lookup_gid"] = input_group_id
                st.rerun()
        conn.close()
    except Exception as e:
        st.error(f"Server data alignment pipeline exception: {e}")
# 2. Render Analytics Screen Phase: Activates after validation state is confirmed
if "active_ratings_lookup_gid" in st.session_state and st.session_state["active_ratings_lookup_gid"] == input_group_id:
    p_id = st.session_state["active_ratings_pres_id"]
    p_title = st.session_state["active_ratings_title"]
    g_name = st.session_state["active_ratings_group_name"]
    p_desc = st.session_state["active_ratings_desc"]
    
    # Structural Parameter Initializers
    summary_metrics = {"total_votes": 0, "avg_score": "0.0"}
    raw_comments_feed = []
    
    try:
        conn = get_mysql_connection()
        with conn.cursor() as cursor:
            # Transaction 1: Compute real-time aggregated averages over the rating database table layers
            sql_summary = """
                SELECT COUNT(rating_number) as total_votes,
                       FORMAT(AVG(rating_number), 1) as avg_score
                FROM rating
                WHERE presentation_id = %s
                GROUP BY presentation_id
            """
            cursor.execute(sql_summary, (int(p_id),))
            summary_res = cursor.fetchone()
            if summary_res:
                summary_metrics = summary_res
                
            # Transaction 2: Pull detailed textual student feedback commentaries
            sql_comments = """
                SELECT rating_number, feedback, submitted 
                FROM rating 
                WHERE presentation_id = %s
                ORDER BY submitted DESC
            """
            cursor.execute(sql_comments, (int(p_id),))
            raw_comments_feed = cursor.fetchall()
        conn.close()
    except Exception as fetch_err:
        st.error(f"Failed to compile rating metrics data streams: {fetch_err}")

    # UI Visual Generation Block Elements
    st.success(f"📊 Evaluation metrics compiled successfully for team **'{g_name}'**!")
    
    with st.container(border=True):
        st.subheader(f"🎤 Topic Track: {p_title}")
        st.caption(f"**Abstract:** {p_desc}")
        st.markdown("---")
        
        # Display the primary scalar math metrics rows
        m_col1, m_col2 = st.columns(2)
        with m_col1:
            st.metric(label="Calculated Performance Rating Average", value=f"★ {summary_metrics['avg_score']} / 5.0")
        with m_col2:
            st.metric(label="Total Peer Evaluations Submitted", value=str(summary_metrics["total_votes"]))

    st.markdown("---")
    st.markdown("### 💬 Anonymous Peer Evaluation Feed Entries")
    
    if not raw_comments_feed:
        st.info("ℹ️ No qualitative commentary reviews have been processed by your classmates yet.")
    else:
        # Loop through every individual feedback row and print inside clean card widgets
        for item in raw_comments_feed:
            # Format time strings beautifully: "June 22, 2026 at 07:12 PM"
            time_stamp_obj = item["submitted"]
            if isinstance(time_stamp_obj, (datetime.datetime, datetime.date)):
                formatted_time_str = time_stamp_obj.strftime("%B %d, %Y at %I:%M %p")
            else:
                formatted_time_str = str(time_stamp_obj)
                
            score_weight_val = int(item["rating_number"])
            feedback_text_val = str(item["feedback"]).strip()
            
            # Setup dynamic badge configurations to identify the visual tone of the review card row
            if score_weight_val >= 4:
                card_badge = "🟢 Strong Review"
            elif score_weight_val == 3:
                card_badge = "🟡 Average Review"
            else:
                card_badge = "🔴 Critique Review"
                
            with st.container(border=True):
                col_item1, col_item2 = st.columns([1, 3])
                with col_item1:
                    st.markdown(f"**Score:** ★ **{score_weight_val}** / 5")
                    st.caption(f"*{card_badge}*")
                with col_item2:
                    st.markdown(f"💬 **Feedback Critique Note:**\n\"{feedback_text_val}\"")
                    st.caption(f"⏱️ Submitted on: {formatted_time_str}")
    st.markdown("---")
