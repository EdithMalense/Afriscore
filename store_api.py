from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import loans

app = FastAPI(title="Store Loan API")

class OTPVerifyRequest(BaseModel):
    otp: str

class PaymentRequest(BaseModel):
    otp: str
    amount: float

@app.post("/verify_otp")
def verify_otp(req: OTPVerifyRequest):
    success = loans.grant_loan(req.otp)
    if not success:
        raise HTTPException(status_code=400, detail="Invalid or already used OTP.")
    return {"message": "OTP verified successfully. Loan granted."}

@app.post("/record_payment")
def record_payment(req: PaymentRequest):
    loan = loans.record_payment(req.otp, req.amount)
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found.")
    return {"message": "Payment recorded.", "loan_status": loan}
