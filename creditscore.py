import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler

# -----------------------------
# 1️⃣ Train model (demo)
# -----------------------------
np.random.seed(42)
demo_data = pd.DataFrame({
    "savings": np.random.uniform(0, 20000, 200),
    "stockvel_contribution": np.random.uniform(0, 5000, 200),
    "monthly_payments": np.random.uniform(0, 15000, 200),
    "outstanding_loans": np.random.uniform(0, 5000, 200),
})
demo_data["credit_score"] = (
    300
    + 0.002 * demo_data["savings"]
    + 0.004 * demo_data["stockvel_contribution"]
    + 0.003 * demo_data["monthly_payments"]
    - 0.004 * demo_data["outstanding_loans"]
    + np.random.normal(0, 25, 200)
).clip(300, 850)

X = demo_data.drop(columns=["credit_score"])
y = demo_data["credit_score"]

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

model = RandomForestRegressor(n_estimators=200, random_state=42)
model.fit(X_scaled, y)

# -----------------------------
# 2️⃣ Prediction function
# -----------------------------
def predict_credit_score(user_features: dict) -> float:
    """
    user_features: dict with keys
        'savings', 'stockvel_contribution', 'monthly_payments', 'outstanding_loans'
    Returns predicted credit score (300-850)
    """
    df_input = pd.DataFrame([user_features])
    X_scaled_input = scaler.transform(df_input.values)
    pred = model.predict(X_scaled_input)[0]
    return float(np.clip(pred, 300, 850))




