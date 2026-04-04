from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.postgres import get_db
from app.models.schema import User
from app.schemas.user import UserResponse, UserCreate
from app.api.deps import get_current_active_user, RoleChecker
from app.services.auth import get_password_hash

router = APIRouter()
admin_role_checker = RoleChecker(["Admin"])

@router.get("/", response_model=List[UserResponse], dependencies=[Depends(admin_role_checker)])
def get_users(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    return db.query(User).offset(skip).limit(limit).all()

@router.put("/{user_id}", response_model=UserResponse, dependencies=[Depends(admin_role_checker)])
def update_user(user_id: int, user_update: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db_user.email = user_update.email
    db_user.name = user_update.name
    db_user.role = user_update.role
    if user_update.password:
        db_user.password_hash = get_password_hash(user_update.password)
    
    db.commit()
    db.refresh(db_user)
    return db_user
