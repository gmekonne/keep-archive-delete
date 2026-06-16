import streamlit as st
import datetime
import pymysql
import bcrypt

st.title("📝 Instructor Registration (Personal Account)")
st.write("Create your personal 5-Star Presentation Rater account.")

# Match your exact Hostinger database columns
with st.form("personal_registration_form"):
    email = st.text_input("Email Address")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")
    fname = st.text_input("First Name")
    lname = st.text_input("Last Name")
    
    submit = st.form_submit_button("Register Account", use_container_width=True)

if submit:
    if not email or not password or not fname or not lname:
        st.error("All fields are strictly required.")
    elif password != confirm_password:
        st.error("Passwords do not match.")
    else:
        try:
            # Reuses your central secrets connection config
            conn = pymysql.connect(
                host=st.secrets["mysql"]["host"],
                user=st.secrets["mysql"]["user"],
                password=st.secrets["mysql"]["password"],
                database=st.secrets["mysql"]["database"],
                port=st.secrets["mysql"].get("port", 3306)
            )
            
            # PHP password_hash compatibility layer
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            # Replace '2y' back to standard PHP format if your host forces string replacements
            if hashed_password.startswith("$2b$"):
                hashed_password = hashed_password.replace("$2b$", "$2y$", 1)
                
            with conn.cursor() as cursor:
                # Insert statement matching your database schema fields
                sql = """
                    INSERT INTO user (role, fname, lname, email, password, acct_type, dateCreated) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (
                    "instructor", fname, lname, email.lower().strip(), 
                    hashed_password, "personal", datetime.datetime.now()
                ))
            conn.commit()
            conn.close()
            st.success("🎉 Registration complete! You can now navigate to the Log In portal.")
        except pymysql.err.IntegrityError:
            st.error("This email address is already registered.")
        except Exception as e:
            st.error(f"System Error: {e}")

