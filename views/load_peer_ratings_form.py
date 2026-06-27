import streamlit as st
import pymysql
import datetime
import pandas as pd

def get_mysql_connection():
    """Fresh uncached link to keep Hostinger database connections open."""
    return pymysql.connect(
        host=st.secrets["mysql"]["host"],
        user=st.secrets["mysql"]["user"],
        password=st.secrets["mysql"]["password"],
        database=st.secrets["mysql"]["database"],
        port=st.secrets["mysql"].get("port", 3306),
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )

# Inherit active course context from the main dashboard workspace row
if "dash_course_sel_v2" in st.session_state:
    selected_course_code = st.session_state["dash_course_sel_v2"]
else:
    selected_course_code = "Selected Course"

st.subheader(f"📝 Peer Ratings Ledger: {selected_course_code}")
st.write("Review aggregate evaluation score averages and raw student text comments.")
st.markdown("---")

target_course_id = st.session_state.get("active_dashboard_last_cid", 0)

if target_course_id == 0:
    st.info("💡 Please select an active course code option from the dashboard calendar first.")
else:
    presentations_list = []
    try:
        conn = get_mysql_connection()
        with conn.cursor() as cursor:
            # Query Step 1: Fetch all presentations for this course that have received at least one rating
            sql_pres = """
                SELECT p.presID, p.presTitle, g.groupName,
                       FORMAT(AVG(r.rating_number), 1) as avg_score,
                       COUNT(r.rating_number) as total_votes
                FROM presentation p
                INNER JOIN presentationgroup g ON p.groupID = g.groupID
                INNER JOIN rating r ON p.presID = r.presentation_id
                WHERE p.courseID = %s
                GROUP BY p.presID, p.presTitle, g.groupName
                ORDER BY avg_score DESC
            """
            cursor.execute(sql_pres, (int(target_course_id),))
            presentations_list = cursor.fetchall()
        conn.close()
    except Exception as e:
        st.error(f"Failed to query peer evaluation matrix records: {e}")

    if not presentations_list:
        st.warning(f"ℹ️ No active peer evaluations or scores have been logged under course track '{selected_course_code}' yet.")
    else:
        st.success(f"📋 Found **{len(presentations_list)}** evaluated presentations!")
        
        # Create an options dictionary mapping titles to presentation IDs
        options_map = {f"🎤 {p['groupName']} - {p['presTitle']} (★ {p['avg_score']} from {p['total_votes']} votes)": p for p in presentations_list}
        selected_pres_label = st.selectbox("Select a presentation profile to inspect text comments:", options=list(options_map.keys()))
        
        # Extract metadata metrics for the selected item
        chosen_meta = options_map[selected_pres_label]
        target_pres_id = chosen_meta["presID"]
        
        st.markdown("---")
        st.markdown("### 💬 Qualitative Student Feedback Review Panel")
        
        comments_feed = []
        try:
            conn = get_mysql_connection()
            with conn.cursor() as cursor:
                # Query Step 2: Fetch all text comments and scores for the explicitly selected presentation
                sql_comments = """
                    SELECT rating_number, feedback, submitted, user_ip 
                    FROM rating 
                    WHERE presentation_id = %s 
                    ORDER BY submitted DESC
                """
                cursor.execute(sql_comments, (int(target_pres_id),))
                comments_feed = cursor.fetchall()
            conn.close()
        except Exception as err:
            st.error(f"Failed to extract text comments stream lines: {err}")
            
        if not comments_feed:
            st.info("No raw text comments were supplied for this presentation.")
        else:
            for item in comments_feed:
                score = int(item["rating_number"])
                feedback_text = str(item["feedback"]).strip()
                
                # Standarize timestamps cleanly
                raw_date = item["submitted"]
                formatted_date = raw_date.strftime("%B %d, %Y at %I:%M %p") if isinstance(raw_date, (datetime.date, datetime.datetime)) else str(raw_date)
                
                # Visual grouping badges based on evaluation tone
                badge = "🟢 High Mark" if score >= 4 else "🟡 Mid Mark" if score == 3 else "🔴 Low Mark"
                
                with st.container(border=True):
                    col_b1, col_b2 = st.columns([1, 4])
                    with col_b1:
                        st.markdown(f"**Score:** ★ **{score}** / 5")
                        st.caption(f"*{badge}*")
                    with col_b2:
                        st.markdown(f"💬 **Peer Critique Note:**\n\"{feedback_text}\"")
                        st.caption(f"⏱️ Timestamp Log: {formatted_date} • IP Trace: {item['user_ip']}")
    st.markdown("---")
