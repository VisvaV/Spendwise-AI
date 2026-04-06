from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.postgres import get_db
from app.models.schema import Expense
from app.api.deps import RoleChecker

router = APIRouter()
finance_role_checker = RoleChecker(["Finance", "Admin", "finance", "admin"])

@router.get("/metrics", dependencies=[Depends(finance_role_checker)])
def get_finance_metrics(db: Session = Depends(get_db)):
    total_pipeline = db.query(func.sum(Expense.amount)).scalar() or 0.0
    
    flagged_count = db.query(Expense).filter(Expense.risk_score > 0.5).count()
    policy_breaches = db.query(Expense).filter(Expense.duplicate_flag == True).count()
    
    low_risk = db.query(Expense).filter(Expense.risk_score <= 0.3).count()
    med_risk = db.query(Expense).filter(Expense.risk_score > 0.3, Expense.risk_score <= 0.7).count()
    high_risk = db.query(Expense).filter(Expense.risk_score > 0.7).count()
    
    risk_data = [
        {"name": "Low Risk", "value": low_risk, "color": "#22c55e"},
        {"name": "Medium Risk", "value": med_risk, "color": "#eab308"},
        {"name": "High Risk", "value": high_risk, "color": "#ef4444"}
    ]
    
    category_group = db.query(Expense.category, func.sum(Expense.amount)).group_by(Expense.category).all()
    
    cat_spend_obj = {"name": "YTD"}
    for cat, amt in category_group:
        if cat:
            cat_spend_obj[cat] = amt
            
    category_spend = [cat_spend_obj]
    
    return {
        "total_pipeline": total_pipeline,
        "flagged_count": flagged_count,
        "policy_breaches": policy_breaches,
        "risk_data": risk_data,
        "category_spend": category_spend
    }
