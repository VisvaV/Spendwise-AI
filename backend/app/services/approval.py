from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import List

from app.models.schema import ApprovalMatrix, Approval, Expense, User

def generate_approval_chain(db: Session, expense: Expense, user: User):
    matrices = db.query(ApprovalMatrix).filter(
        (ApprovalMatrix.department_id == user.department_id) | (ApprovalMatrix.department_id == None),
        (ApprovalMatrix.category == expense.category) | (ApprovalMatrix.category == None),
        ApprovalMatrix.amount_min <= expense.amount,
        (ApprovalMatrix.amount_max >= expense.amount) | (ApprovalMatrix.amount_max == None)
    ).all()
    
    if not matrices:
        required_roles = ["Manager"]
    else:
        # Simple policy: use the first matched policy (in reality, prioritize most specific)
        required_roles = matrices[0].required_roles

    # Rule: If submitter IS the manager -> skip Manager, escalate to Finance
    if user.role.lower() == "manager" and "Manager" in required_roles:
        required_roles.remove("Manager")
        if "Finance" not in required_roles:
            required_roles.insert(0, "Finance")
    
    # Generate the chain
    base_deadline = datetime.utcnow()
    for role in required_roles:
        base_deadline += timedelta(hours=48)
        approval = Approval(
            expense_id=expense.id,
            role_required=role,
            deadline_at=base_deadline
        )
        db.add(approval)
    db.commit()

def process_approval_action(db: Session, expense_id: int, action: str, approver: User, note: str):
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    # For simplicity, we just look up pending approvals matching the user's role
    approval = db.query(Approval).filter(
        Approval.expense_id == expense.id,
        Approval.action == None,
        Approval.role_required == approver.role
    ).first()

    if not approval:
        raise HTTPException(status_code=403, detail="Not authorized to approve at this stage or already acted")

    approval.action = action
    approval.approver_id = approver.id
    approval.note = note
    approval.acted_at = datetime.utcnow()

    from app.services.budget import consume_budget, release_budget
    from app.models.schema import AuditLog

    prev_state = expense.status

    if action == "REJECTED":
        expense.status = "REJECTED"
        release_budget(db, approver.department_id, expense.amount)
    elif action == "PENDING_INFO":
        expense.status = "PENDING_INFO"
    elif action == "APPROVED":
        # Check if more approvals needed
        pending = db.query(Approval).filter(Approval.expense_id == expense.id, Approval.action == None).count()
        if pending == 0:
            expense.status = "APPROVED"
            consume_budget(db, approver.department_id, expense.amount)
        else:
            expense.status = "UNDER_REVIEW"

    # Audit log
    db.add(AuditLog(
        expense_id=expense.id, actor_id=approver.id,
        from_state=prev_state, to_state=expense.status, note=note
    ))

    db.commit()
    return expense
