import streamlit as st
import requests
import pymysql
import datetime
import json
import hashlib
from requests.auth import HTTPBasicAuth

def get_mysql_connection():
    """Fresh uncached real-time link straight to Hostinger."""
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
    """Generates an ephemeral bearer access token using direct data credentials payload mapping."""
    if "paypal" not in st.secrets:
        st.error("🔑 Configuration Error: The '[paypal]' block header is missing from your secrets manager window panel.")
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
    
    # 🟢 FIXED: Swapped basic auth header with direct, flat payload structures to stop 401 rejections
    headers = {
        "Accept": "application/json",
        "Accept-Language": "en_US",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    # Explicitly pass credentials as raw form dictionary items straight to the server
    payload = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }
    
    try:
        # Firing standard direct network data request post tracking streams
        response = requests.post(token_url, headers=headers, data=payload, timeout=10)
        
        if response.status_code == 200:
            return response.json().get("access_token"), base_url
        else:
            st.error(f"🔒 PayPal OAuth Refused: Status {response.status_code}. Details: {response.text[:120]}")
            return None, None
    except Exception as e:
        st.toast(f"🔌 Connection Exception: {e}", icon="⚠️")
        return None, None


def create_paypal_order(price_amount, company_name, target_instructor_uid):
    """Outbound payload setup: Spawns the order and binds custom_id exactly like your PHP file."""
    token, base_url = get_paypal_access_token()
    if not token:
        return None
        
    order_url = f"{base_url}/v2/checkout/orders"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    payload = {
        "intent": "CAPTURE",
        "purchase_units": [{
            "description": f"CPMS Corporate Enterprise Activation - Organization: {company_name}",
            "custom_id": str(target_instructor_uid), 
            "amount": {"currency_code": "USD", "value": f"{price_amount:.2f}"}
        }],
        "application_context": {
            "return_url": f"https://streamlit.app",
            "cancel_url": "https://streamlit.app"
        }
    }
    
    response = requests.post(order_url, headers=headers, json=payload, timeout=10)
    if response.status_code == 201 or response.status_code == 200:
        return response.json()
    else:
        # 🟢 DIAGNOSTIC HIGHLIGHT: Alerts you to the exact raw error string if PayPal throws a payload error
        st.error(f"⚠️ PayPal Order API Refused ({response.status_code}): {response.text}")
        return None

st.title("🏢 Corporate & Institutional Portal Registration")
st.write("Register your educational organization, log account variables, and complete purchase orders via PayPal checkout portals.")
st.markdown("---")

current_system_mode = str(st.secrets["paypal"].get("mode", "sandbox")).strip().upper()
if current_system_mode == "SANDBOX":
    st.caption(f"🛡️ Active Gateway Network Status: **{current_system_mode} MODE ACTIVE**")
else:
    st.caption(f"🛡️ Active Gateway Network Status: **{current_system_mode} PRODUCTION MODE**")
# 1. UI Information Processing Fields Layer (Includes First Name, Last Name, and Corporate Contexts)
with st.form("corporate_registration_details_form"):
    col_n1, col_n2 = st.columns(2)
    with col_n1:
        first_name = st.text_input("First Name *", placeholder="e.g., John")
    with col_n2:
        last_name = st.text_input("Last Name *", placeholder="e.g., Smith")
        
    corp_name = st.text_input("Organization / University Name *", placeholder="e.g., Global Tech University")
    corp_email = st.text_input("Administrative Account Email *", placeholder="admin@domain.com")
    corp_password = st.text_input("Create Portal Access Password *", type="password", placeholder="Choose a strong password string")
    corp_seats = st.number_input("Target Seat Allocations (Total Instructor Accounts)", min_value=5, max_value=500, value=25, step=5)
    
    calculated_subtotal = float(corp_seats * 10.0)
    st.info(f"🏅 **Enterprise Invoice Quote:** {corp_seats} Teacher Accounts @ $10.00 each = **${calculated_subtotal:.2f} USD / Semester**")
    
    checkout_submit_btn = st.form_submit_button("💳 Initialize Secure PayPal Corporate Checkout", use_container_width=True)

