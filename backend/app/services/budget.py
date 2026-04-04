from fastapi import HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from app.models.schema import Budget, Expense

def reserve_budget(db: Session, department_id: int, amount: float):
    if not department_id:
        return

    # Use with_for_update for row level locking
    budget = db.query(Budget).filter(Budget.department_id == department_id).with_for_update().first()
    if not budget:
        budget = Budget(
            department_id=department_id,
            fiscal_quarter=(datetime.utcnow().month - 1) // 3 + 1,
            fiscal_year=datetime.utcnow().year,
            total_amount=100000.0,
            reserved_amount=0.0,
            consumed_amount=0.0
        )
        db.add(budget)
        db.commit()
        db.refresh(budget)

    available = budget.total_amount - (budget.reserved_amount + budget.consumed_amount)
    if amount > available:
        raise HTTPException(status_code=400, detail="Insufficient budget. Submission blocked.")

    budget.reserved_amount += amount
    db.commit()

def consume_budget(db: Session, department_id: int, amount: float):
    budget = db.query(Budget).filter(Budget.department_id == department_id).with_for_update().first()
    if not budget:
        return
    
    # move from reserved to consumed
    budget.reserved_amount = max(0, budget.reserved_amount - amount)
    budget.consumed_amount += amount
    db.commit()

def release_budget(db: Session, department_id: int, amount: float):
    budget = db.query(Budget).filter(Budget.department_id == department_id).with_for_update().first()
    if not budget:
        return
    
    budget.reserved_amount = max(0, budget.reserved_amount - amount)
    db.commit()
