from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.postgres import get_db
from app.models.schema import User
from app.schemas.approval import ApprovalAction
from app.api.deps import get_current_active_user
from app.services.approval import process_approval_action

router = APIRouter()

@router.post("/{expense_id}/action")
def act_on_expense(expense_id: int, action_in: ApprovalAction, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    # Role checker isn't hardcoded here; the service will verify the user's role matches the required_role for this step
    res = process_approval_action(db, expense_id, action_in.action, current_user, action_in.note)
    return {"message": "Success", "new_status": res.status}