if checkout_submit_btn:
    if not first_name or not last_name or not corp_name or not corp_email or not corp_password:
        st.error("All starred fields are required to process your organization registration profile.")
    else:
        with st.spinner("Checking database for duplicates and connecting to PayPal..."):
            try:
                conn = get_mysql_connection()
                target_email_clean = corp_email.strip().lower()
                
                with conn.cursor() as cursor:
                    cursor.execute("SELECT userID FROM user WHERE LOWER(email) = %s", (target_email_clean,))
                    duplicate_user_found = cursor.fetchone()
                    
                    if duplicate_user_found:
                        st.error(f"⚠️ Account Creation Restricted: The administrative email address **'{target_email_clean}'** is already registered.")
                        conn.close()
                    else:
                        hashed_password_string = hashlib.sha256(corp_password.strip().encode('utf-8')).hexdigest()
                        current_ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        
                        sql_create_pending_user = """
                            INSERT INTO user (fname, lname, corp_name, email, password, acct_type, subscription_status, dateCreated, role, user_role) 
                            VALUES (%s, %s, %s, %s, %s, 'corporate', 'pending', %s, 'instructor', 'instructor')
                        """
                        cursor.execute(sql_create_pending_user, (
                            first_name.strip(), last_name.strip(), corp_name.strip(), 
                            target_email_clean, hashed_password_string, current_ts
                        ))
                        
                        new_corporate_userid = cursor.lastrowid
                        conn.close()
                        
                        # Trigger Order Generation
                        order_object = create_paypal_order(calculated_subtotal, corp_name, new_corporate_userid)
                        
                        if order_object:
                            paypal_order_id = order_object["id"]
                            approve_link = next(link["href"] for link in order_object["links"] if link["rel"] == "approve")
                            
                            st.session_state["pending_corp_order_id"] = paypal_order_id
                            st.session_state["pending_corp_name"] = corp_name
                            st.session_state["pending_uid"] = new_corporate_userid
                            st.session_state["pending_subtotal"] = calculated_subtotal
                            
                            st.success(f"🎉 Pending account created with **User ID {new_corporate_userid}**! Please finalize payment below.")
                            st.link_button("🚀 Proceed to PayPal Secure Payment Portal", url=approve_link, use_container_width=True)
            except Exception as e:
                st.error(f"Failed to record pending infrastructure account details: {e}")

st.markdown("---")

# =====================================================================
# 2. AUTO-CAPTURE GATEWAY: PORTED DIRECTLY FROM YOUR PHP DB ACTIONS
# =====================================================================
url_params = st.query_params
incoming_token = url_params.get("token")

if incoming_token:
    pending_order_id = st.session_state.get("pending_corp_order_id")
    
    if pending_order_id:
        st.info("⚡ Detecting incoming payment clearing metrics. Verifying transaction payload...")
        
        token, base_url = get_paypal_access_token()
        if token:
            capture_url = f"{base_url}/v2/checkout/orders/{pending_order_id}/capture"
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            
            cap_response = requests.post(capture_url, headers=headers, json={}, timeout=10)
            
            if cap_response.status_code == 201 or cap_response.status_code == 200:
                res_data = cap_response.json()
                payment_status = res_data.get("status") 
                
                if payment_status == "COMPLETED":
                    paypal_txn_id = res_data.get("id")
                    
                    # 🟢 FIXED DATA ARRAYS DRILLING: Safely targets the array list indices to match PayPal V2 responses perfectly
                    purchase_unit = res_data["purchase_units"][0]
                    capture_object = purchase_unit["payments"]["captures"][0]
                    captured_amount = capture_object["amount"]["value"]
                    captured_currency = capture_object["amount"]["currency_code"]
                    
                    custom_subscription_id = purchase_unit.get("custom_id")
                    if not custom_subscription_id:
                        custom_subscription_id = st.session_state.get("pending_uid")
                        
                    try:
                        conn = get_mysql_connection()
                        with conn.cursor() as cursor:
                            cursor.execute("SELECT COUNT(*) as cnt FROM transactions WHERE txn_id = %s", (paypal_txn_id,))
                            dup_check = cursor.fetchone()
                            
                            if dup_check and dup_check["cnt"] > 0:
                                st.warning("🎉 Payment already processed previously.")
                            else:
                                current_ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                
                                sql_update_user = """
                                    UPDATE user 
                                    SET subscription_status = 'active', 
                                        last_payment_date = %s, 
                                        paypal_order_id = %s 
                                    WHERE userID = %s
                                """
                                cursor.execute(sql_update_user, (current_ts, paypal_txn_id, int(custom_subscription_id)))
                                
                                sql_insert_txn = """
                                    INSERT INTO transactions 
                                    (user_id, txn_id, amount, currency, status, payment_gateway, transaction_data, created_at) 
                                    VALUES (%s, %s, %s, %s, %s, 'PayPal', %s, %s)
                                """
                                transaction_data_json = json.dumps(res_data)
                                cursor.execute(sql_insert_txn, (
                                    int(custom_subscription_id), paypal_txn_id, float(captured_amount),
                                    captured_currency, payment_status, transaction_data_json, current_ts
                                ))
                                
                                st.success(f"🎉 **Payment Captured Successfully!** Access tokens deployed for corporate user ID {custom_subscription_id}.")
                                st.balloons()
                                
                        conn.close()
                        st.session_state["pending_corp_order_id"] = None
                        st.query_params.clear()
                    except Exception as db_err:
                        st.error(f"Database sync exception: {db_err}")
                else:
                    st.error(f"❌ Payment not completed. Status returned: {payment_status}")
            else:
                st.error(f"❌ Failed to execute order capture command to PayPal endpoints. Status: {cap_response.status_code}")
