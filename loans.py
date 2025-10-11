import os
import json, uuid, datetime

loan_limits = {}

DATA_FILE = "data/loans.json"

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"users": {}, "loans": []}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)

def create_loan(user, amount, months):
    data = load_data()

    # 🔒 Check for existing active loans
    active_loans = [
        loan for loan in data["loans"]
        if loan["user"] == user and not loan["repaid"]
    ]
    if active_loans:
        raise ValueError("You already have an active loan. Please repay it before applying for a new one.")

    otp = str(uuid.uuid4())[:6]
    due_dates = []
    installment = round(amount / months, 2)
    start_date = datetime.date.today()
    for i in range(months):
        due_dates.append((start_date + datetime.timedelta(days=30 * (i+1))).isoformat())

    loan = {
        "id": str(uuid.uuid4()),
        "user": user,
        "amount": amount,
        "installment": installment,
        "months": months,
        "due_dates": due_dates,
        "payments": [],
        "otp": otp,
        "granted": False,
        "repaid": False,
    }

    data["loans"].append(loan)
    save_data(data)
    return otp

def grant_loan(otp):
    data = load_data()
    for loan in data["loans"]:
        if loan["otp"] == otp and not loan["granted"]:
            loan["granted"] = True
            save_data(data)
            return True
    return False

def record_payment(otp, amount):
    data = load_data()
    for loan in data["loans"]:
        if loan["otp"] == otp:
            loan["payments"].append({"amount": amount, "date": datetime.date.today().isoformat()})
            if sum(p["amount"] for p in loan["payments"]) >= loan["amount"]:
                loan["repaid"] = True
            save_data(data)
            return loan
    return None

def adjust_credit_score(base_score, user_id):
    from loans import get_user_loans
    loans = get_user_loans(user_id)
    adjusted_score = base_score

    for loan in loans:
        payments = loan.get("payments", [])
        for idx, payment in enumerate(payments):
            due_date_str = loan.get("due_dates", [])[idx] if idx < len(loan.get("due_dates", [])) else None
            if due_date_str:
                due_date = datetime.fromisoformat(due_date_str)
                paid_on_time = datetime.fromisoformat(payment["date"]) <= due_date
            else:
                paid_on_time = True

            if paid_on_time:
                adjusted_score += 2
            else:
                adjusted_score -= 3

        # Bonus for full loan repayment on time
        if loan.get("repaid", False):
            all_paid_on_time = True
            for idx, payment in enumerate(payments):
                due_date_str = loan.get("due_dates", [])[idx] if idx < len(loan.get("due_dates", [])) else None
                if due_date_str and datetime.fromisoformat(payment["date"]) > datetime.fromisoformat(due_date_str):
                    all_paid_on_time = False
            if all_paid_on_time:
                adjusted_score += 5

    # Update personalized limit
    current_limit = loan_limits.get(user_id, 200)
    on_time_payments = sum(
        1 for loan in loans for idx, payment in enumerate(loan.get("payments", []))
        if idx < len(loan.get("due_dates", [])) and datetime.fromisoformat(payment["date"]) <= datetime.fromisoformat(loan["due_dates"][idx])
    )
    late_payments = sum(
        1 for loan in loans for idx, payment in enumerate(loan.get("payments", []))
        if idx < len(loan.get("due_dates", [])) and datetime.fromisoformat(payment["date"]) > datetime.fromisoformat(loan["due_dates"][idx])
    )

    if on_time_payments > late_payments:
        loan_limits[user_id] = min(current_limit * 1.1, 5000)
    else:
        loan_limits[user_id] = max(current_limit * 0.9, 200)

    return max(300, min(adjusted_score, 850))

def extract_loan_features(user):
    loans = get_user_loans(user)
    
    total_loans = len(loans)
    fully_repaid = sum(1 for loan in loans if loan.get("repaid", False))
    late_payments = 0
    on_time_payments = 0
    total_borrowed = sum(loan["amount"] for loan in loans)
    
    for loan in loans:
        payments = loan.get("payments", [])
        due_dates = loan.get("due_dates", [])
        for idx, payment in enumerate(payments):
            if idx < len(due_dates):
                due_date = datetime.fromisoformat(due_dates[idx])
                paid_on_time = datetime.fromisoformat(payment["date"]) <= due_date
                if paid_on_time:
                    on_time_payments += 1
                else:
                    late_payments += 1
    
    features = {
        "total_loans": total_loans,
        "fully_repaid": fully_repaid,
        "late_payments": late_payments,
        "on_time_payments": on_time_payments,
        "total_borrowed": total_borrowed,
    }
    
    return features


def get_user_loans(user):
    data = load_data()
    return [loan for loan in data["loans"] if loan["user"] == user]

def save_data(data):
    # Ensure the folder exists
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)

