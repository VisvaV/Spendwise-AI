from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.db.postgres import get_db
from app.models.schema import Expense, User, AuditLog
from app.schemas.expense import ExpenseCreate, ExpenseResponse
from app.api.deps import get_current_active_user
from app.services.policy import validate_expense_policy
from app.services.budget import reserve_budget
from app.services.ai_client import get_fraud_score, get_categorization, run_ocr_validation
from app.services.approval import generate_approval_chain

router = APIRouter()

@router.post("/", response_model=ExpenseResponse)
def submit_expense(expense_in: ExpenseCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    # Run policy engine
    duplicate_flag = validate_expense_policy(db, expense_in.dict(), current_user)
    
    # AI Validations (Step 21 integration)
    mock_merchant = "General Merchant"
    fraud_data = get_fraud_score(current_user.id, expense_in.amount, expense_in.category, mock_merchant, expense_in.expense_date.isoformat())
    
    ai_cat = get_categorization(expense_in.title, expense_in.description)
    category = expense_in.category
    if not category and ai_cat.get("predicted_category"):
        category = ai_cat["predicted_category"]
        
    risk_score = fraud_data.get("risk_score", 0.0)
    ai_confidence = ai_cat.get("confidence_score")
    
    # Soft lock budget
    reserve_budget(db, current_user.department_id, expense_in.amount)
    
    new_expense = Expense(
        employee_id=current_user.id,
        title=expense_in.title,
        description=expense_in.description,
        amount=expense_in.amount,
        currency=expense_in.currency,
        category=category,
        receipt_s3_url=expense_in.receipt_s3_url,
        business_justification=expense_in.business_justification,
        duplicate_flag=duplicate_flag,
        risk_score=risk_score,
        ai_category=ai_cat.get("predicted_category"),
        ai_confidence=ai_confidence,
        status="SUBMITTED",
        submitted_at=datetime.utcnow()
    )
    
    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)
    
    # Generate Approvals Chain
    generate_approval_chain(db, new_expense, current_user)

    # Audit log
    log = AuditLog(
        expense_id=new_expense.id,
        actor_id=current_user.id,
        from_state="DRAFT",
        to_state="SUBMITTED",
        note="Expense originally submitted"
    )
    db.add(log)
    db.commit()
    
    return new_expense

@router.get("/", response_model=List[ExpenseResponse])
def my_expenses(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    return db.query(Expense).filter(Expense.employee_id == current_user.id).all()
