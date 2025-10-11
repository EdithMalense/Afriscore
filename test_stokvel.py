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
# ALIASES
# ==================================================
manager = st.session_state.savings_manager
payments = st.session_state.payments_manager
security = st.session_state.security_manager
notifs = st.session_state.notifications_manager

# ==================================================
# DEFAULT USER
# ==================================================
if 'current_user' not in st.session_state:

    st.session_state.current_user = "user_001"  # Default test user

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
    st.session_state.current_user = "user_001"

st.title("💰 Savings Profile Manager")

# ==================================================
# SIDEBAR USER SELECTION
# ==================================================
with st.sidebar:
    st.header("👤 Test User")
    st.session_state.current_user = st.text_input(
        "Current User ID",
        value=st.session_state.current_user
    )
    st.info(f"Logged in as: {st.session_state.current_user}")

    # 🔔 Notifications summary
    unread_count = notifs.get_unread_count(st.session_state.current_user)
    st.markdown(f"🔔 **Unread Notifications:** {unread_count}")

    with st.expander("View Notifications"):
        user_notifs = notifs.get_user_notifications(st.session_state.current_user)
        if not user_notifs:
            st.write("No notifications yet.")
        else:
            for n in user_notifs[:10]:
                st.write(f"🕒 {n['created_at'].strftime('%Y-%m-%d %H:%M')} — {n['message']}")
                if not n['read']:
                    notifs.mark_notification_read(n['notification_id'], st.session_state.current_user)

# ==================================================
# MAIN TABS
# ==================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🤝 Stokvel Savings", "💵 Individual Savings", "Withdrawals", "Credit Score", "Loans"])

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

## ============================================
# CREDIT SCORE TAB
# ============================================
with tab4:
    st.header("💳 Credit Score Estimator & Loans")

    user_data = get_user_financial_data(manager, st.session_state.current_user)
    base_score = predict_credit_score(user_data)

    # Adjust score automatically based on loan repayment history
    credit_score = adjust_credit_score(base_score, current_user)

    st.metric("Predicted Credit Score", f"{credit_score:.0f}")
    if credit_score >= 700:
        st.success("✅ Excellent Credit: Low risk borrower.")
    elif credit_score >= 600:
        st.info("🟨 Fair Credit: Moderate risk borrower.")
    else:
        st.warning("⚠️ Poor Credit: High risk borrower.")


# ============================================
# LOANS TAB
# ============================================
with tab5:
    st.subheader("📩 Request a New Loan")
    amount = st.number_input("Loan Amount (R)", min_value=100.0)
    months = st.number_input("Repayment Months", min_value=1, max_value=12, step=1)
    if st.button("Request Loan"):
        otp = create_loan(current_user, amount, months)
        st.success(f"Loan requested. OTP for store collection: {otp}")

    # View Outstanding Loans
    st.subheader("📄 Outstanding Loans")
    user_loans = get_user_loans(current_user)

    if not user_loans:
        st.info("No loans yet.")
    else:
        for i, loan in enumerate(user_loans):
            status = "✅ Repaid" if loan["repaid"] else "⏳ Ongoing"
            st.write(f"Loan {i+1}: R{loan['amount']} | Installment: R{loan['installment']} | Status: {status}")
            st.write(f"Due Dates: {', '.join(loan['due_dates'])}")
            st.write(f"Payments made: {len(loan['payments'])}/{loan['months']}")

            if not loan["repaid"]:
                st.info("Payments are made in person at the store. Your loan status will update automatically once the store records the payment.")

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
# DEBUG INFO
# ==================================================
with st.sidebar.expander("🔧 Debug Info"):
    st.write("**All Stokvels:**", list(manager.stokvels.keys()))
    st.write("**All Savings Accounts:**", list(manager.individual_savings.keys()))
    st.write("**All PINs:**", [p['pin_code'] for p in payments.get_user_pins(st.session_state.current_user, include_expired=True)])








