import streamlit as st
import pymysql
import bcrypt

st.title("🔑 Instructor Login Portal")
st.write("Sign in to access your personal student dashboards.")

def get_mysql_connection():
    return pymysql.connect(
        host=st.secrets["mysql"]["host"],
        user=st.secrets["mysql"]["user"],
        password=st.secrets["mysql"]["password"],
        database=st.secrets["mysql"]["database"],
        port=st.secrets["mysql"].get("port", 3306),
        cursorclass=pymysql.cursors.DictCursor
    )

login_email = st.text_input("Email Address", key="portal_login_email")
login_password = st.text_input("Password", type="password", key="portal_login_pass")

if st.button("Log In to Dashboard", use_container_width=True):
    try:
        conn = get_mysql_connection()
        with conn.cursor() as cursor:
            sql = "SELECT userID, fname, lname, password FROM user WHERE email = %s"
            cursor.execute(sql, (login_email.lower().strip(),))
            user_record = cursor.fetchone()
        conn.close()
        
        if user_record and bcrypt.checkpw(login_password.encode('utf-8'), user_record["password"].encode('utf-8')):
            st.session_state.logged_in = True
            st.session_state.user_id = user_record["userID"]
            st.session_state.user_name = f"{user_record['fname']} {user_record['lname']}"
            st.session_state.user_email = login_email.lower().strip()
            st.success("Access Granted! Loading your dashboard...")
            st.rerun()
        else:
            st.error("Invalid email or password.")
    except Exception as ex:
        st.error(f"Database connection error: {ex}")
