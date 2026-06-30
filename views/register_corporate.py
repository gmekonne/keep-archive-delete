import streamlit as st
import pymysql
import datetime
import hashlib
import json

# =====================================================================
# SECTION 1: DATABASE CONNECTION INFRASTRUCTURE & HELPER FUNCTIONS
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

st.title("🏢 Corporate & Institutional Portal Registration")
st.write("Register your educational organization and process your enterprise purchase order using the live secure PayPal interface buttons below.")
st.markdown("---")

# =====================================================================
# SECTION 2: CORPORATE ONBOARDING INFORMATION FORM (STABLE STATES)
# What it does: Captures user profile fields natively into state memory blocks.
# =====================================================================
with st.container(border=True):
    st.markdown("##### 📝 Step 1: Administrative Account Specifications")
    
    col_n1, col_n2 = st.columns(2)
    with col_n1:
        st.text_input("First Name *", placeholder="e.g., John", key="corp_fname")
    with col_n2:
        st.text_input("Last Name *", placeholder="e.g., Smith", key="corp_lname")
        
    st.text_input("Organization / University Name *", placeholder="e.g., Global Tech University", key="corp_org")
    st.text_input("Administrative Account Email *", placeholder="admin@domain.com", key="corp_email")
    st.text_input("Create Portal Access Password *", type="password", placeholder="Choose a strong password string", key="corp_pass")
    st.number_input("Target Seat Allocations (Instructor Accounts)", min_value=5, max_value=500, value=25, step=5, key="corp_seats")
    
    # Read variables directly from stable memory state lines to calculate price subtotals
    seats_val = st.session_state.get("corp_seats", 25)
    calculated_subtotal = float(seats_val * 10.0)
    st.info(f"🏅 **Enterprise Invoice Quote:** {seats_val} Teacher Accounts @ $10.00 each = **${calculated_subtotal:.2f} USD / Semester**")
# =====================================================================
# SECTION 3: EMBEDDED JAVASCRIPT PAYPAL BUTTON ENGINE (THE UI LAYER)
# What it does: Mounts the native yellow PayPal smart buttons inside an iframe.
# =====================================================================
st.markdown("---")
st.markdown("##### 💳 Step 2: Live Payment Processing Portal")

mode = str(st.secrets["paypal"].get("mode", "sandbox")).strip().lower()
if mode == "sandbox":
    paypal_client_id = str(st.secrets["paypal"]["sandbox_client_id"]).strip()
    st.caption("🛡️ Gateway Status: **... SANDBOX SIMULATION ENGAGED** (Test Accounts Active)")
else:
    paypal_client_id = str(st.secrets["paypal"]["live_client_id"]).strip()
    st.caption("🛡️ Gateway Status: **... LIVE PRODUCTION ENGAGED** (Processing Real Funds)")

# 🟢 FIXED LOGIC FILTER: Reads straight from stable session keys to guarantee instant unlocking
f_name = st.session_state.get("corp_fname", "").strip()
l_name = st.session_state.get("corp_lname", "").strip()
c_name = st.session_state.get("corp_org", "").strip()
c_email = st.session_state.get("corp_email", "").strip()
c_pass = st.session_state.get("corp_pass", "").strip()

if not f_name or not l_name or not c_name or not c_email or not c_pass:
    st.warning("... Form Locked: Please fill out all required account fields above to unlock the secure PayPal buttons module.")
