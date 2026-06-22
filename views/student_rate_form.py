import streamlit as st
import pymysql
import datetime
import requests

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



def get_visitor_public_ip():
    """Extracts the student's authentic public IP address natively from Streamlit server connection headers."""
    try:
        # Accesses the raw context headers sent by the visitor's browser tab session
        ctx_headers = st.context.headers
        
        # Standard proxy headers used by cloud providers to pass the true client IP
        if "X-Forwarded-For" in ctx_headers:
            # Splits any proxy chains and grabs the true origin visitor IP address text string cleanly
            return str(ctx_headers["X-Forwarded-For"]).split(",")[0].strip()
        elif "X-Real-IP" in ctx_headers:
            return str(ctx_headers["X-Real-IP"]).strip()
        else:
            return "127.0.0.1"
    except Exception:
        return "127.0.0.1"

st.title("⭐ Rate Current Presentation")
st.write("Secure Evaluation Portal • Authenticated via anonymous URL routing keys.")
st.markdown("---")


# Capture the postID parameter from the URL bar automatically
url_params = st.query_params

if "postID" in url_params:
    target_key = str(url_params["postID"]).strip()
    presentation_meta = None
    
    try:
        conn = get_mysql_connection()
        with conn.cursor() as cursor:
            # Query 1: Use randomized string to get presentation details
            sql_pres = """
                SELECT presID, ptypeID, courseID, groupID, presTitle, presDescription 
                FROM presentation 
                WHERE random_string = %s AND status = 'scheduled'
            """
            cursor.execute(sql_pres, (target_key,))
            presentation_meta = cursor.fetchone()
        conn.close()
    except Exception as err:
        st.error(f"Failed to authenticate routing key: {err}")

    if not presentation_meta:
        st.warning("⚠️ Invalid Access Key: No active presentation found matching this key.")
    else:
        st.subheader(f"🎤 Presentation: {presentation_meta['presTitle']}")
        st.caption(f"**Abstract:** {presentation_meta['presDescription']}")
        st.markdown("---")
        
        st.caption("(*Write your optional feedback before selecting a star)")
        peer_feedback = st.text_area("Write feedback (optional)", placeholder="Type constructive feedback pointers here...")
        
        star_selection = st.radio(
            "Select Evaluation Star Rating Metric *",
            options=[1, 2, 3, 4, 5],
            index=4,
            horizontal=True
        )
        
        # Display the rubric descriptions
        with st.expander("📖 Review Quality Rubric Guidelines", expanded=True):
            st.markdown("""
            <div style="line-height:1.6; font-size:14px;">
                <p><strong>★ 1 Star:</strong> The presentation was poorly organized and lacked clarity.</p>
                <p><strong>★★ 2 Stars:</strong> The presentation was somewhat clear but had significant issues and was difficult to follow.</p>
                <p><strong>★★★ 3 Stars:</strong> The presentation was average, with clear moments but also noticeable areas for improvement.</p>
                <p><strong>★★★★ 4 Stars:</strong> The presentation was well-organized and clear, with minor areas that could be improved.</p>
                <p><strong>★★★★★ 5 Stars:</strong> The presentation was exceptional, highly engaging, and very well-organized.</p>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("---")
        
        if st.button("Submit Presentation Rating", use_container_width=True):
            user_ip = get_visitor_public_ip()
            current_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            p_id = presentation_meta["presID"]
            pt_id = presentation_meta["ptypeID"]
            c_id = presentation_meta["courseID"]
            g_id = presentation_meta["groupID"]
            
            try:
                conn = get_mysql_connection()
                with conn.cursor() as cursor:
                    # Check if the user already submitted a rating from this IP (Duplicate Check)
                    cursor.execute("SELECT rating_number FROM rating WHERE presentation_id = %s AND user_ip = %s", (int(p_id), user_ip))
                    already_voted = cursor.fetchone()
                    
                    if already_voted:
                        st.error("❌ You have already submitted a rating for this presentation.")
                    else:
                        # Insert rating directly into your 'rating' table matching your exact columns
                        sql_insert = """
                            INSERT INTO rating (presentation_id, rating_number, user_ip, submitted, ptypeID, courseID, groupID, feedback) 
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """
                        cursor.execute(sql_insert, (int(p_id), int(star_selection), user_ip, current_date, int(pt_id), int(c_id), int(g_id), peer_feedback.strip() if peer_feedback else "None"))
                        st.balloons()
                        st.success(f"Thanks! You gave **{presentation_meta['presTitle']}** a rating of {star_selection} stars.")
            except Exception as tx_err:
                st.error(f"Database error: {tx_err}")
else:
    st.error("Presentation to be evaluated has not been provided!")
    # Student Zone Workspace Routes
    st_create_acct = st.Page("views/student_create_account.py", title="👤 1. Create Student Account")
    st_enter_pres  = st.Page("views/student_enter_presentation.py", title="🎤 2. Enter Presentation")
    st_view_dates  = st.Page("views/student_view_dates.py", title="📅 3. View Presentation Dates")
    st_view_inst   = st.Page("views/student_view_instructions.py", title="📋 4. View Presentation Guidelines")
    st_view_rating = st.Page("views/student_view_ratings.py", title="⭐ 5. View Ratings & Feedback")
    st_view_guide  = st.Page("views/student_view_guide.py", title="📖 6. View Student Guide")
    st_enter_contrib = st.Page("views/student_enter_contribution.py", title="💡 7. Enter Class Contributions")
    st_ai_feedback = st.Page("views/student_ai_feedback.py", title="🤖 8. AI-Generated Feedback")
    
    # 🟢 ADD THIS NEW HIDDEN ROUTE: Defines the rating form but keeps it unlisted in the navigation menu dictionary below
    st_hidden_form = st.Page("views/student_rate_form.py", title="Hidden Form URL")

    pg = st.navigation({
        "Information Channel": [home_page],
        "Student Zone Workspace": [
            st_create_acct, st_enter_pres, st_view_dates, st_view_inst, 
            st_view_rating, st_view_guide, st_enter_contrib, st_ai_feedback
        ],
        "Instructor Executive Gate": [login_page, personal_reg, corporate_reg, reset_pass]
    })
    pg.run()
