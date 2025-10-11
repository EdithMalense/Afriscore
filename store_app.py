import streamlit as st
import requests

API_URL = "http://localhost:8000"  # FastAPI backend URL

st.set_page_config(page_title="Afriscore Store App", page_icon="🏪", layout="centered")
st.title("🏪 Afriscore Store Portal")
st.caption("For store clerks to verify loan withdrawals and record repayments.")

# --- Tabs for different actions ---
tab1, tab2 = st.tabs(["✅ Verify OTP", "💵 Record Payment"])

# =============== TAB 1: OTP Verification ===============
with tab1:
    st.subheader("🔐 Verify Customer OTP")
    otp = st.text_input("Enter Customer OTP", max_chars=6)
    if st.button("Verify Loan OTP"):
        if not otp.strip():
            st.warning("Please enter the OTP.")
        else:
            try:
                resp = requests.post(f"{API_URL}/verify_otp", json={"otp": otp})
                if resp.ok:
                    data = resp.json()
                    st.success(data["message"])
                else:
                    st.error(resp.json().get("detail", "OTP verification failed."))
            except requests.exceptions.ConnectionError:
                st.error("Unable to connect to the server. Ensure the backend is running.")

# =============== TAB 2: Record Payment ===============
with tab2:
    st.subheader("💰 Record a Customer Payment")
    otp = st.text_input("Customer OTP", key="pay_otp", max_chars=6)
    amount = st.number_input("Amount Paid (R)", min_value=1.0, step=1.0)

    if st.button("Record Payment"):
        if not otp.strip():
            st.warning("Please enter the OTP.")
        else:
            try:
                resp = requests.post(f"{API_URL}/record_payment", json={"otp": otp, "amount": amount})
                if resp.ok:
                    data = resp.json()
                    st.success("✅ Payment recorded successfully.")
                    loan_status = data["loan_status"]
                    st.write(f"**Total Loan Amount:** R{loan_status['amount']}")
                    st.write(f"**Payments Made:** {len(loan_status['payments'])}/{loan_status['months']}")
                    st.write(f"**Loan Status:** {'✅ Fully Repaid' if loan_status['repaid'] else '⏳ Ongoing'}")
                else:
                    st.error(resp.json().get("detail", "Payment failed."))
            except requests.exceptions.ConnectionError:
                st.error("Unable to connect to the server. Ensure the backend is running.")
