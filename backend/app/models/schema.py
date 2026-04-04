from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from app.db.postgres import Base

class Department(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    head_user_id = Column(Integer, ForeignKey("users.id", use_alter=True, name="fk_department_head"))
    
    users = relationship("User", back_populates="department", foreign_keys="User.department_id")
    budgets = relationship("Budget", back_populates="department")
    approval_matrices = relationship("ApprovalMatrix", back_populates="department")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False) # Employee, Manager, Finance, Senior Approver, Admin
    department_id = Column(Integer, ForeignKey("departments.id"))
    manager_id = Column(Integer, ForeignKey("users.id"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    department = relationship("Department", back_populates="users", foreign_keys=[department_id])
    manager = relationship("User", remote_side=[id])

class Budget(Base):
    __tablename__ = "budgets"
    id = Column(Integer, primary_key=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    fiscal_quarter = Column(Integer, nullable=False)
    fiscal_year = Column(Integer, nullable=False)
    total_amount = Column(Float, nullable=False)
    reserved_amount = Column(Float, default=0.0)
    consumed_amount = Column(Float, default=0.0)
    alert_threshold = Column(Float, default=0.8) # 80%

    department = relationship("Department", back_populates="budgets")

class Expense(Base):
    __tablename__ = "expenses"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="INR")
    category = Column(String(100), nullable=False)
    status = Column(String(50), default="DRAFT", index=True)
    submitted_at = Column(DateTime, default=None)
    expense_date = Column(DateTime, nullable=True)
    receipt_s3_url = Column(String(1024))
    receipt_hash = Column(String(255), index=True)
    risk_score = Column(Float)
    risk_flags = Column(JSON, default=[])
    ai_category = Column(String(100))
    ai_confidence = Column(Float)
    business_justification = Column(Text)
    duplicate_flag = Column(Boolean, default=False)
    
    employee = relationship("User")
    approvals = relationship("Approval", back_populates="expense")

class ApprovalMatrix(Base):
    __tablename__ = "approval_matrix"
    id = Column(Integer, primary_key=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True) # null = any dept
    category = Column(String(100), nullable=True) # null = any category
    amount_min = Column(Float, default=0.0)
    amount_max = Column(Float)
    required_roles = Column(ARRAY(String)) # [Manager, Finance]
    
    department = relationship("Department", back_populates="approval_matrices")

class Approval(Base):
    __tablename__ = "approvals"
    id = Column(Integer, primary_key=True, index=True)
    expense_id = Column(Integer, ForeignKey("expenses.id"), nullable=False)
    approver_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    role_required = Column(String(50), nullable=False)
    action = Column(String(50)) # APPROVED, REJECTED, PENDING_INFO
    note = Column(Text)
    acted_at = Column(DateTime)
    deadline_at = Column(DateTime, nullable=False)

    expense = relationship("Expense", back_populates="approvals")
    approver = relationship("User")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    expense_id = Column(Integer, ForeignKey("expenses.id"), nullable=False)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    from_state = Column(String(50))
    to_state = Column(String(50))
    timestamp = Column(DateTime, default=datetime.utcnow)
    note = Column(Text)
    ip_address = Column(String(45))

class PolicyRule(Base):
    __tablename__ = "policy_rules"
    id = Column(Integer, primary_key=True, index=True)
    rule_name = Column(String(255), unique=True, nullable=False)
    rule_type = Column(String(50), nullable=False)
    parameters = Column(JSONB)
    is_active = Column(Boolean, default=True)
