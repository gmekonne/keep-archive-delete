import streamlit as st
import pymysql

def get_mysql_connection():
    """Establishes a real-time connection straight to Hostinger."""
    return pymysql.connect(
        host=st.secrets["mysql"]["host"],
        user=st.secrets["mysql"]["user"],
        password=st.secrets["mysql"]["password"],
        database=st.secrets["mysql"]["database"],
        port=st.secrets["mysql"].get("port", 3306),
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )

st.title("📋 Course Presentation Guidelines")
st.write("Review the grading rubrics, presentation durations, and instructions set by your professor.")
st.markdown("---")

# 1. User-Friendly Input Interface (Asks for Group ID)
input_gid = st.number_input("Enter your Group ID *", min_value=1, step=1, key="student_inst_lookup_val")

if st.button("Fetch Course Guidelines", use_container_width=True):
    try:
        conn = get_mysql_connection()
        with conn.cursor() as cursor:
            # Step 1: Look up the group directly to verify registration
            cursor.execute("SELECT groupName, courseID FROM presentationgroup WHERE groupID = %s", (int(input_gid),))
            group_record = cursor.fetchone()
            
            if not group_record:
                st.error(f"❌ Verification Failed: Group ID '{input_gid}' is not registered in the system.")
                st.info("💡 **Next Step:** If you are part of a new team, go to the **👤 1. Create Student Account** tab to register your group roster first.")
            else:
                # Step 2: Fetch corresponding parameters straight from the parent course row table matching fields
                sql_course = """
                    SELECT courseCode, courseTitle, courseTerm, instruction, courseSection 
                    FROM course 
                    WHERE courseID = %s
                """
                cursor.execute(sql_course, (int(group_record["courseID"]),))
                course_record = cursor.fetchone()
                
                if not course_record:
                    st.error("❌ Linkage Error: Your group is registered, but it points to a course tracking row that no longer exists.")
                else:
                    # Translate Term IDs cleanly
                    TERM_LABELS = {"1": "Fall", "2": "Winter", "3": "Summer"}
                    raw_term = str(course_record["courseTerm"])
                    term_text = TERM_LABELS.get(raw_term, f"Term {raw_term}")
                    
                    st.success(f"🟢 Authenticated: Loaded class rules for team **'{group_record['groupName']}'**")
                    
                    # 2. Render Course Specifications Card layout
                    with st.container(border=True):
                        st.subheader(f"📚 {course_record['courseCode']} — Section {course_record['courseSection']}")
                        st.markdown(f"**Full Course Title:** {course_record['courseTitle']}")
                        st.markdown(f"**Academic Term:** {term_text}")
                        st.markdown("---")
                        
                        st.markdown("##### 📢 Official Presentation Instructions & Requirements:")
                        
                        # Extract and sanitize the real-time instructions text parameters from the DB
                        raw_instructions = course_record["instruction"]
                        if not raw_instructions or str(raw_instructions).strip().lower() in ["none", ""]:
                            st.info("ℹ️ Your instructor has not added specific guidelines for this course track yet.")
                        else:
                            # --- FIXED: PARSES TEXT LINE-BY-LINE AND PARAGRAPH-BY-PARAGRAPH ---
                            # Step A: Clean up weird hidden database carriage return sequences (\r\n) down to standard line breaks (\n)
                            sanitized_text = str(raw_instructions).replace("\r\n", "\n").replace("\r", "\n").strip()
                            
                            # Step B: Replace single line breaks with a web breakthrough tag (<br>) to keep continuous lineation
                            # And replace double line breaks with custom structural spacing wrappers to build separate paragraphs
                            html_formatted_instructions = ""
                            paragraphs = [p for p in sanitized_text.split("\n\n") if p.strip()]
                            
                            for p in paragraphs:
                                # Within each paragraph, preserve individual single-line breaks cleanly
                                line_broken_text = p.replace("\n", "<br>")
                                html_formatted_instructions += f"<p style='margin-bottom: 16px; line-height: 1.6;'>{line_broken_text}</p>"
                            
                            # Step C: Render using the native HTML component to ensure responsive, wrapped visual formatting
                            st.html(f"<div style='white-space: normal; word-break: break-word; font-family: sans-serif; font-size: 15px; color: #333;'>{html_formatted_instructions}</div>")
                            
        conn.close()
    except Exception as server_error:
        st.error(f"Server data retrieval failure: {server_error}")
