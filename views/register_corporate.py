import streamlit as st
import requests
import pymysql
import datetime
import hashlib
import json
import urllib.parse
from requests.auth import HTTPBasicAuth
import streamlit.components.v1 as components

# =====================================================================
# SECTION 1: DATABASE CONNECTION INFRASTRUCTURE
# What it does: Establishes a live link to your Hostinger MySQL database.
# =====================================================================
def get_mysql_connection():
    """Fresh real-time link straight to Hostinger."""
    return pymysql.connect(
        host=st.secrets["mysql"]["host"],
        user=st.secrets["mysql"]["user"],
        password=st.secrets["mysql"]["password"],
        database=st.secrets["mysql"]["database"],
        port=st.secrets["mysql"].get("port", 3306),
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )

def get_paypal_access_token():
    """Generates an ephemeral bearer access token natively for background lookups."""
    if "paypal" not in st.secrets:
        return None, None
    mode = str(st.secrets["paypal"].get("mode", "sandbox")).strip().lower()
    if mode == "sandbox":
        client_id = str(st.secrets["paypal"]["sandbox_client_id"]).strip()
        client_secret = str(st.secrets["paypal"]["sandbox_client_secret"]).strip()
        base_url = "https://paypal.com"
    else:
        client_id = str(st.secrets["paypal"]["live_client_id"]).strip()
        client_secret = str(st.secrets["paypal"]["live_client_secret"]).strip()
        base_url = "https://paypal.com"
        
    token_url = f"{base_url}/v1/oauth2/token"
    headers = {"Accept": "application/json", "Accept-Language": "en_US"}
    payload = {"grant_type": "client_credentials"}
    try:
        response = requests.post(token_url, auth=HTTPBasicAuth(client_id, client_secret), headers=headers, data=payload, timeout=10)
        if response.status_code == 200:
            return response.json().get("access_token"), base_url
    except Exception:
        pass
    return None, None

st.title("🏢 Corporate & Institutional Portal Registration")
st.write("Register your educational organization and process your enterprise purchase order using the live secure PayPal interface buttons below.")
st.markdown("---")

url_params = st.query_params
is_paid_signal = url_params.get("corp_paid")

if "corp_form_validated" not in st.session_state:
    st.session_state["corp_form_validated"] = False

# =====================================================================
# SECTION 2: THE REGISTRATION FORM (STEP 1)
# What it does: Captures all text data and runs pre-flight duplicate scans on submit.
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
            
            with get_mysql_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT userID FROM user WHERE LOWER(email) = %s", (target_email_clean,))
                    duplicate_user_found = cursor.fetchone()
                    
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
# What it does: Mounts buttons via components wrapper. Passes only the Order ID
# through the URL to eliminate browser parameter truncation freezes completely.
# =====================================================================
if st.session_state["corp_form_validated"] and not is_paid_signal:
    st.markdown("---")
    st.markdown("##### 💳 Step 2: Live Payment Processing Portal")
    st.success("🟢 Fields Validated successfully! Please complete your checkout selection below.")
    
    c_fname = st.session_state["cached_fname"]
    c_lname = st.session_state["cached_lname"]
    c_name = st.session_state["cached_org"]
    c_email = st.session_state["cached_email"]
    c_pass = st.session_state["cached_pass"]
    c_seats = st.session_state["cached_seats"]
    
    calculated_subtotal = float(c_seats * 10.0)
    st.info(f"🏅 **Enterprise Invoice Quote:** {c_seats} Teacher Accounts @ $10.00 each = **${calculated_subtotal:.2f} USD / Semester**")

    mode = str(st.secrets["paypal"].get("mode", "sandbox")).strip().lower()
    paypal_client_id = str(st.secrets["paypal"]["sandbox_client_id"]).strip() if mode == "sandbox" else str(st.secrets["paypal"]["live_client_id"]).strip()

    html_layout_string = """<!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <script src="https://paypal.com""" + paypal_client_id + """&currency=USD"></script>
        <style>
            body { font-family: Arial, sans-serif; background-color: transparent; margin: 0; padding: 5px; }
            #paypal-button-container { max-width: 100%; margin-top: 5px; }
        </style>
    </head>
    <body>
        <div id="paypal-button-container"></div>
        <script>
            paypal.Buttons({
                createOrder: function(data, actions) {
                    return actions.order.create({
                        purchase_units: [{
                            description: "CPMS Enterprise Activation: """ + c_name + """",
                            amount: { currency_code: "USD", value: """ + f'"{calculated_subtotal:.2f}"' + """ }
                        }]
                    });
                },
                onApprove: function(data, actions) {
                    return actions.order.capture().then(function(details) {
                        var orderID = details.id;
                        // 🟢 FIXED: We drop the massive raw_json payload to prevent web URL truncation freezes entirely!
                        window.parent.location.href = "https://streamlit.app" + orderID;
                    });
                }
            }).render('#paypal-button-container');
        </script>
    </body>
    </html>"""
    
    components.html(html_layout_string, height=600, scrolling=True)

