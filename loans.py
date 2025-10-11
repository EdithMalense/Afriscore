from datetime import datetime, timedelta

class Loan:
    def __init__(self, amount, date, due_date):
        self.amount = amount
        self.date = date
        self.due_date = due_date
        self.repaid = False
        self.repaid_on_time = None  # True/False

class LoanManager:
    def __init__(self):
        # user_id -> list of Loan objects
        self.loans = {}

        # user_id -> base loan limit (starts at 200)
        self.loan_limits = {}

    # -----------------------------
    # 1️⃣ Maximum loan based on credit score
    # -----------------------------
    def get_max_loan_amount(self, credit_score, user_id=None):
        """Determine max loan based on credit score"""
        if credit_score < 600:
            base = 200
        elif credit_score < 650:
            base = 1000
        elif credit_score < 700:
            base = 2500
        elif credit_score < 750:
            base = 4000
        else:
            base = 5000

        # Ensure user cannot exceed personalized limit
        if user_id:
            personalized_limit = self.loan_limits.get(user_id, 200)
            return min(base, personalized_limit)
        return base

    # -----------------------------
    # 2️⃣ Create a new loan
    # -----------------------------
    def create_loan(self, user_id, credit_score, requested_amount):
        max_loan = self.get_max_loan_amount(credit_score, user_id)
        if requested_amount > max_loan:
            raise ValueError(f"Maximum loan allowed: R{max_loan}")

        loan = Loan(
            amount=requested_amount,
            date=datetime.now(),
            due_date=datetime.now() + timedelta(days=30)  # 30-day repayment
        )

        self.loans.setdefault(user_id, []).append(loan)
        return loan

    # -----------------------------
    # 3️⃣ Repay a loan
    # -----------------------------
    def repay_loan(self, user_id, loan_index, on_time=True):
        """User repays loan"""
        loans = self.loans.get(user_id, [])
        if loan_index >= len(loans):
            raise IndexError("Invalid loan index")
        loan = loans[loan_index]
        loan.repaid = True
        loan.repaid_on_time = on_time

        # Adjust loan limit based on repayment
        current_limit = self.loan_limits.get(user_id, 200)
        if on_time:
            # Gradually increase limit by 10% of current limit
            self.loan_limits[user_id] = min(current_limit * 1.1, 5000)
        else:
            # Penalize by decreasing limit 10%
            self.loan_limits[user_id] = max(current_limit * 0.9, 200)

    # -----------------------------
    # 4️⃣ Adjust credit score based on loans
    # -----------------------------
    def adjust_credit_score(self, base_score, user_id):
        """Increase/decrease credit score based on repayment behavior"""
        loans = self.loans.get(user_id, [])
        adjusted_score = base_score
        for loan in loans:
            if loan.repaid:
                if loan.repaid_on_time:
                    adjusted_score += 5  # timely repayment boost
                else:
                    adjusted_score -= 10  # late repayment penalty
            else:
                # Optionally, penalize overdue loans
                if datetime.now() > loan.due_date:
                    adjusted_score -= 5
        return max(300, min(adjusted_score, 850))

    # -----------------------------
    # 5️⃣ Helper: Get user loans
    # -----------------------------
    def get_user_loans(self, user_id):
        return self.loans.get(user_id, [])
