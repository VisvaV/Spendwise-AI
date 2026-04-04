from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.postgres import get_db
from app.models.schema import Budget, User
from app.schemas.budget import BudgetCreate, BudgetResponse
from app.api.deps import get_current_active_user, RoleChecker

router = APIRouter()
admin_role_checker = RoleChecker(["Admin", "Finance"])

@router.post("/", response_model=BudgetResponse, dependencies=[Depends(admin_role_checker)])
def allocate_budget(budget_in: BudgetCreate, db: Session = Depends(get_db)):
    # Check if budget already exists for dept + quarter + year
    existing = db.query(Budget).filter(
        Budget.department_id == budget_in.department_id,
        Budget.fiscal_quarter == budget_in.fiscal_quarter,
        Budget.fiscal_year == budget_in.fiscal_year
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Budget already exists for this quarter")
    
    b = Budget(
        department_id=budget_in.department_id,
        fiscal_quarter=budget_in.fiscal_quarter,
        fiscal_year=budget_in.fiscal_year,
        total_amount=budget_in.total_amount,
        alert_threshold=budget_in.alert_threshold
    )
    db.add(b)
    db.commit()
    db.refresh(b)
    return b

@router.get("/", response_model=List[BudgetResponse], dependencies=[Depends(admin_role_checker)])
def list_budgets(db: Session = Depends(get_db)):
    return db.query(Budget).all()
