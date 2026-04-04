from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.schema import Expense, User

def validate_expense_policy(db: Session, expense_in: dict, user: User):
    amount = expense_in.get("amount", 0.0)
    receipt_url = expense_in.get("receipt_s3_url")
    expense_date: datetime = expense_in.get("expense_date")
    category = expense_in.get("category", "")
    justification = expense_in.get("business_justification")

    # 1. Receipt required if amount > 500
    if amount > 500 and not receipt_url:
        raise HTTPException(status_code=400, detail="Receipt is required for expenses over ₹500")

    # 2. Expense date cannot be older than 30 days
    if expense_date and (datetime.utcnow() - expense_date.replace(tzinfo=None)).days > 30:
        raise HTTPException(status_code=400, detail="Expense date cannot be older than 30 days")

    # 3. Category-specific daily caps (meals 800/day, travel 5000/day)
    # Get all expenses for this user on that day for that category
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
    if category.lower() == "meals" and daily_total > 800:
        raise HTTPException(status_code=400, detail=f"Daily meals cap of ₹800 exceeded (Total: {daily_total})")
    if category.lower() == "travel" and daily_total > 5000:
        raise HTTPException(status_code=400, detail=f"Daily travel cap of ₹5000 exceeded (Total: {daily_total})")

    duplicate_flag = False
    # 4. Duplicate detection
    seven_days_ago = expense_date - timedelta(days=7)
    potential_duplicates = db.query(Expense).filter(
        Expense.employee_id == user.id,
        Expense.amount == amount,
        Expense.submitted_at >= seven_days_ago,
        Expense.submitted_at <= expense_date
    ).all()
    if potential_duplicates:
        duplicate_flag = True

    # 6. Working day check
    if expense_date.weekday() == 6: # Sunday
        if not justification:
            raise HTTPException(status_code=400, detail="Business justification required for Sunday expenses")

    return duplicate_flag
