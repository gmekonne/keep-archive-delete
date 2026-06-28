import streamlit as st
import requests
import pymysql
import datetime
import json
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
    """Generates an ephemeral bearer access token from PayPal using basic auth."""
    client_id = st.secrets["paypal"]["client_id"]
    client_secret = st.secrets["paypal"]["client_secret"]
    mode = st.secrets["paypal"]["mode"]
    
    base_url = "https://paypal.com" if mode == "sandbox" else "https://paypal.com"
    token_url = f"{base_url}/v1/oauth2/token"
    
    headers = {"Accept": "application/json", "Accept-Language": "en_US"}
    payload = {"grant_type": "client_credentials"}
    
    response = requests.post(token_url, auth=HTTPBasicAuth(client_id, client_secret), headers=headers, data=payload, timeout=10)
    if response.status_code == 200:
        return response.json().get("access_token"), base_url
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
    # FIXED: Replaced the broken empty array lookups with a clean status code validation comparison
    if response.status_code == 201 or response.status_code == 200:
        return response.json()
    return None

st.title("🏢 Corporate & Institutional Portal Registration")
st.write("Register your educational organization, submit purchase requests, and deploy system access tokens via PayPal checkout.")
st.markdown("---")
# 1. UI Information Processing Fields Layer
with st.form("corporate_registration_details_form"):
    corp_name = st.text_input("Organization / University Name *", placeholder="e.g., Global Tech University")
    corp_email = st.text_input("Administrative Account Email *", placeholder="admin@domain.com")
    corp_seats = st.number_input("Target Seat Allocations (Total Instructor Accounts)", min_value=5, max_value=500, value=25, step=5)
    
    calculated_subtotal = float(corp_seats * 10.0)
    st.info(f"🏅 **Enterprise Invoice Quote:** {corp_seats} Teacher Accounts @ $10.00 each = **${calculated_subtotal:.2f} USD / Semester**")
    
    checkout_submit_btn = st.form_submit_button("💳 Initialize Secure PayPal Corporate Checkout", use_container_width=True)

if checkout_submit_btn:
    if not corp_name or not corp_email:
        st.error("All starred fields are required to process your organization registration profile.")
    else:
        with st.spinner("Connecting to PayPal payment gateway servers..."):
            mock_target_uid = st.session_state.get("user_id", 1) 
            
            order_object = create_paypal_order(calculated_subtotal, corp_name, mock_target_uid)
            
            if not order_object:
                st.error("❌ Gateway Connection Error: PayPal rejected the purchase request. Audit your secrets configurations.")
            else:
                paypal_order_id = order_object["id"]
                approve_link = next(link["href"] for link in order_object["links"] if link["rel"] == "approve")
                
                # Cache user parameters safely inside temporary session memory buffers
                st.session_state["pending_corp_order_id"] = paypal_order_id
                st.session_state["pending_corp_name"] = corp_name
                st.session_state["pending_uid"] = mock_target_uid
                
                st.success("🎉 Purchase Order spawned successfully! Please click the authorization button below to finalize your transaction.")
                st.link_button("🚀 Proceed to PayPal Secure Payment Portal", url=approve_link, use_container_width=True)

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
            
            # FIXED: Replaced the broken empty array lookups with a clean status code validation comparison
            if cap_response.status_code == 201 or cap_response.status_code == 200:
                res_data = cap_response.json()
                payment_status = res_data.get("status") 
                
                if payment_status == "COMPLETED":
                    paypal_txn_id = res_data.get("id")
                    
                    purchase_unit = res_data["purchase_units"][0]
                    capture_object = purchase_unit["payments"]["captures"][0]
                    captured_amount = capture_object["amount"]["value"]
                    captured_currency = capture_object["amount"]["currency_code"]
                    
                    custom_subscription_id = purchase_unit.get("custom_id")
                    if not custom_subscription_id:
                        custom_subscription_id = st.session_state.get("pending_uid", 1)
                        
                    try:
                        conn = get_mysql_connection()
                        with conn.cursor() as cursor:
                            # PHP Step 1: Prevent duplicate processing for this txn_id
                            cursor.execute("SELECT COUNT(*) as cnt FROM transactions WHERE txn_id = %s", (paypal_txn_id,))
                            dup_check = cursor.fetchone()
                            
                            if dup_check and dup_check["cnt"] > 0:
                                st.warning("🎉 Payment already processed previously.")
                            else:
                                current_ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                
                                # PHP Step 2: Update user's subscription status using custom ID
                                sql_update_user = """
                                    UPDATE user 
                                    SET subscription_status = 'active', 
                                        last_payment_date = %s, 
                                        paypal_order_id = %s 
                                    WHERE userID = %s
                                """
                                cursor.execute(sql_update_user, (current_ts, paypal_txn_id, int(custom_subscription_id)))
                                
                                # PHP Step 3: Insert transaction auditing ledger record
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
                                
                                st.success(f"🎉 **Payment Captured Successfully!** System access activated for user ID {custom_subscription_id}.")
                                st.balloons()
                                
                        conn.close()
                        st.session_state["pending_corp_order_id"] = None
                        st.query_params.clear()
                    except Exception as db_err:
                        st.error(f"Database sync exception: {db_err}")
                else:
                    st.error(f"❌ Payment not completed. Status returned: {payment_status}")
            else:
                st.error("❌ Failed to execute order capture command to PayPal endpoints.")
