from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.schema import Expense, User

def validate_expense_policy(db: Session, expense_in: dict, user: User, merchant: str = "UNKNOWN"):
    warnings = []
    
    amount = expense_in.get("amount", 0.0)
    receipt_url = expense_in.get("receipt_s3_url")
    expense_date: datetime = expense_in.get("expense_date")
    category = expense_in.get("category", "")
    justification = expense_in.get("business_justification")
    team_members = expense_in.get("team_members", 1)

    if amount > 500 and not receipt_url:
        raise HTTPException(status_code=400, detail="Receipt is required for expenses over ₹500")

    if expense_date and (datetime.utcnow() - expense_date.replace(tzinfo=None)).days > 30:
        raise HTTPException(status_code=400, detail="Expense date cannot be older than 30 days")

    start_of_day = expense_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)
    daily_expenses = db.query(Expense).filter(
        Expense.employee_id == user.id,
        Expense.category == category,
        Expense.submitted_at >= start_of_day,
        Expense.submitted_at < end_of_day,
        Expense.status != "REJECTED"
    ).all()
    
    daily_total = sum(e.amount for e in daily_expenses) + amount
    meals_cap = 800 * team_members
    travel_cap = 5000 * team_members
    accom_cap = 8000 * team_members
    
    cat_lower = category.lower()
    if cat_lower == "meals":
        if daily_total > meals_cap:
            raise HTTPException(status_code=400, detail=f"Daily meals cap of ₹{meals_cap} exceeded (Total: {daily_total})")
        if daily_total > meals_cap * 0.8:
            warnings.append("Amount is close to daily cap.")
    elif cat_lower == "travel":
        if daily_total > travel_cap:
            raise HTTPException(status_code=400, detail=f"Daily travel cap of ₹{travel_cap} exceeded (Total: {daily_total})")
        if daily_total > travel_cap * 0.8:
            warnings.append("Amount is close to daily cap.")
    elif cat_lower == "accommodation":
        if daily_total > accom_cap:
            raise HTTPException(status_code=400, detail=f"Daily accommodation cap of ₹{accom_cap} exceeded")
    elif cat_lower in ["software", "equipment"]:
        quarter_start = datetime.utcnow() - timedelta(days=90)
        quarter_expenses = db.query(Expense).filter(
            Expense.employee_id == user.id,
            Expense.category == category,
            Expense.submitted_at >= quarter_start,
            Expense.status != "REJECTED"
        ).all()
        q_total = sum(e.amount for e in quarter_expenses) + amount
        if q_total > 50000:
            raise HTTPException(status_code=400, detail=f"Quarterly {cat_lower} cap of ₹50000 exceeded")

    duplicate_flag = False
    
    reference_date = datetime.utcnow()
    seven_days_ago = reference_date - timedelta(days=7)
    
    potential_duplicates = db.query(Expense).filter(
        Expense.employee_id == user.id,
        Expense.amount.between(amount * 0.97, amount * 1.03),
        Expense.submitted_at >= seven_days_ago,
        Expense.submitted_at <= reference_date
    ).all()
    
    if merchant and merchant not in ["UNKNOWN", "General Merchant"]:
        # If we had a merchant column we would filter by it here.
        pass

    if potential_duplicates:
        duplicate_flag = True

    if expense_date.weekday() >= 5: 
        if not justification:
            raise HTTPException(status_code=400, detail="Business justification required for weekend expenses")
        else:
            warnings.append("Expense on weekend — ensure justification is detailed")

    return {"duplicate_flag": duplicate_flag, "policy_warnings": warnings}
