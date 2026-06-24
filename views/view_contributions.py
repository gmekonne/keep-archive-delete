import streamlit as st
import pymysql
import datetime
import pandas as pd

def get_mysql_connection():
    """Fresh uncached connection to keep Hostinger firewalls open."""
    return pymysql.connect(
        host=st.secrets["mysql"]["host"],
        user=st.secrets["mysql"]["user"],
        password=st.secrets["mysql"]["password"],
        database=st.secrets["mysql"]["database"],
        port=st.secrets["mysql"].get("port", 3306),
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )

st.subheader("📈 Instructor Participation Audit Console")
st.write("Lookup, review, and input grades for student classroom contributions.")
st.markdown("---")

# FIXED: Set min_value=0 and value=0 so the input box starts completely blank/neutral
input_gid = st.number_input("Enter Group ID to Audit *", min_value=0, value=0, step=1, key="inst_contrib_lookup_gid")

# FIXED GUARD CONDITION: Only fires database query tracks if the instructor types a number greater than 0
if input_gid > 0:
    contrib_index_list = []
    group_name_str = "Unknown Team"
    
    try:
        conn = get_mysql_connection()
        with conn.cursor() as cursor:
            # Step 1.1: Grab group team name for context verification
            cursor.execute("SELECT groupName FROM presentationgroup WHERE groupID = %s", (int(input_gid),))
            g_rec = cursor.fetchone()
            if g_rec:
                group_name_str = g_rec["groupName"]
                
            # Step 1.2: Scan table for all contributions matched to this group
            sql_list = "SELECT contributionID, title, contributionType FROM contribution WHERE groupID = %s ORDER BY contributionID DESC"
            cursor.execute(sql_list, (int(input_gid),))
            contrib_index_list = cursor.fetchall()
        conn.close()
    except Exception as e:
        st.error(f"Failed to extract matching data rows: {e}")

    if not contrib_index_list:
        st.warning(f"ℹ️ No participation entries logged under Team **'{group_name_str}'** (ID: {input_gid}) yet.")
    else:
        st.success(f"📋 Found **{len(contrib_index_list)}** submissions for Team **'{group_name_str}'**")
        
        # Map choice text labels safely to their database auto-incremented primary keys
        options_map = {f"📌 [{item['contributionType']}] - {item['title']} (ID: {item['contributionID']})": item['contributionID'] for item in contrib_index_list}
        selected_label = st.selectbox("Select a contribution title track to audit & grade:", options=list(options_map.keys()))
        target_contrib_id = options_map[selected_label]
        
        st.markdown("---")
        
        # --- DYNAMIC DATA ROW EXPANSION & GRADING LOOPS ---
        try:
            conn = get_mysql_connection()
            with conn.cursor() as cursor:
                sql_row = "SELECT * FROM contribution WHERE contributionID = %s"
                cursor.execute(sql_row, (int(target_contrib_id),))
                c_data = cursor.fetchone()
            conn.close()
            
            if c_data:
                raw_date = c_data["contributionDate"]
                formatted_date = raw_date.strftime("%B %d, %Y") if isinstance(raw_date, (datetime.date, datetime.datetime)) else str(raw_date)
                
                with st.container(border=True):
                    st.markdown(f"#### 📝 Title: **{c_data['title']}**")
                    st.markdown(f"📂 **Type:** `{c_data['contributionType']}` • 📅 **Submitted:** {formatted_date} • 🏷️ **Tags:** *{c_data['tags']}*")
                    
                    if c_data['link'] and str(c_data['link']).lower() != "none":
                        st.markdown(f"🔗 **Web Asset Link:** [{c_data['link']}]({c_data['link']})")
                        
                    st.markdown("---")
                    st.markdown(f"📖 **Submission Message/Insight Content:**\n\n\"{c_data['description']}\"")
                    st.markdown("---")
                    
                    st.markdown("##### 🏅 Instructor Grade Allocation")
                    current_grade = c_data["grade"] if c_data["grade"] is not None else 0.0
                    
                    with st.form(f"grading_sub_form_{target_contrib_id}", clear_on_submit=False):
                        new_score = st.number_input("Assign Grade Points (e.g., Participation Credits)", min_value=0.0, max_value=100.0, value=float(current_grade), step=0.5)
                        submit_grade_btn = st.form_submit_button("💾 Save Grade to Ledger")
                        
                    if submit_grade_btn:
                        try:
                            conn = get_mysql_connection()
                            with conn.cursor() as cursor:
                                sql_update = "UPDATE contribution SET grade = %s WHERE contributionID = %s"
                                cursor.execute(sql_update, (float(new_score), int(target_contrib_id)))
                            st.success(f"🎉 Grade of **{new_score}** permanently recorded for this item!")
                            st.rerun()
                        except Exception as grade_err:
                            st.error(f"Failed to record grade update: {grade_err}")
                            
        except Exception as query_err:
            st.error(f"Error compiling selection detail card: {query_err}")
else:
    # This renders clean guidance instructions on screen when the input box is sitting on neutral zero
    st.info("💡 **Awaiting Input:** Please enter a student team's Group ID inside the numeric input box above to audit classroom participation logs.")
