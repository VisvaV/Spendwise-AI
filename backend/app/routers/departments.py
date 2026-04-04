from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.postgres import get_db
from app.models.schema import Department, User
from app.schemas.department import DepartmentCreate, DepartmentResponse
from app.api.deps import get_current_active_user, RoleChecker

router = APIRouter()
admin_role_checker = RoleChecker(["Admin"])

@router.post("/", response_model=DepartmentResponse, dependencies=[Depends(admin_role_checker)])
def create_department(dept: DepartmentCreate, db: Session = Depends(get_db)):
    db_dept = db.query(Department).filter(Department.name == dept.name).first()
    if db_dept:
        raise HTTPException(status_code=400, detail="Department already exists")
    
    new_dept = Department(name=dept.name, head_user_id=dept.head_user_id)
    db.add(new_dept)
    db.commit()
    db.refresh(new_dept)
    return new_dept

@router.get("/", response_model=List[DepartmentResponse])
def get_departments(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    return db.query(Department).all()

@router.put("/{dept_id}", response_model=DepartmentResponse, dependencies=[Depends(admin_role_checker)])
def update_department(dept_id: int, dept: DepartmentCreate, db: Session = Depends(get_db)):
    db_dept = db.query(Department).filter(Department.id == dept_id).first()
    if not db_dept:
        raise HTTPException(status_code=404, detail="Department not found")
    
    db_dept.name = dept.name
    db_dept.head_user_id = dept.head_user_id
    db.commit()
    db.refresh(db_dept)
    return db_dept
