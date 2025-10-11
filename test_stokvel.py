import streamlit as st
from savings import SavingsManager
from payments import PaymentsManager
from notifications import NotificationManager
from security import SecurityManager
from datetime import datetime
from creditscore import predict_credit_score
from loans import create_loan, get_user_loans, grant_loan, record_payment, adjust_credit_score
import numpy as np
import pandas as pd
import requests

API_URL = "http://localhost:8000"
from accounts import AccountManager, AccountType

# ==================================================
# PAGE CONFIG - MUST BE FIRST STREAMLIT COMMAND
# ==================================================
st.set_page_config(
    page_title="AfriScore",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==================================================
# CUSTOM CSS FOR PURPLE & WHITE THEME
# ==================================================
st.markdown("""
<style>
    /* Main color scheme */
    :root {
        --primary-purple: #7C3AED;
        --secondary-purple: #A78BFA;
        --light-purple: #EDE9FE;
        --dark-purple: #5B21B6;
        --white: #FFFFFF;
        --light-gray: #F9FAFB;
        --text-dark: #1F2937;
    }
    
    /* Hide default Streamlit elements on login page */
    .login-page [data-testid="stHeader"] {
        display: none;
    }
    
    /* Logo styling */
    .logo-container {
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .logo-container img {
        max-width: 150px;
        height: auto;
        margin-bottom: 1rem;
    }
    
    /* Login container styling */
    .login-container {
        max-width: 450px;
        margin: 0 auto;
        padding: 3rem 2rem;
        background: white;
        border-radius: 20px;
        box-shadow: 0 10px 40px rgba(124, 58, 237, 0.1);
        margin-top: 5vh;
    }
    
    /* Hide streamlit image container styling */
    .login-container [data-testid="stImage"] {
        text-align: center;
    }
    
    .login-container [data-testid="stImage"] > img {
        margin: 0 auto;
    }
    
    .login-header {
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .login-header h1 {
        color: var(--primary-purple);
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    .login-header p {
        color: var(--text-dark);
        font-size: 1rem;
        opacity: 0.7;
    }
    
    /* Input field styling */
    .stTextInput > div > div > input {
        border: 2px solid #E5E7EB;
        border-radius: 10px;
        padding: 12px 16px;
        font-size: 1rem;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: var(--primary-purple);
        box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.1);
    }
    
    /* Button styling */
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, var(--primary-purple), var(--dark-purple));
        color: white;
        border: none;
        border-radius: 10px;
        padding: 12px 24px;
        font-size: 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
        margin-top: 1rem;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 25px rgba(124, 58, 237, 0.3);
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: var(--light-gray);
        padding: 8px;
        border-radius: 12px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border-radius: 8px;
        color: var(--text-dark);
        font-weight: 500;
        padding: 10px 20px;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: var(--primary-purple) !important;
        color: white !important;
    }
    
    /* Metric cards */
    [data-testid="stMetricValue"] {
        color: var(--primary-purple);
        font-size: 1.8rem;
        font-weight: 700;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: var(--light-purple);
        border-radius: 10px;
        color: var(--dark-purple);
        font-weight: 600;
    }
    
    /* Success/Error messages */
    .stSuccess {
        background-color: #D1FAE5;
        color: #065F46;
        border-radius: 10px;
        padding: 1rem;
    }
    
    .stError {
        background-color: #FEE2E2;
        color: #991B1B;
        border-radius: 10px;
        padding: 1rem;
    }
    
    .stWarning {
        background-color: #FEF3C7;
        color: #92400E;
        border-radius: 10px;
        padding: 1rem;
    }
    
    .stInfo {
        background-color: var(--light-purple);
        color: var(--dark-purple);
        border-radius: 10px;
        padding: 1rem;
    }
    
    /* Divider */
    hr {
        border-color: var(--light-purple);
        margin: 2rem 0;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--primary-purple), var(--dark-purple));
        color: white;
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: white;
    }
    
    /* Container styling */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Welcome banner */
    .welcome-banner {
        background: linear-gradient(135deg, var(--primary-purple), var(--dark-purple));
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
    }
    
    .welcome-banner h1 {
        margin: 0;
        font-size: 2rem;
    }
    
    /* Logout button */
    .logout-btn {
        position: fixed;
        top: 1rem;
        right: 1rem;
        z-index: 999;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .login-container {
            padding: 2rem 1.5rem;
            margin-top: 2vh;
        }
        
        .login-header h1 {
            font-size: 2rem;
        }
        
        .welcome-banner h1 {
            font-size: 1.5rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# ==================================================
# INITIALIZE MANAGERS IN SESSION STATE
# ==================================================
if 'account_manager' not in st.session_state:
    st.session_state.account_manager = AccountManager()
if 'savings_manager' not in st.session_state:
    st.session_state.savings_manager = SavingsManager()
if 'notifications_manager' not in st.session_state:
    st.session_state.notifications_manager = NotificationManager()
if 'security_manager' not in st.session_state:
    st.session_state.security_manager = SecurityManager()
if 'payments_manager' not in st.session_state:
    st.session_state.payments_manager = PaymentsManager(
        savings_manager=st.session_state.savings_manager,
        security_manager=st.session_state.security_manager
    )

# ==================================================
# LOGIN STATE MANAGEMENT
# ==================================================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'current_user' not in st.session_state:
    st.session_state.current_user = None
if 'users_db' not in st.session_state:
    # Simple user database (in production, use proper database)
    st.session_state.users_db = {
        "user_001": {"password": "password123", "name": "Demo User"}
    }

# ==================================================
# LOGIN/SIGNUP FUNCTIONS
# ==================================================
def login_user(user_id, password):
    """Authenticate user"""
    if user_id in st.session_state.users_db:
        if st.session_state.users_db[user_id]["password"] == password:
            st.session_state.logged_in = True
            st.session_state.current_user = user_id
            return True, "Login successful!"
        else:
            return False, "Incorrect password"
    else:
        return False, "Username not found"

def signup_user(user_id, password, name):
    """Register new user"""
    if user_id in st.session_state.users_db:
        return False, "Username already exists"
    
    st.session_state.users_db[user_id] = {
        "password": password,
        "name": name
    }
    st.session_state.logged_in = True
    st.session_state.current_user = user_id
    return True, "Account created successfully!"

def logout_user():
    """Logout current user"""
    st.session_state.logged_in = False
    st.session_state.current_user = None
    st.rerun()

# ==================================================
# LOGIN/SIGNUP PAGE
# ==================================================
def show_login_page():
    st.markdown('<div class="login-page">', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Logo - centered
        try:
            st.image("AfriScore_logo.jpg", width=230,use_container_width=False)
        except:
            # Fallback if logo file not found
            st.markdown('<div style="text-align: center;"><h3>🌍 AfriScore</h3></div>', unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["🔐 Login", "📝 Sign Up"])
        
        with tab1:
            st.markdown("### Welcome Back")
            login_user_id = st.text_input("Username", key="login_user_id", placeholder="Enter your username")
            login_password = st.text_input("Password", type="password", key="login_password", placeholder="Enter your password")
            
            if st.button("Login", key="login_btn", use_container_width=True):
                if login_user_id and login_password:
                    success, message = login_user(login_user_id, login_password)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.warning("Please fill in all fields")
        
        with tab2:
            st.markdown("### Create Account")
            signup_name = st.text_input("Full Name", key="signup_name", placeholder="Enter your full name")
            signup_user_id = st.text_input("Username", key="signup_user_id", placeholder="Choose a username")
            signup_password = st.text_input("Password", type="password", key="signup_password", placeholder="Choose a password")
            signup_confirm = st.text_input("Confirm Password", type="password", key="signup_confirm", placeholder="Re-enter password")
            
            if st.button("Sign Up", key="signup_btn", use_container_width=True):
                if signup_name and signup_user_id and signup_password and signup_confirm:
                    if signup_password == signup_confirm:
                        success, message = signup_user(signup_user_id, signup_password, signup_name)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                    else:
                        st.error("Passwords do not match")
                else:
                    st.warning("Please fill in all fields")
    
    st.markdown('</div>', unsafe_allow_html=True)

# ==================================================
# MAIN APP - SHOW LOGIN OR HOME
# ==================================================
if not st.session_state.logged_in:
    show_login_page()
    st.stop()

# ==================================================
# USER IS LOGGED IN - SHOW MAIN APP
# ==================================================
# Logout button
col1, col2, col3 = st.columns([6, 1, 1])
with col3:
    if st.button("🚪 Logout", key="logout_btn"):
        logout_user()

# Welcome banner
user_name = st.session_state.users_db[st.session_state.current_user]["name"]

# Display logo in main app
col_logo1, col_logo2, col_logo3 = st.columns([1, 2, 1])
with col_logo2:
    try:
        st.image("AfriScore_logo.jpg", width=230)
    except:
        st.markdown("### 🌍 AfriScore")

st.markdown(f"""
<div class="welcome-banner">
    <h1>Welcome back, {user_name}! 👋</h1>
    <p>Manage your savings and stokvels with ease</p>
</div>
""", unsafe_allow_html=True)

# ==================================================
# ALIASES
# ==================================================
manager = st.session_state.savings_manager
payments = st.session_state.payments_manager
security = st.session_state.security_manager
notifs = st.session_state.notifications_manager
current_user = st.session_state.current_user

def get_user_financial_data(manager, user_id):
    data = {
        "savings": 0.0,
        "stockvel_contribution": 0.0,
        "monthly_payments": 0.0,
        "outstanding_loans": 0.0,
    }
    try:
        savings = manager.get_individual_savings(user_id)
        data["savings"] = sum(c["amount"] for c in savings.contributions)
    except ValueError:
        pass
    user_stokvels = manager.get_user_stokvels(user_id)
    if user_stokvels:
        data["stockvel_contribution"] = sum(s["monthly_amount"] for s in user_stokvels)
    # Demo placeholders for monthly payments and loans
    utility_score = np.random.uniform(0.3, 0.9)
    data["monthly_payments"] = utility_score * 5000
    mobile_activity = len(user_stokvels) * 10 if user_stokvels else 0
    data["outstanding_loans"] = mobile_activity * 100
    return data

# ==================================================
# SIDEBAR USER INFO & NOTIFICATIONS
# ==================================================
with st.sidebar:
    st.markdown(f"### 👤 {user_name}")
    st.markdown(f"**Username:** {st.session_state.current_user}")
    st.divider()
    
    # 🔔 Notifications summary
    unread_count = notifs.get_unread_count(st.session_state.current_user)
    st.markdown(f"### 🔔 Notifications ({unread_count})")
    
    with st.expander("View All Notifications"):
        user_notifs = notifs.get_user_notifications(st.session_state.current_user)
        if not user_notifs:
            st.write("No notifications yet.")
        else:
            for n in user_notifs[:10]:
                st.write(f"🕒 {n['created_at'].strftime('%Y-%m-%d %H:%M')} — {n['message']}")
                if not n['read']:
                    notifs.mark_notification_read(n['notification_id'], st.session_state.current_user)
    
    st.divider()
    
    # Debug info COMMENTED OUT FOR NOW
    #ith st.expander("🔧 Debug Info"):
        #t.write("**All Stokvels:**", list(manager.stokvels.keys()))
        #t.write("**All Savings Accounts:**", list(manager.individual_savings.keys()))
        #t.write("**All PINs:**", [p['pin_code'] for p in payments.get_user_pins(st.session_state.current_user, include_expired=True)])

# ==================================================
# MAIN TABS
# ==================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🤝 Stokvel Savings", "💵 Individual Savings", "🏧 Withdrawals", "💳 Credit Score", "🏦 Loans"])

# ==================================================
# STOKVEL TAB
# ==================================================
with tab1:
    st.header("Stokvel Management")
    
    with st.expander("➕ Create New Stokvel", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            stokvel_name = st.text_input("Stokvel Name")
            stokvel_id = st.text_input("Stokvel ID (unique)")
        with col2:
            monthly_amount = st.number_input(
                "Monthly Amount (R)",
                min_value=10.0,
                max_value=5000.0,
                value=500.0
            )
        if st.button("Create Stokvel"):
            try:
                stokvel = manager.create_stokvel(
                    stokvel_id,
                    stokvel_name,
                    st.session_state.current_user,
                    monthly_amount
                )
                st.success(f"✅ Stokvel '{stokvel_name}' created successfully!")
            except ValueError as e:
                st.error(f"❌ {str(e)}")
    
    st.subheader("Your Stokvels")
    user_stokvels = manager.get_user_stokvels(st.session_state.current_user)
    
    if user_stokvels:
        for stokvel_data in user_stokvels:
            with st.container():
                st.markdown(f"### {stokvel_data['name']}")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Saved", f"R{stokvel_data['total_contributions']:,.2f}")
                with col2:
                    st.metric("Members", stokvel_data['member_count'])
                with col3:
                    st.metric("Monthly Target", f"R{stokvel_data['monthly_amount']:,.2f}")
                
                # Add Contribution
                with st.expander("💸 Add Contribution (Deposit via Store)"):
                    contribution_amount = st.number_input(
                        "Amount (R)",
                        min_value=10.0,
                        max_value=5000.0,
                        key=f"contrib_{stokvel_data['stokvel_id']}"
                    )
                    if st.button("Generate Deposit PIN", key=f"deposit_{stokvel_data['stokvel_id']}"):
                        try:
                            stokvel = manager.get_stokvel(stokvel_data['stokvel_id'])
                            # Generate PIN using existing method for deposit
                            pin = payments.request_stokvel_withdrawal(st.session_state.current_user, stokvel_data['stokvel_id'])
                            st.success(f"✅ Deposit PIN generated: **{pin.pin_code}** — Amount: R{contribution_amount:,.2f}")
                        except ValueError as e:
                            st.error(f"❌ {str(e)}")
                
                with st.expander("👥 View Members"):
                    for member_id, member_data in stokvel_data['members'].items():
                        emoji = "✅" if member_data['status'] == "accepted" else "⏳" if member_data['status'] == "pending" else "❌"
                        st.write(f"{emoji} **{member_id}** — R{member_data['total_contributed']:,.2f} ({member_data['status']})")
                
                st.divider()
    else:
        st.info("You are not part of any stokvel yet. Create one or wait for an invitation.")
    
    # Invitations
    with st.expander("📨 Manage Stokvel Invitations"):
        existing_stokvel_id = st.selectbox(
            "Select Stokvel",
            options=list(manager.stokvels.keys()) if manager.stokvels else ["No stokvels available"]
        )
        if existing_stokvel_id != "No stokvels available":
            action = st.radio("Action", ["Invite Member", "Accept Invitation", "Reject Invitation"])
            member_id_input = st.text_input("Member ID", key="member_invite")
            
            if st.button("Execute Action"):
                try:
                    stokvel = manager.get_stokvel(existing_stokvel_id)
                    if action == "Invite Member":
                        stokvel.invite_member(member_id_input, st.session_state.current_user)
                        notifs.send_stokvel_invitation_notification(
                            st.session_state.current_user, stokvel.name, st.session_state.current_user, member_id_input, stokvel.monthly_amount
                        )
                        st.success(f"✅ Invited {member_id_input} to stokvel")
                    elif action == "Accept Invitation":
                        stokvel.accept_invitation(member_id_input)
                        st.success(f"✅ {member_id_input} accepted invitation")
                    else:
                        stokvel.reject_invitation(member_id_input)
                        st.warning(f"⚠️ {member_id_input} rejected invitation")
                except ValueError as e:
                    st.error(f"❌ {str(e)}")

# ==================================================
# INDIVIDUAL SAVINGS TAB
# ==================================================
with tab2:
    st.header("Individual Savings")
    
    try:
        individual_savings = manager.get_individual_savings(st.session_state.current_user)
    except ValueError:
        with st.expander("➕ Create Savings Account", expanded=True):
            goal = st.number_input("Set Savings Goal (R)", min_value=10.0, value=5000.0)
            if st.button("Create Savings Account"):
                manager.create_individual_savings(st.session_state.current_user, goal if goal > 0 else None)
                st.success("✅ Savings account created!")
        st.stop()
    
    summary = individual_savings.get_savings_summary()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Saved", f"R{summary['total_saved']:,.2f}")
    with col2:
        if summary['savings_goal']:
            st.metric("Goal", f"R{summary['savings_goal']:,.2f}")
    with col3:
        progress = summary['progress_percentage']
        if progress:
            st.metric("Progress", f"{progress:.1f}%")
    
    if summary['progress_percentage']:
        st.progress(min(summary['progress_percentage'] / 100, 1.0))
    
    st.divider()
    
    st.subheader("💵 Add Money (Deposit via Store)")
    col1, col2 = st.columns([3, 1])
    with col1:
        amount = st.number_input("Amount (R)", min_value=0.0, max_value=5000.0, value=100.0)
    with col2:
        st.write("")
        if st.button("Generate Deposit PIN", type="primary"):
            try:
                # Use existing withdrawal method to generate a deposit PIN
                pin = payments.request_individual_withdrawal(st.session_state.current_user, amount)
                st.success(f"✅ Deposit PIN generated: **{pin.pin_code}** — Amount: R{amount:,.2f}")
            except ValueError as e:
                st.error(f"❌ {str(e)}")
    
    with st.expander("🎯 Update Goal"):
        new_goal = st.number_input("New Goal (R)", min_value=0.0, value=summary['savings_goal'] or 10000.0)
        if st.button("Update Goal"):
            individual_savings.set_savings_goal(new_goal)
            st.success(f"✅ Goal updated to R{new_goal:,.2f}")

# ==================================================
# WITHDRAWALS TAB
# ==================================================
with tab3:
    st.header("🏧 Withdraw Money")
    
    subtab1, subtab2 = st.tabs(["💰 Individual Savings Withdrawal", "👥 Stokvel Payout Withdrawal"])
    
    # ---------------------------
    # Individual Savings Withdraw
    # ---------------------------
    with subtab1:
        st.subheader("Withdraw from Individual Savings")
        try:
            total_saved = manager.get_individual_savings(st.session_state.current_user).get_total_savings()
            st.info(f"Available Balance: R{total_saved:,.2f}")
            
            amount = st.number_input("Withdrawal Amount (R)", min_value=50.0, max_value=5000.0, value=100.0)
            
            if st.button("Request Withdrawal", key="req_ind_withdraw"):
                allowed, msg = security.verify_withdrawal_request(st.session_state.current_user, amount)
                if not allowed:
                    st.warning(msg)
                else:
                    try:
                        pin = payments.request_individual_withdrawal(st.session_state.current_user, amount)
                        st.success(f"✅ Withdrawal PIN generated: **{pin.pin_code}** — Amount: R{amount:,.2f}")
                    except ValueError as e:
                        st.error(f"❌ {str(e)}")
        except ValueError:
            st.warning("No individual savings account found.")
    
    # ---------------------------
    # Stokvel Withdraw
    # ---------------------------
    with subtab2:
        st.subheader("Withdraw from Stokvel")
        stokvel_options = list(manager.stokvels.keys())
        
        if stokvel_options:
            stokvel_id = st.selectbox("Select Stokvel", stokvel_options, key="select_stokvel")
            
            if st.button("Request Stokvel Payout", key="req_stok_payout"):
                try:
                    pin = payments.request_stokvel_withdrawal(st.session_state.current_user, stokvel_id)
                    st.success(f"✅ Stokvel withdrawal PIN: **{pin.pin_code}**")
                except ValueError as e:
                    st.error(f"❌ {str(e)}")
        else:
            st.info("No stokvels available for withdrawal yet.")

# ==================================================
# CREDIT SCORE TAB
# ==================================================
with tab4:
    st.header("💳 Credit Score Estimator")
    
    user_data = get_user_financial_data(manager, st.session_state.current_user)
    base_score = predict_credit_score(user_data)
    
    # Adjust score automatically based on loan repayment history
    credit_score = adjust_credit_score(base_score, current_user)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.metric("Your Credit Score", f"{credit_score:.0f}", help="Based on your financial activity")
    
    if credit_score >= 700:
        st.success("✅ Excellent Credit: Low risk borrower.")
    elif credit_score >= 600:
        st.info("🟨 Fair Credit: Moderate risk borrower.")
    else:
        st.warning("⚠️ Poor Credit: High risk borrower.")

# ==================================================
# LOANS TAB
# ==================================================
with tab5:
    st.header("🏦 Loans Management")
    
    st.subheader("📩 Request a New Loan")
    
    col1, col2 = st.columns(2)
    with col1:
        amount = st.number_input("Loan Amount (R)", min_value=100.0)
    with col2:
        months = st.number_input("Repayment Months", min_value=1, max_value=12, step=1)
    
    if st.button("Request Loan", type="primary"):
        otp = create_loan(current_user, amount, months)
        st.success(f"✅ Loan requested successfully! OTP for store collection: **{otp}**")
    
    st.divider()
    
    # View Outstanding Loans
    st.subheader("📄 Outstanding Loans")
    user_loans = get_user_loans(current_user)
    
    if not user_loans:
        st.info("No loans yet.")
    else:
        for i, loan in enumerate(user_loans):
            with st.container():
                status = "✅ Repaid" if loan["repaid"] else "⏳ Ongoing"
                st.markdown(f"### Loan {i+1} - {status}")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Amount", f"R{loan['amount']:,.2f}")
                with col2:
                    st.metric("Monthly Installment", f"R{loan['installment']:,.2f}")
                with col3:
                    st.metric("Payments Made", f"{len(loan['payments'])}/{loan['months']}")
                
                st.write(f"**Due Dates:** {', '.join(loan['due_dates'])}")
                
                if not loan["repaid"]:
                    st.info("💡 Payments are made in person at the store. Your loan status will update automatically once the store records the payment.")
                
                st.divider()








