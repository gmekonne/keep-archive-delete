import streamlit as st
import pymysql
import datetime
import hashlib
import json
import urllib.parse

# =====================================================================
# SECTION 1: DATABASE CONNECTION INFRASTRUCTURE
# What it does: Establishes a live link to your Hostinger database.
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

if "corp_form_validated" not in st.session_state:
    st.session_state["corp_form_validated"] = False

# =====================================================================
# SECTION 2: THE REGISTRATION FORM (STEP 1)
# What it does: Captures text data and runs pre-flight duplicate scans on submit.
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
# SECTION 3 & 4: VISUAL PAYPAL BUTTON ENGINE & BACKGROUND PROCESSOR (STEP 2)
# What it does: Runs ONLY when validated. Mounts buttons and turns on the
# event listener inside a protective shell to stop loop-crashes entirely.
# =====================================================================
if st.session_state["corp_form_validated"]:
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
    if mode == "sandbox":
        paypal_client_id = str(st.secrets["paypal"]["sandbox_client_id"]).strip()
        st.caption("🛡️ Gateway Status: **🟢 SANDBOX SIMULATION ENGAGED**")
    else:
        paypal_client_id = str(st.secrets["paypal"]["live_client_id"]).strip()
        st.caption("🛡️ Gateway Status: **🚨 LIVE PRODUCTION ENGAGED**")

    # Construct clean raw source code block
    paypal_smart_buttons_html = f"""<!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <script src="https://paypal.com{paypal_client_id}&currency=USD"></script>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: transparent; margin: 0; padding: 5px; }}
            #paypal-button-container {{ max-width: 100%; margin-top: 5px; }}
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
    </html>"""
    
    safe_encoded_src_url = "data:text/html;charset=utf-8," + urllib.parse.quote(paypal_smart_buttons_html)
    
    st.iframe(src=safe_encoded_src_url, height=320)

    # 🟢 LOCKED COUPLING: The JS evaluation module now runs ONLY inside this protected block container
    from streamlit_js_eval import streamlit_js_eval

    js_listener_script = """
    (function() {
        return new Promise((resolve) => {
            window.addEventListener('message', function(event) {
                if (event.data && event.data.type === 'streamlit:paypal_success') {
                    resolve(event.data);
                }
            });
            setTimeout(() => resolve(null), 600);
        });
    })()
    """

    paypal_event_payload = streamlit_js_eval(js_script=js_listener_script, key="paypal_bridge_listener_loop_v10")

    if paypal_event_payload:
        paypal_order_id = paypal_event_payload.get("orderID")
        payment_status = paypal_event_payload.get("status")
        captured_amount = paypal_event_payload.get("amount")
        captured_currency = paypal_event_payload.get("currency")
        full_raw_json_str = paypal_event_payload.get("raw_json")
        
        if payment_status == "COMPLETED" and paypal_order_id:
            st.info("⚡ Transaction validated by PayPal. Completing database synchronization loops...")
            
            try:
                current_ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                with get_mysql_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT COUNT(*) as cnt FROM transactions WHERE txn_id = %s", (paypal_order_id,))
                        dup_check = cursor.fetchone()
                        
                        if dup_check and dup_check["cnt"] > 0:
                            st.warning("🎉 Payment already processed previously.")
                        else:
                            hashed_password_string = hashlib.sha256(c_pass.encode('utf-8')).hexdigest()
                            
                            sql_insert_user = """
                                INSERT INTO user (fname, lname, corp_name, email, password, acct_type, subscription_status, dateCreated, role, user_role, paypal_order_id, last_payment_date) 
                                VALUES (%s, %s, %s, %s, %s, 'corporate', 'active', %s, 'instructor', 'instructor', %s, %s)
                            """
                            cursor.execute(sql_insert_user, (
                                c_fname, c_lname, c_name, c_email, 
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
                            
                            st.success(f"🎉 **Corporate Profile Deployed Successfully!** Account created with User ID **{new_corporate_userid}**.")
                            st.balloons()
                            st.session_state["corp_form_validated"] = False
                st.rerun()
            except Exception as db_err:
                st.error(f"❌ Database Transaction Synchronization Failure: {db_err}")
st.markdown("---")
