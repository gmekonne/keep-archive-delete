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
