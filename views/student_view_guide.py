import streamlit as st
import pymysql
import datetime

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

# Establish page headers
st.title("📖 Class Participation Management System (CPMS)")
st.write("Student Master Documentation Guide Manual")
st.markdown("---")

# Initialize placeholder tracking container fields
db_student_guide_content = ""
last_updated_timestamp = None
version_string_tag = "v1.0"
load_success = False

# 1. Execution Phase: Connect to Hostinger and fetch row metadata strings
try:
    conn = get_mysql_connection()
    with conn.cursor() as cursor:
        # Targets your exact fields and table names from your custom documentation schema
        cursor.execute("SELECT student_guide, last_updated, version_label FROM guide WHERE guideID = 1")
        guide_record = cursor.fetchone()
        
        if guide_record:
            db_student_guide_content = guide_record["student_guide"]
            last_updated_timestamp = guide_record["last_updated"]
            version_string_tag = guide_record["version_label"] or "v1.0"
            load_success = True
    conn.close()
except Exception as e:
    st.error(f"Failed to synchronize documentation from database server: {e}")

# 2. Render Phase: Format and print text strings to screen dynamically
if not load_success or not db_student_guide_content.strip():
    st.warning("⚠️ Documentation Offline: The student user manual has not been uploaded to the database master index row yet.")
    st.info("💡 **Instructor Note:** Log into the Instructor Dashboard and open the **📝 Enter / Edit Guide** operations console to save your master copy.")
else:
    # Format modification log metrics beautifully
    if isinstance(last_updated_timestamp, (datetime.datetime, datetime.date)):
        formatted_time = last_updated_timestamp.strftime("%B %d, %Y")
    else:
        formatted_time = str(last_updated_timestamp)
        
    # Render small metadata information tags line right at the top
    st.caption(f"📚 Edition: **{version_string_tag}** • ⏱️ Documentation Last Sync: *{formatted_time}*")
    st.markdown("---")
    
    # --- RENDER METHOD: PIPES THE RAW MARKDOWN STRING INTO AN INTERACTIVE TEXT GRID ---
    # Streamlit natively reads markdown tags (#, ##, **, -, etc.) and draws headers and layouts cleanly
    st.markdown(db_student_guide_content)
    
    st.markdown("---")
    st.caption("📍 *End of CPMS Student Guide Document Matrix. Review your left navigation sidebar menu to execute an operation.*")
