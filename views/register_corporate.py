import streamlit as st
import pymysql
import datetime
import hashlib
import json
import urllib.parse
import streamlit.components.v1 as components

# =====================================================================
# SECTION 1: DATABASE CONNECTION INFRASTRUCTURE
# =====================================================================
def get_mysql_connection():
    """Fresh link straight to Hostinger with proper configuration 
       to prevent port exhaustion (Errno 99)."""
    conn = pymysql.connect(
        host=st.secrets["mysql"]["host"],
        user=st.secrets["mysql"]["user"],
        password=st.secrets["mysql"]["password"],
        database=st.secrets["mysql"]["database"],
        port=st.secrets["mysql"].get("port", 3306),
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
        client_flag=pymysql.constants.CLIENT.MULTI_STATEMENTS
    )
    return conn


st.title("🏢 Corporate & Institutional Portal Registration")
st.write("Register your educational organization and process your enterprise subscription using the secure PayPal interface buttons below.")
st.markdown("---")

url_params = st.query_params
is_paid_signal = url_params.get("corp_paid")

if "corp_form_validated" not in st.session_state:
    st.session_state["corp_form_validated"] = False

# =====================================================================
# SECTION 2: THE REGISTRATION FORM (STEP 1)
# =====================================================================
st.markdown("##### 📝 Step 1: Administrative Account Specifications")

with st.form("corporate_onboarding_form", clear_on_submit=False):
    col_n1, col_n2 = st.columns(2)
    with col_n1:
        first_name = st.text_input("First Name *", placeholder="e.g., John")
    with col_n2:
        last_name = st.text_input("Last Name *", placeholder="e.g., Smith")
        
    corp_name = st.text_input("Organization / University Name *", placeholder="e.g., Global Tech University")
    corp_email = st.text_input("Administrative Account Email *", placeholder="admin@domain.com")
    corp_password = st.text_input("Create Portal Access Password *", type="password", placeholder="Choose a strong password string")
    corp_seats = st.number_input("Target Seat Allocations (Instructor Accounts)", min_value=5, max_value=500, value=25, step=5)
    
    validate_btn = st.form_submit_button("🔒 Validate Roster Fields & Initialize Checkout", use_container_width=True)

if validate_btn:
    if not first_name or not last_name or not corp_name or not corp_email or not corp_password:
        st.error("❌ All starred fields are strictly required to initialize your profile setup.")
        st.session_state["corp_form_validated"] = False
    else:
        try:
            target_email_clean = corp_email.strip().lower()
            conn = get_mysql_connection()
            duplicate_user_found = None
            
            try:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT userID FROM user WHERE LOWER(email) = %s", (target_email_clean,))
                    duplicate_user_found = cursor.fetchone()
            finally:
                conn.close()
                    
            if duplicate_user_found:
                st.error(f"⚠️ Account Creation Restricted: The email address '{target_email_clean}' is already registered inside our system.")
                st.session_state["corp_form_validated"] = False
            else:
                st.session_state["corp_form_validated"] = True
                st.session_state["cached_fname"] = first_name.strip()
                st.session_state["cached_lname"] = last_name.strip()
                st.session_state["cached_org"] = corp_name.strip()
                st.session_state["cached_email"] = target_email_clean
                st.session_state["cached_pass"] = corp_password
                st.session_state["cached_seats"] = corp_seats
                st.rerun()
                
        except Exception as e:
            st.error(f"Failed to execute pre-flight database scans: {e}")

    
