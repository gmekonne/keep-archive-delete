import streamlit as st
import datetime
import pymysql
import bcrypt

st.title("🏢 Corporate Instructor Registration")
st.write("Establish an institutional account with organizational mapping.")

with st.form("corporate_registration_form"):
    email = st.text_input("Work Email Address")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")
    fname = st.text_input("First Name")
    lname = st.text_input("Last Name")
    corp_name = st.text_input("Institution / Corporation Name")
    org_id = st.text_input("Assigned Organization ID (orgID)")
    
    submit = st.form_submit_button("Register Corporate Account", use_container_width=True)

if submit:
    if not email or not password or not corp_name or not org_id:
        st.error("Required fields missing.")
    elif password != confirm_password:
        st.error("Passwords do not match.")
    else:
        try:
            conn = pymysql.connect(
                host=st.secrets["mysql"]["host"],
                user=st.secrets["mysql"]["user"],
                password=st.secrets["mysql"]["password"],
                database=st.secrets["mysql"]["database"],
                port=st.secrets["mysql"].get("port", 3306)
            )
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            if hashed_password.startswith("$2b$"):
                hashed_password = hashed_password.replace("$2b$", "$2y$", 1)
                
            with conn.cursor() as cursor:
                sql = """
                    INSERT INTO user (role, fname, lname, email, password, corp_name, acct_type, orgID, dateCreated) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (
                    "instructor", fname, lname, email.lower().strip(), 
                    hashed_password, corp_name, "corporate", org_id, datetime.datetime.now()
                ))
            conn.commit()
            conn.close()
            st.success("🏢 Corporate profile synchronized successfully!")
        except Exception as e:
            st.error(f"Error: {e}")
