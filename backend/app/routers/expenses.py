from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.db.postgres import get_db
from app.models.schema import Expense, User, AuditLog
from app.schemas.expense import ExpenseCreate, ExpenseResponse
from app.api.deps import get_current_active_user
from app.services.policy import validate_expense_policy
from app.services.budget import reserve_budget
from app.services.ai_client import run_full_analysis
from app.services.approval import generate_approval_chain

router = APIRouter()

@router.post("/", response_model=ExpenseResponse)
def submit_expense(expense_in: ExpenseCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    policy_res = validate_expense_policy(db, expense_in.dict(), current_user)
    duplicate_flag = policy_res["duplicate_flag"]
    
    recent_category_count = db.query(Expense).filter(
        Expense.employee_id == current_user.id,
        Expense.category == expense_in.category,
        Expense.submitted_at >= datetime.utcnow() - timedelta(hours=24)
    ).count()
    
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_amount_count = db.query(Expense).filter(
        Expense.employee_id == current_user.id,
        Expense.amount.between(expense_in.amount * 0.97, expense_in.amount * 1.03),
        Expense.submitted_at >= seven_days_ago
    ).count()
    
    ai_res = run_full_analysis(
        receipt_url=expense_in.receipt_s3_url,
        claimed_amount=expense_in.amount,
        title=expense_in.title,
        description=expense_in.description or "",
        employee_id=current_user.id,
        category=expense_in.category,
        date=expense_in.expense_date.isoformat(),
        department_id=current_user.department_id,
        role=current_user.role,
        recent_same_category_count=recent_category_count,
        recent_same_amount_count=recent_amount_count
    )
    
    fraud_data = ai_res.get("fraud", {})
    ocr_data = ai_res.get("ocr", {}) or {}
    cat_data = ai_res.get("categorization", {})
    
    risk_score = fraud_data.get("risk_score", 0.0)
    risk_flags = fraud_data.get("risk_flags", [])
    
    receipt_phash = ocr_data.get("receipt_phash")
    if receipt_phash and receipt_phash != "UNKNOWN":
        phash_duplicate = db.query(Expense).filter(Expense.receipt_hash == receipt_phash).first()
        if phash_duplicate:
            duplicate_flag = True
            risk_flags.append("DUPLICATE_RECEIPT")
            
    final_category = expense_in.category
    if not final_category and cat_data.get("predicted_category"):
        final_category = cat_data["predicted_category"]
        
    ai_confidence = cat_data.get("confidence_score")
    
    new_expense = Expense(
        employee_id=current_user.id,
        title=expense_in.title,
        description=expense_in.description,
        amount=expense_in.amount,
        currency=expense_in.currency,
        category=final_category,
        expense_date=expense_in.expense_date,
        receipt_s3_url=expense_in.receipt_s3_url,
        receipt_hash=receipt_phash if receipt_phash != "UNKNOWN" else None,
        business_justification=expense_in.business_justification,
        duplicate_flag=duplicate_flag,
        risk_score=risk_score,
        risk_flags=risk_flags,
        ai_category=cat_data.get("predicted_category"),
        ai_confidence=ai_confidence,
        status="SUBMITTED",
        submitted_at=datetime.utcnow()
    )
    
    try:
        db.add(new_expense)
        db.commit()
        db.refresh(new_expense)
        
        reserve_budget(db, current_user.department_id, expense_in.amount)
        generate_approval_chain(db, new_expense, current_user)
        
        log = AuditLog(
            expense_id=new_expense.id,
            actor_id=current_user.id,
            from_state="DRAFT",
            to_state="SUBMITTED",
            note=f"Submitted with AI score {risk_score}"
        )
        db.add(log)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database transaction failed during submission.")
        
    return new_expense

@router.get("/", response_model=List[ExpenseResponse])
def my_expenses(skip: int = Query(0, ge=0), limit: int = Query(50, le=100), db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    if current_user.role.lower() == "admin":
        return db.query(Expense).order_by(Expense.submitted_at.desc()).offset(skip).limit(limit).all()
    return db.query(Expense).filter(Expense.employee_id == current_user.id).order_by(Expense.submitted_at.desc()).offset(skip).limit(limit).all()

@router.get("/{expense_id}", response_model=ExpenseResponse)
def get_expense(expense_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    from sqlalchemy.orm import joinedload
    expense = db.query(Expense).options(joinedload(Expense.approvals)).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
        
    if expense.employee_id != current_user.id and current_user.role not in ["Manager", "Finance", "Admin", "Senior Approver"]:
        raise HTTPException(status_code=403, detail="Not authorized to view this expense")
        
    return expense
