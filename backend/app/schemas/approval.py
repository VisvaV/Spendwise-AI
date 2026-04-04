from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ApprovalAction(BaseModel):
    action: str  # APPROVED, REJECTED, PENDING_INFO
    note: Optional[str] = None

class ApprovalResponse(BaseModel):
    id: int
    expense_id: int
    approver_id: Optional[int]
    role_required: str
    action: Optional[str]
    note: Optional[str]
    acted_at: Optional[datetime]
    deadline_at: datetime

    class Config:
        from_attributes = True
