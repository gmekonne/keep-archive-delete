import streamlit as st
import pymysql
import bcrypt

st.title("🔑 Reset Instructor Password")
st.write("Modify your credentials securely.")

with st.form("reset_form"):
    email = st.text_input("Enter Registered Email Address")
    new_password = st.text_input("Enter New Password", type="password")
    confirm_password = st.text_input("Confirm New Password", type="password")
    
    submit = st.form_submit_button("Update Password", use_container_width=True)

if submit:
    if password != confirm_password:
        st.error("Passwords mismatch.")
    else:
        try:
            conn = pymysql.connect(
                host=st.secrets["mysql"]["host"],
                user=st.secrets["mysql"]["user"],
                password=st.secrets["mysql"]["password"],
                database=st.secrets["mysql"]["database"],
                port=st.secrets["mysql"].get("port", 3306)
            )
            hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            if hashed_password.startswith("$2b$"):
                hashed_password = hashed_password.replace("$2b$", "$2y$", 1)
                
            with conn.cursor() as cursor:
                # Update user matching your field schemas
                sql = "UPDATE user SET password = %s WHERE email = %s"
                cursor.execute(sql, (hashed_password, email.lower().strip()))
                rows_affected = cursor.rowcount
                
            conn.commit()
            conn.close()
            
            if rows_affected > 0:
                st.success("🔓 Password updated successfully! Please navigate back to login.")
            else:
                st.error("No account found matching that email address.")
        except Exception as e:
            st.error(f"Error processing password rewrite: {e}")