# =====================================================================
# SECTION 4: THE SECURE SERVERLESS PAYLOAD FETCH & BACKEND WRITER
# What it does: Runs ONLY when the app reads "corp_paid=true" in the URL.
# Securely downloads transaction data from PayPal and records entries.
# =====================================================================
if is_paid_signal and str(is_paid_signal).lower() == "true":
    paypal_order_id = url_params.get("orderID")
    
    if paypal_order_id:
        st.info("⚡ Transaction validated by browser link. Verifying financial payload with PayPal's infrastructure...")
        
        # 🟢 SECURE UPGRADE: Fetch the true transaction parameters directly from PayPal serverless APIs
        token, base_url = get_paypal_access_token()
        if token:
            lookup_url = f"{base_url}/v2/checkout/orders/{paypal_order_id}"
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            
            res = requests.get(lookup_url, headers=headers, timeout=10)
            if res.status_code == 200:
                res_data = res.json()
                payment_status = res_data.get("status") # 'COMPLETED' or 'APPROVED'
                
                # Treat both completed and approved capture lines as validation clearing gates
                if payment_status in ["COMPLETED", "APPROVED"]:
                    try:
                        # Extract exact currency metrics matching your PHP logic
                        p_unit = res_data["purchase_units"][0]
                        captured_amount = p_unit["amount"]["value"]
                        captured_currency = p_unit["amount"]["currency_code"]
                        
                        c_fname = st.session_state.get("cached_fname", "Corporate")
                        c_lname = st.session_state.get("cached_lname", "User")
                        c_name = st.session_state.get("cached_org", "University")
                        c_email = st.session_state.get("cached_email")
                        c_pass = st.session_state.get("cached_pass", "defaultpass")
                        
                        if c_email:
                            current_ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            
                            with get_mysql_connection() as conn:
                                with conn.cursor() as cursor:
                                    cursor.execute("SELECT COUNT(*) as cnt FROM transactions WHERE txn_id = %s", (paypal_order_id,))
                                    dup_check = cursor.fetchone()
                                    
                                    if dup_check and dup_check["cnt"] > 0:
                                        st.warning("🎉 Payment already processed previously.")
                                    else:
                                        hashed_password_string = hashlib.sha256(c_pass.encode('utf-8')).hexdigest()
                                        
                                        # Write Step 1: Create the User Account
                                        sql_insert_user = """
                                            INSERT INTO user (fname, lname, corp_name, email, password, acct_type, subscription_status, dateCreated, role, user_role, paypal_order_id, last_payment_date) 
                                            VALUES (%s, %s, %s, %s, %s, 'corporate', 'active', %s, 'instructor', 'instructor', %s, %s)
                                        """
                                        cursor.execute(sql_insert_user, (
                                            c_fname, c_lname, c_name, c_email.strip().lower(), 
                                            hashed_password_string, current_ts, paypal_order_id, current_ts
                                        ))
                                        
                                        new_corporate_userid = cursor.lastrowid
                                        
                                        # Write Step 2: Create the auditing transaction history record
                                        sql_insert_txn = """
                                            INSERT INTO transactions 
                                            (user_id, txn_id, amount, currency, status, payment_gateway, transaction_data, created_at) 
                                            VALUES (%s, %s, %s, %s, 'COMPLETED', 'PayPal', %s, %s)
                                        """
                                        transaction_data_json = json.dumps(res_data)
                                        cursor.execute(sql_insert_txn, (
                                            int(new_corporate_userid), paypal_order_id, float(captured_amount),
                                            captured_currency, transaction_data_json, current_ts
                                        ))
                                        
                                        st.success(f"🎉 **Corporate Profile Deployed Successfully!** Account created with User ID **{new_corporate_userid}**.")
                                        st.balloons()
                                        
                            st.session_state["corp_form_validated"] = False
                            st.query_params.clear()
                    except Exception as db_err:
                        st.error(f"❌ Database Transaction Synchronization Failure: {db_err}")
                else:
                    st.error(f"❌ Payment verification refused: Status returned was '{payment_status}'.")
            else:
                st.error("❌ Failed to query secure verification receipt data from PayPal servers.")
        else:
            st.error("❌ API Authentication Failed: Unable to verify transaction codes with PayPal.")
st.markdown("---")