else:
    # Clear the warning box and compile the custom visual buttons frame
    paypal_smart_buttons_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <script src="https://paypal.com{paypal_client_id}&currency=USD"></script>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: transparent; margin: 0; padding: 10px; }}
            #paypal-button-container {{ max-width: 100%; margin-top: 10px; }}
        </style>
    </head>
    <body>
        <div id="paypal-button-container"></div>
        <script>
            paypal.Buttons({{
                createOrder: function(data, actions) {{
                    return actions.order.create({{
                        purchase_units: [{{
                            description: "CPMS Enterprise Activation: {c_name}",
                            amount: {{ currency_code: "USD", value: "{calculated_subtotal:.2f}" }}
                        }}]
                    }});
                }},
                onApprove: function(data, actions) {{
                    return actions.order.capture().then(function(details) {{
                        // 🟢 FIXED OBJECT EXPLORATION: Target the exact array list mapping used by PayPal responses
                        var capture = details.purchase_units[0].payments.captures[0];
                        window.parent.postMessage({{
                            type: 'streamlit:paypal_success',
                            orderID: details.id,
                            amount: capture.amount.value,
                            currency: capture.amount.currency_code,
                            status: details.status,
                            raw_json: JSON.stringify(details)
                        }}, '*');
                    }});
                }},
                onError: function(err) {{
                    console.error("PayPal Error Interface Callback:", err);
                }}
            }}).render('#paypal-button-container');
        </script>
    </body>
    </html>
    """
    st.components.v1.html(paypal_smart_buttons_html, height=280, scrolling=False)

# =====================================================================
# SECTION 4: THE PYTHON PROCESSOR LOOP (THE BACKEND DATA CAPTURER)
# What it does: Listens for the successful payment transaction payload message.
# =====================================================================
from streamlit_js_eval import streamlit_js_eval

js_listener_script = """
(function() {
    return new Promise((resolve) => {
        window.addEventListener('message', function(event) {
            if (event.data && event.data.type === 'streamlit:paypal_success') {
                resolve(event.data);
            }
        });
        setTimeout(() => resolve(null), 500);
    });
})()
"""

paypal_event_payload = streamlit_js_eval(js_script=js_listener_script, key="paypal_bridge_listener_loop_v3")

if paypal_event_payload and f_name and c_email:
    paypal_order_id = paypal_event_payload.get("orderID")
    payment_status = paypal_event_payload.get("status")
    captured_amount = paypal_event_payload.get("amount")
    captured_currency = paypal_event_payload.get("currency")
    full_raw_json_str = paypal_event_payload.get("raw_json")
    
    if payment_status == "COMPLETED" and paypal_order_id:
        st.info("... Transaction validated by PayPal. Completing database synchronization loops...")
        target_email_clean = c_email.lower().strip()
        
        try:
            conn = get_mysql_connection()
            current_ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            with conn.cursor() as cursor:
                cursor.execute("SELECT userID FROM user WHERE LOWER(email) = %s", (target_email_clean,))
                duplicate_user_found = cursor.fetchone()
                
                if duplicate_user_found:
                    st.warning("... Transaction captured, but this email address is already active in the user records.")
                else:
                    hashed_password_string = hashlib.sha256(c_pass.encode('utf-8')).hexdigest()
                    
                    sql_insert_user = """
                        INSERT INTO user (fname, lname, corp_name, email, password, acct_type, subscription_status, dateCreated, role, user_role, paypal_order_id, last_payment_date) 
                        VALUES (%s, %s, %s, %s, %s, 'corporate', 'active', %s, 'instructor', 'instructor', %s, %s)
                    """
                    cursor.execute(sql_insert_user, (
                        f_name, l_name, c_name, target_email_clean, 
                        hashed_password_string, current_ts, paypal_order_id, current_ts
                    ))
                    
                    new_corporate_userid = cursor.lastrowid
                    
                    sql_insert_txn = """
                        INSERT INTO transactions 
                        (user_id, txn_id, amount, currency, status, payment_gateway, transaction_data, created_at) 
                        VALUES (%s, %s, %s, %s, %s, 'PayPal', %s, %s)
                    """
                    cursor.execute(sql_insert_txn, (
                        int(new_corporate_userid), paypal_order_id, float(captured_amount),
                        captured_currency, payment_status, full_raw_json_str, current_ts
                    ))
                    
                    st.success(f"... **Corporate Profile Deployed Successfully!** Account created with User ID **{new_corporate_userid}**.")
                    st.balloons()
            conn.close()
        except Exception as db_err:
            st.error(f"... Database Transaction Synchronization Failure: {db_err}")
st.markdown("---")
