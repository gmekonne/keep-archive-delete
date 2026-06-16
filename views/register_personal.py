import streamlit as st
import datetime
import pymysql
import bcrypt

st.title("📝 Instructor Registration (Personal Account)")
st.write("Create your personal 5-Star Presentation Rater account.")

with st.form("personal_registration_form"):
    email = st.text_input("Email Address")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")
    fname = st.text_input("First Name")
    lname = st.text_input("Last Name")
    
    submit = st.form_submit_button("Register Free Trial Account", use_container_width=True)

if submit:
    if not email or not password or not fname or not lname:
        st.error("All fields are strictly required.")
    elif password != confirm_password:
        st.error("Passwords do not match.")
    else:
        try:
            # Calculate initial free subscription status and expiry date
            current_date = datetime.date.today()
            expiry_date = current_date + datetime.timedelta(days=90)  # +3 months
            subscription_status = 'active'  # Free trials are active immediately
            
            conn = pymysql.connect(
                host=st.secrets["mysql"]["host"],
                user=st.secrets["mysql"]["user"],
                password=st.secrets["mysql"]["password"],
                database=st.secrets["mysql"]["database"],
                port=st.secrets["mysql"].get("port", 3306)
            )
            
            # Encrypt password to match PHP password_hash
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            if hashed_password.startswith("$2b$"):
                hashed_password = hashed_password.replace("$2b$", "$2y$", 1)
                
            with conn.cursor() as cursor:
                # Updated SQL statement matching your exact subscription fields
                sql = """
                    INSERT INTO user (role, fname, lname, email, password, acct_type, dateCreated, expirty_date, subscription_status) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (
                    "instructor", fname, lname, email.lower().strip(), 
                    hashed_password, "personal", current_date, expiry_date, subscription_status
                ))
            conn.commit()
            conn.close()
            st.success("🎉 Registration complete! Your 3-month free trial is active. Go to the Log In Portal to sign in.")
        except pymysql.err.IntegrityError:
            st.error("This email address is already registered.")
        except Exception as e:
            st.error(f"System Error: {e}")
