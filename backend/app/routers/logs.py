from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Any
from app.db.postgres import get_db
from app.models.schema import AuditLog, User
from app.api.deps import RoleChecker

router = APIRouter()
admin_role_checker = RoleChecker(["Admin"])

@router.get("/", dependencies=[Depends(admin_role_checker)])
def get_audit_logs(db: Session = Depends(get_db)):
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).all()
    # Pydantic is not explicitly defined for logs, we return dicts
    return [{
        "id": l.id,
        "expense_id": l.expense_id,
        "actor_id": l.actor_id,
        "from_state": l.from_state,
        "to_state": l.to_state,
        "timestamp": l.timestamp,
        "note": l.note,
        "ip_address": l.ip_address
    } for l in logs]
