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

st.title("💡 My Classroom Engagement Contributions Log")
st.write("Input your System Assigned Group ID to audit your logged participation records and view transaction parameters.")
st.markdown("---")

# 1. User Input Control Board Panel Layout
input_group_id = st.number_input("Enter your Group ID *", min_value=1, step=1, key="contrib_view_group_lookup")

if st.button("Fetch My Contributions Index", use_container_width=True):
    try:
        conn = get_mysql_connection()
        with conn.cursor() as cursor:
            # Query Step 1: Scan table to find if any contribution entries exist matching this Group ID reference key
            sql_check = """
                SELECT contributionID, title 
                FROM contribution 
                WHERE groupID = %s 
                ORDER BY contributionID DESC
            """
            cursor.execute(sql_check, (int(input_group_id),))
            records = cursor.fetchall()
            
            if not records:
                # Fallback Step 1.2: Check if group exists but simply hasn't submitted a contribution asset yet
                cursor.execute("SELECT groupName FROM presentationgroup WHERE groupID = %s", (int(input_group_id),))
                group_exists = cursor.fetchone()
                
                if group_exists:
                    st.warning(f"⚠️ Team **'{group_exists['groupName']}'** is verified, but no participation records have been saved under your profile yet.")
                    st.info("💡 **Next Step:** Navigate to the **💡 7. Enter Class Contributions** tab to upload your first insight asset!")
                else:
                    st.error(f"❌ ID Not Found: No group matching ID '{input_group_id}' was located inside the system registry.")
                st.session_state["cached_contrib_list"] = None
            else:
                # Step 2: Cache parameters to memory map states safely
                st.session_state["cached_contrib_list"] = records
                st.session_state["active_contrib_lookup_gid"] = input_group_id
                st.rerun()
        conn.close()
    except Exception as e:
        st.error(f"Server data alignment pipeline exception: {e}")
# 2. Detail Rendering Layout Phase: Activates after validation state is cached
if "active_contrib_lookup_gid" in st.session_state and st.session_state["active_contrib_lookup_gid"] == input_group_id:
    contrib_index_list = st.session_state["cached_contrib_list"]
    
    if contrib_index_list:
        st.success(f"📋 Found **{len(contrib_index_list)}** saved participation entries under Group ID {input_group_id}!")
        
        # Build an clean dictionary mapping choice labels to their exact database primary key IDs
        options_map = {f"📌 {item['title']} (Record ID: {item['contributionID']})": item['contributionID'] for item in contrib_index_list}
        
        # User Selector Box
        selected_title_label = st.selectbox("Choose a contribution title track to audit details:", options=list(options_map.keys()))
        target_contrib_id = options_map[selected_title_label]
        
        # --- EXECUTE INDIVIDUAL SELECTION REAL-TIME ROW EXPANSION ---
        if st.button("👁️ View Full Contribution Details", use_container_width=True):
            try:
                conn = get_mysql_connection()
                with conn.cursor() as cursor:
                    # Query all row columns for this specific primary key ID
                    sql_row = """
                        SELECT title, contributionType, description, link, tags, contributionDate, grade 
                        FROM contribution 
                        WHERE contributionID = %s
                    """
                    cursor.execute(sql_row, (int(target_contrib_id),))
                    c_row = cursor.fetchone()
                    
                conn.close()
                
                if c_row:
                    # Format optional date parameters beautifully
                    raw_date = c_row["contributionDate"]
                    formatted_date = raw_date.strftime("%B %d, %Y") if isinstance(raw_date, (datetime.datetime, datetime.date)) else str(raw_date)
                    
                    # Grade Score Evaluation Handler
                    raw_grade = c_row["grade"]
                    grade_text = f"⭐ {raw_grade} Points" if raw_grade is not None else "⏳ Awaiting Instructor Grading"
                    
                    st.markdown("---")
                    # Visual summary container box layout
                    with st.container(border=True):
                        st.subheader(f"📝 Title: {c_row['title']}")
                        st.markdown(f"🗂️ **Participation Category Bucket:** `{c_row['contributionType']}`")
                        st.markdown("---")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"📅 **Submission Date Log:** {formatted_date}")
                            st.markdown(f"🏷️ **Instructor Tracking Tags:** *{c_row['tags']}*")
                        with col2:
                            st.markdown(f"🔗 **Web Asset URL Link:** [Click to Open Asset Destination]({c_row['link']})")
                            st.markdown(f"🏅 **Grading Roster Evaluation Ledger:** **{grade_text}**")
                            
                        st.markdown("---")
                        st.markdown(f"📖 **Detailed Insight / Message Content:**\n\n\"{c_row['description']}\"")
                else:
                    st.error("Transaction mismatch error: This record reference row is no longer live on Hostinger server nodes.")
            except Exception as row_err:
                st.error(f"Failed to query contribution row matrix: {row_err}")
                
    st.markdown("---")
