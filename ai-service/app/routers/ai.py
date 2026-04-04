from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
import asyncio

from app.services.ocr import perform_ocr
from app.services.categorization import categorizer
from app.services.fraud import calculate_risk_score

router = APIRouter()

class OCRRequest(BaseModel):
    receipt_image_url: str
    claimed_amount: float
    expense_date: Optional[str] = None

class CategorizeRequest(BaseModel):
    title: str
    description: Optional[str] = None

class FraudRequest(BaseModel):
    employee_id: int
    amount: float
    category: str
    merchant: str
    date: str
    department_id: Optional[int] = None
    role: Optional[str] = None
    recent_same_category_count: int = 0
    recent_same_amount_count: int = 0

class AnalyzeRequest(BaseModel):
    receipt_image_url: Optional[str] = None
    claimed_amount: float
    title: str
    description: Optional[str] = None
    employee_id: int
    category: str
    date: str
    department_id: Optional[int] = None
    role: Optional[str] = None
    recent_same_category_count: int = 0
    recent_same_amount_count: int = 0

@router.post("/ocr")
def run_ocr(req: OCRRequest):
    return perform_ocr(req.receipt_image_url, req.claimed_amount, req.expense_date)

@router.post("/categorize")
def run_categorization(req: CategorizeRequest):
    return categorizer.categorize(req.title, req.description)

@router.post("/fraud-score")
def run_fraud_scoring(req: FraudRequest):
    return calculate_risk_score(
        req.employee_id, req.amount, req.category, req.merchant, req.date,
        req.department_id, req.role, req.recent_same_category_count, req.recent_same_amount_count
    )

@router.post("/analyze")
async def run_full_analysis(req: AnalyzeRequest):
    # Run in threadpool since the underlying funcs are synchronous
    loop = asyncio.get_event_loop()
    
    ocr_task = loop.run_in_executor(None, perform_ocr, req.receipt_image_url, req.claimed_amount, req.date) if req.receipt_image_url else None
    cat_task = loop.run_in_executor(None, categorizer.categorize, req.title, req.description)
    
    if ocr_task:
        ocr_res, cat_res = await asyncio.gather(ocr_task, cat_task)
        merchant = ocr_res.get("merchant", "UNKNOWN")
    else:
        ocr_res = None
        cat_res = await cat_task
        merchant = "UNKNOWN"
        
    fraud_task = loop.run_in_executor(None, lambda: calculate_risk_score(
        employee_id=req.employee_id, 
        amount=req.claimed_amount, 
        category=req.category, 
        merchant=merchant, 
        date=req.date,
        department_id=req.department_id, 
        role=req.role, 
        recent_same_category_count=req.recent_same_category_count, 
        recent_same_amount_count=req.recent_same_amount_count
    ))
    
    fraud_res = await fraud_task
    
    return {
        "ocr": ocr_res,
        "categorization": cat_res,
        "fraud": fraud_res
    }
