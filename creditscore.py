import streamlit as st
import pandas as pd
import numpy as np
import joblib
import os
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt

# -------------------------------------------------------
# 💳 AFRISCORE: Credit Scoring for the Unbanked
# -------------------------------------------------------

st.set_page_config(page_title="Afriscore - Credit Scoring for the Unbanked", page_icon="💳", layout="centered")

st.title("💳 Afriscore: AI Credit Scoring for the Unbanked")
st.markdown(
    """
    *Empowering financial inclusion across Africa with alternative data.*

    This AI model predicts a **credit score** based on non-traditional data such as:
    - Mobile money transactions  
    - Airtime purchases  
    - Savings consistency  
    - Utility payment behavior  
    - Stokvel participation
    """
)

# -------------------------------------------------------
# 🧠 Load or Train Model
# -------------------------------------------------------

@st.cache_resource
def load_or_train_model():
    if os.path.exists("credit_model.joblib") and os.path.exists("scaler.joblib"):
        model = joblib.load("credit_model.joblib")
        scaler = joblib.load("scaler.joblib")
        return model, scaler

    # --- Simulate realistic training data ---
    np.random.seed(42)
    n = 300
    data = {
        "mobile_txn_freq": np.random.randint(5, 80, n),
        "avg_txn_value": np.random.randint(50, 1000, n),
        "airtime_purchases": np.random.randint(2, 20, n),
        "savings_consistency": np.random.rand(n),
        "utility_payment_score": np.random.rand(n),  # 0–1 reliability score
        "stokvel_participation": np.random.choice([0, 1], n, p=[0.4, 0.6])
    }
    df = pd.DataFrame(data)

    # Credit category logic (based on realistic behaviors)
    conditions = [
        (df["mobile_txn_freq"] < 20) & (df["savings_consistency"] < 0.4) & (df["utility_payment_score"] < 0.5),
        (df["mobile_txn_freq"].between(20, 50)) & (df["savings_consistency"].between(0.4, 0.7)),
        (df["mobile_txn_freq"] > 50) & (df["savings_consistency"] > 0.7) & (df["utility_payment_score"] > 0.7)
    ]
    choices = ["low", "medium", "high"]
    df["credit_category"] = np.select(conditions, choices, default="medium")

    X = df.drop("credit_category", axis=1)
    y = df["credit_category"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train_scaled, y_train)

    joblib.dump(model, "credit_model.joblib")
    joblib.dump(scaler, "scaler.joblib")

    return model, scaler


model, scaler = load_or_train_model()

# -------------------------------------------------------
# 🧾 Input Section
# -------------------------------------------------------

st.subheader("📋 Enter Financial Behavior Details")

col1, col2 = st.columns(2)

with col1:
    mobile_txn_freq = st.slider("Mobile Transactions per Month", 0, 100, 20)
    avg_txn_value = st.slider("Average Transaction Value (R)", 50, 2000, 300)
    airtime_purchases = st.slider("Airtime Purchases per Month", 0, 30, 5)

with col2:
    savings_consistency = st.slider("Savings Consistency (0–1)", 0.0, 1.0, 0.5)
    utility_payment_score = st.slider("Utility Payment Score (0–1)", 0.0, 1.0, 0.5)
    stokvel_participation = st.selectbox("Stokvel Participation", [0, 1], format_func=lambda x: "Yes" if x else "No")

# -------------------------------------------------------
# 🔮 Prediction
# -------------------------------------------------------

if st.button("Predict Credit Score"):
    X_input = np.array([[mobile_txn_freq, avg_txn_value, airtime_purchases,
                         savings_consistency, utility_payment_score, stokvel_participation]])
    X_scaled = scaler.transform(X_input)
    pred = model.predict(X_scaled)[0]

    # Score ranges (for realism)
    score_map = {
        "low": np.random.randint(300, 579),
        "medium": np.random.randint(580, 699),
        "high": np.random.randint(700, 850)
    }

    st.success(f"### 🧭 Credit Category: **{pred.upper()}**")
    st.metric("Predicted Credit Score", score_map[pred])

    st.write("---")

    # -------------------------------------------------------
    # 📊 Feature Importance Visualization
    # -------------------------------------------------------
    st.subheader("📈 Feature Importance in Decision")
    importances = model.feature_importances_
    features = ["Txn Freq", "Txn Value", "Airtime", "Savings", "Utility Pay", "Stokvel"]

    fig, ax = plt.subplots(figsize=(6, 3))
    ax.barh(features, importances, color="skyblue")
    ax.set_xlabel("Importance")
    ax.set_title("Which features matter most?")
    st.pyplot(fig)

    st.info(
        "💡 Regular utility payments and consistent savings greatly improve credit reliability."
    )

# -------------------------------------------------------
# 🪙 Footer
# -------------------------------------------------------

st.markdown(
    """
    ---
    **Afriscore** © 2025  
    *Financial Freedom for all*
    """
)
