import streamlit as st
from savings import SavingsManager, Stokvel, IndividualSavings
from datetime import datetime
from creditscore import predict_credit_score
from loans import create_loan, get_user_loans, grant_loan, record_payment, adjust_credit_score
import numpy as np
import pandas as pd
import requests


API_URL = "http://localhost:8000"

# Initialize session state
if 'manager' not in st.session_state:
    st.session_state.manager = SavingsManager()

if 'current_user' not in st.session_state:
    st.session_state.current_user = "user_001"  # Default test user

current_user = st.session_state.current_user
manager = st.session_state.manager

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

st.title("💰 Savings Profile Manager")

# Sidebar for user selection (for testing multiple users)
with st.sidebar:
    st.header("Test User")
    st.session_state.current_user = st.text_input(
        "Current User ID", 
        value=st.session_state.current_user
    )
    st.info(f"Logged in as: {st.session_state.current_user}")

# Main tabs
tab1, tab2, tab3, tab4 = st.tabs(["Stokvel Savings", "Individual Savings", "Credit Score", "Loans"])

# ============================================
# STOKVEL TAB
# ============================================
with tab1:
    st.header("Stokvel Management")
    
    # Create Stokvel Section
    with st.expander("➕ Create New Stokvel", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            stokvel_name = st.text_input("Stokvel Name")
            stokvel_id = st.text_input("Stokvel ID (unique)")
        with col2:
            monthly_amount = st.number_input(
                "Monthly Amount (R)", 
                min_value=0.0, 
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
    
    # View User's Stokvels
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
                with st.expander("💸 Add Contribution"):
                    contribution_amount = st.number_input(
                        "Amount (R)", 
                        min_value=0.0, 
                        max_value=5000.0,
                        key=f"contrib_{stokvel_data['stokvel_id']}"
                    )
                    if st.button("Add Contribution", key=f"add_{stokvel_data['stokvel_id']}"):
                        try:
                            stokvel = manager.get_stokvel(stokvel_data['stokvel_id'])
                            stokvel.add_contribution(
                                st.session_state.current_user, 
                                contribution_amount
                            )
                            st.success(f"✅ Added R{contribution_amount:,.2f}")
                            st.rerun()
                        except ValueError as e:
                            st.error(f"❌ {str(e)}")
                
                # View Members
                with st.expander("👥 View Members"):
                    for member_id, member_data in stokvel_data['members'].items():
                        status_emoji = "✅" if member_data['status'] == "accepted" else "⏳" if member_data['status'] == "pending" else "❌"
                        st.write(f"{status_emoji} **{member_id}**: R{member_data['total_contributed']:,.2f} ({member_data['status']})")
                
                st.divider()
    else:
        st.info("You are not part of any stokvel yet. Create one or wait for an invitation!")
    
    # Manage Invitations
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
                        stokvel.invite_member(member_id_input)
                        st.success(f"✅ Invited {member_id_input} to stokvel")
                    elif action == "Accept Invitation":
                        stokvel.accept_invitation(member_id_input)
                        st.success(f"✅ {member_id_input} accepted invitation")
                    else:
                        stokvel.reject_invitation(member_id_input)
                        st.warning(f"⚠️ {member_id_input} rejected invitation")
                    
                    st.rerun()
                except ValueError as e:
                    st.error(f"❌ {str(e)}")

## ============================================
# CREDIT SCORE TAB
# ============================================
with tab3:
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
with tab4:
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


# ============================================
# INDIVIDUAL SAVINGS TAB
# ============================================
with tab2:
    st.header("Individual Savings")
    
    # Create or Load Individual Savings
    try:
        individual_savings = manager.get_individual_savings(st.session_state.current_user)
    except ValueError:
        # Account doesn't exist, show creation form
        with st.expander("➕ Create Savings Account", expanded=True):
            savings_goal = st.number_input(
                "Set Savings Goal (Optional, R)", 
                min_value=0.0,
                value=5000.0
            )
            if st.button("Create Savings Account"):
                individual_savings = manager.create_individual_savings(
                    st.session_state.current_user,
                    savings_goal if savings_goal > 0 else None
                )
                st.success("✅ Savings account created!")
                st.rerun()
            st.stop()
    
    # Display Savings Summary
    summary = individual_savings.get_savings_summary(include_interest=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Saved", f"R{summary['total_saved']:,.2f}")
    with col2:
        if summary['total_with_interest']:
            st.metric("With Interest (5%)", f"R{summary['total_with_interest']:,.2f}")
    with col3:
        if summary['savings_goal']:
            st.metric("Goal", f"R{summary['savings_goal']:,.2f}")
    
    # Progress Bar
    if summary['progress_percentage'] is not None:
        st.progress(min(summary['progress_percentage'] / 100, 1.0))
        st.write(f"Progress: {summary['progress_percentage']:.1f}%")
    
    st.divider()
    
    # Add Contribution
    st.subheader("💵 Add Money to Savings")
    col1, col2 = st.columns([3, 1])
    with col1:
        contribution_amount = st.number_input(
            "Amount (R)", 
            min_value=0.0, 
            max_value=5000.0,
            value=100.0,
            key="individual_contrib"
        )
    with col2:
        st.write("")  # Spacing
        st.write("")  # Spacing
        if st.button("Add to Savings", type="primary"):
            try:
                individual_savings.add_contribution(contribution_amount)
                st.success(f"✅ Added R{contribution_amount:,.2f} to savings!")
                st.rerun()
            except ValueError as e:
                st.error(f"❌ {str(e)}")
    
    # Update Goal
    with st.expander("🎯 Update Savings Goal"):
        new_goal = st.number_input(
            "New Goal (R)", 
            min_value=0.0,
            value=summary['savings_goal'] if summary['savings_goal'] else 10000.0
        )
        if st.button("Update Goal"):
            try:
                individual_savings.set_savings_goal(new_goal)
                st.success(f"✅ Goal updated to R{new_goal:,.2f}")
                st.rerun()
            except ValueError as e:
                st.error(f"❌ {str(e)}")
    
    # Contribution History
    if individual_savings.contributions:
        st.subheader("📊 Contribution History")
        for i, contrib in enumerate(reversed(individual_savings.contributions)):
            st.write(f"**{contrib['date'].strftime('%Y-%m-%d %H:%M')}** - R{contrib['amount']:,.2f}")


# Debug Info (collapsible)
with st.sidebar.expander("🔧 Debug Info"):
    st.write("**All Stokvels:**", list(manager.stokvels.keys()))
    st.write("**All Savings Accounts:**", list(manager.individual_savings.keys()))

# -------------------------------------------------------
# Footer
# -------------------------------------------------------

st.markdown(
    """
    ---
    **Afriscore** © 2025  
    *Financial Freedom for all*
    """
)

