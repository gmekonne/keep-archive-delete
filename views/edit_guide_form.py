import streamlit as st
import pymysql
import datetime

def get_mysql_connection():
    """Fresh uncached link to satisfy Hostinger firewall connection rules."""
    return pymysql.connect(
        host=st.secrets["mysql"]["host"],
        user=st.secrets["mysql"]["user"],
        password=st.secrets["mysql"]["password"],
        database=st.secrets["mysql"]["database"],
        port=st.secrets["mysql"].get("port", 3306),
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )

st.subheader("📝 Manage CPMS User Guides")
st.write("Edit and update documentation manuals stored in the database. Supports Markdown layout formatting elements.")
st.markdown("---")

# Initializer tracking variables
current_instructor_text = ""
current_student_text = ""
current_version = "v1.0"
record_exists = False

# 1. Background Scan: Pull existing row data if it already exists (Assumes GuideID = 1 master row paradigm)
try:
    conn = get_mysql_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT instructor_guide, student_guide, version_label FROM guide WHERE guideID = 1")
        existing_guide = cursor.fetchone()
        if existing_guide:
            current_instructor_text = existing_guide["instructor_guide"] or ""
            current_student_text = existing_guide["student_guide"] or ""
            current_version = existing_guide["version_label"] or "v1.0"
            record_exists = True
    conn.close()
except Exception as e:
    st.warning(f"Database layout initialization notice: {e}. If the guide table is brand new, this will clear upon first save.")

# 2. Workspace Form Interface Elements
with st.form("cpms_guide_management_form"):
    version_input = st.text_input("Documentation Version Label", value=current_version, placeholder="e.g., v1.0 - Fall 2026")
    
    st.markdown("##### 👥 Student Guide Content")
    student_guide_input = st.text_area(
        "Student Manual Text (Markdown supported)", 
        value=current_student_text if current_student_text else "Paste student guide here...", 
        height=300
    )
    
    st.markdown("##### 🛠️ Instructor Guide Content")
    instructor_guide_input = st.text_area(
        "Instructor Manual Text (Markdown supported)", 
        value=current_instructor_text if current_instructor_text else "Paste instructor parameters here...", 
        height=200
    )
    
    submit_guide = st.form_submit_button("💾 Save User Documentation to Database", width="stretch")

# 3. Transaction Database Commit Loop
if submit_guide:
    try:
        conn = get_mysql_connection()
        current_ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        with conn.cursor() as cursor:
            if record_exists:
                # Update existing row configurations
                sql_update = """
                    UPDATE guide 
                    SET instructor_guide = %s, student_guide = %s, last_updated = %s, version_label = %s 
                    WHERE guideID = 1
                """
                cursor.execute(sql_update, (instructor_guide_input, student_guide_input, current_ts, version_input.strip()))
            else:
                # Insert primary initial master tracking row
                sql_insert = """
                    INSERT INTO guide (guideID, instructor_guide, student_guide, last_updated, version_label) 
                    VALUES (1, %s, %s, %s, %s)
                """
                cursor.execute(sql_insert, (instructor_guide_input, student_guide_input, current_ts, version_input.strip()))
                
        st.success("🎉 Success! CPMS user guidelines have been successfully synchronized and locked to your Hostinger database.")
        st.balloons()
        conn.close()
    except Exception as tx_err:
        st.error(f"Failed to record documentation configurations: {tx_err}")