# =====================================================================
# SECTION 3: VISUAL PAYPAL SMART BUTTON RENDER (STEP 2)
# =====================================================================
if st.session_state["corp_form_validated"] and not is_paid_signal:
    st.markdown("---")
    st.markdown("##### 💳 Step 2: Live Payment Processing Portal")
    st.success("🟢 Fields Validated successfully! Please complete your subscription checkout below.")
    
    c_seats = st.session_state["cached_seats"]
    st.info(f"🏅 **Selected Tier:** CPMS Classroom Basic Subscription for **{c_seats} Seats**.")

    # -------------------------------------------------------------------------
    # PASTE YOUR ENTIRE COPIED PAYPAL CODE DIRECTLY INSIDE THE TRIPLE QUOTES BELOW.
    # Replace everything between the triple quotes with your exact copied 
    # <div> line and <script> blocks.
    # -------------------------------------------------------------------------
    paypal_layout_string = """
    <div id="paypal-button-container-P-3BM69430LE4978304NJMC6AQ"></div>
    <script src="https://www.paypal.com/sdk/js?client-id=AY-6Q9n6LBX722jJqwtIs722v9qo_RrHAIp3Vk1XWZpGjrDwCQoq5999BvuKLQRpVAOQKtUTsRcwRCFP&vault=true&intent=subscription" data-sdk-integration-source="button-factory"></script>
    <script>
      paypal.Buttons({
          style: {
              shape: 'rect',
              color: 'gold',
              layout: 'vertical',
              label: 'subscribe'
          },
          createSubscription: function(data, actions) {
            return actions.subscription.create({
              /* Creates the subscription */
              plan_id: 'P-3BM69430LE4978304NJMC6AQ',
              quantity: 1 // The quantity of the product for a subscription
            });
          },
          onApprove: function(data, actions) {
              // 1. Capture the unique subscription ID generated by PayPal
              var subID = data.subscriptionID;
              
              // 2. Package the response data so your python database code can read it
              var raw = encodeURIComponent(JSON.stringify(data));
              
              // 3. Force the parent browser tab to reload with the success signals in the URL
              window.top.location.href = window.top.location.origin + window.top.location.pathname + 
                  "?corp_paid=true&subscriptionID=" + subID + "&raw_json=" + raw;
          }
      }).render('#paypal-button-container-P-3BM69430LE4978304NJMC6AQ'); // Renders the PayPal button
    </script>
    """
    # -------------------------------------------------------------------------
    
    # 🟢 FIXED: Kept height at 600px to ensure proper UI layout without tight scrolling
    components.html(paypal_layout_string, height=600, scrolling=True)


# =====================================================================
# SECTION 4: THE URL INTERCEPTOR & BACKEND DATA WRITER
# =====================================================================
if is_paid_signal and str(is_paid_signal).lower() == "true":
    paypal_sub_id = url_params.get("subscriptionID")
    full_raw_json_str = urllib.parse.unquote(url_params.get("raw_json", "{}"))
    
    st.info("⚡ Subscription validated by PayPal. Completing database synchronization loops...")
    
    c_fname = st.session_state.get("cached_fname", "Corporate")
    c_lname = st.session_state.get("cached_lname", "User")
    c_name = st.session_state.get("cached_org", "University")
    c_email = st.session_state.get("cached_email")
    c_pass = st.session_state.get("cached_pass", "defaultpass")
    
    if c_email:
        try:
            current_ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            with get_mysql_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT COUNT(*) as cnt FROM transactions WHERE txn_id = %s", (paypal_sub_id,))
                    dup_check = cursor.fetchone()
                    
                    if dup_check and dup_check["cnt"] > 0:
                        st.warning("🎉 This subscription payment has already been securely processed.")
                    else:
                        hashed_password_string = hashlib.sha256(c_pass.encode('utf-8')).hexdigest()
                        
                        sql_insert_user = """
                            INSERT INTO user (fname, lname, corp_name, email, password, acct_type, subscription_status, dateCreated, role, user_role, paypal_order_id, last_payment_date) 
                            VALUES (%s, %s, %s, %s, %s, 'corporate', 'active', %s, 'instructor', 'instructor', %s, %s)
                        """
                        cursor.execute(sql_insert_user, (
                            c_fname, c_lname, c_name, c_email.strip().lower(), 
                            hashed_password_string, current_ts, paypal_sub_id, current_ts
                        ))
                        
                        new_corporate_userid = cursor.lastrowid
                        
                        sql_insert_txn = """
                            INSERT INTO transactions 
                            (user_id, txn_id, amount, currency, status, payment_gateway, transaction_data, created_at) 
                            VALUES (%s, %s, %s, %s, 'ACTIVE', 'PayPal-Subscription', %s, %s)
                        """
                        cursor.execute(sql_insert_txn, (
                            int(new_corporate_userid), paypal_sub_id, 0.0, 
                            "USD", full_raw_json_str, current_ts
                        ))
                        
                        st.success(f"🎉 **Corporate Profile Deployed Successfully!** Account created with User ID **{new_corporate_userid}**.")
                        st.balloons()
                        
            st.session_state["corp_form_validated"] = False
            st.query_params.clear()
        except Exception as db_err:
            st.error(f"❌ Database Transaction Synchronization Failure: {db_err}")
st.markdown("---")
