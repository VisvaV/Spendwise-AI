from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.postgres import get_db
from app.models.schema import User, AuditLog, Budget, PolicyRule
from app.api.deps import RoleChecker

router = APIRouter()
admin_role_checker = RoleChecker(["Admin"])  # RoleChecker is now case-insensitive

@router.get("/metrics", dependencies=[Depends(admin_role_checker)])
def get_admin_metrics(db: Session = Depends(get_db)):
    users_count = db.query(User).count()
    policies_count = db.query(PolicyRule).count()
    budgets_count = db.query(Budget).count()
    logs_count = db.query(AuditLog).count()

    return {
        "users_count": users_count,
        "policies_count": policies_count,
        "budgets_count": budgets_count,
        "logs_count": logs_count
    }