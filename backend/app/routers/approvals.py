from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.postgres import get_db
from app.models.schema import User
from app.schemas.approval import ApprovalAction
from app.api.deps import get_current_active_user
from app.services.approval import process_approval_action

router = APIRouter()


@router.post("/{expense_id}/action")
def act_on_expense(
    expense_id: int,
    action_in: ApprovalAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    res = process_approval_action(db, expense_id, action_in.action, current_user, action_in.note)
    return {"message": "Success", "new_status": res.status}


@router.get("/pending")
def get_pending_approvals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    from app.models.schema import Approval, Expense, User as EmployeeUser

    query = (
        db.query(Approval, Expense, EmployeeUser)
        .join(Expense, Approval.expense_id == Expense.id)
        .join(EmployeeUser, Expense.employee_id == EmployeeUser.id)
        .filter(Approval.action == None)
    )

    # Admin sees all pending approvals; others only see approvals matching their role
    if current_user.role.lower() != "admin":
        query = query.filter(
            func.lower(Approval.role_required) == current_user.role.lower()
        )

    approvals = query.all()

    results = []
    for approval, expense, employee in approvals:
        results.append({
            "approval_id": approval.id,
            "expense_id": expense.id,
            "expense_title": expense.title,
            "expense_amount": expense.amount,
            "expense_category": expense.category,
            "expense_date": str(expense.submitted_at) if expense.submitted_at else "UNKNOWN",
            "employee_name": employee.name,
            "risk_score": expense.risk_score or 0.0,
            "risk_flags": expense.risk_flags if expense.risk_flags else [],
            "ai_category": expense.ai_category,
            "ai_confidence": expense.ai_confidence,
            "duplicate_flag": expense.duplicate_flag or False,
            "receipt_s3_url": expense.receipt_s3_url,
            "role_required": approval.role_required,
            "deadline_at": str(approval.deadline_at) if approval.deadline_at else None
        })
    return results