import os
import boto3
import requests
from requests.exceptions import RequestException

AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://localhost:8001/api/v1/ai")

def ensure_presigned_url(url: str) -> str:
    if not url or not url.startswith("https://") or "amazonaws.com" not in url:
        return url
    try:
        bucket_domain = url.split("https://")[1].split("/")[0]
        bucket = bucket_domain.split(".")[0]
        key = url.split(bucket_domain + "/")[1]
        
        s3_client = boto3.client('s3', region_name=os.getenv("AWS_REGION", "us-east-1"))
        return s3_client.generate_presigned_url('get_object', Params={'Bucket': bucket, 'Key': key}, ExpiresIn=300)
    except Exception as e:
        print(f"Failed to sign url: {e}")
        return url

def post_with_retry(endpoint: str, payload: dict):
    url = f"{AI_SERVICE_URL}{endpoint}"
    for attempt in range(2):
        try:
            res = requests.post(url, json=payload, timeout=10)
            res.raise_for_status()
            return res.json()
        except RequestException as e:
            print(f"AI Service Error (Attempt {attempt+1}): {e}")
            if attempt == 1:
                raise

def get_fraud_score(*args, **kwargs):
    # Legacy wrapper handled gracefully now
    payload = kwargs if kwargs else {}
    if args and len(args) >= 5:
        payload = {
            "employee_id": args[0],
            "amount": args[1],
            "category": args[2],
            "merchant": args[3],
            "date": args[4]
        }
    try:
        return post_with_retry("/fraud-score", payload)
    except:
        return {"risk_score": 0.5, "risk_flags": ["AI_SERVICE_UNAVAILABLE"], "recommendation": "REVIEW"}

def get_categorization(title: str, description: str):
    try:
        return post_with_retry("/categorize", {"title": title, "description": description})
    except:
        return {"predicted_category": None, "confidence_score": None, "method": "fallback"}

def run_ocr_validation(receipt_image_url: str, claimed_amount: float, expense_date: str = None):
    try:
        presigned_url = ensure_presigned_url(receipt_image_url)
        return post_with_retry("/ocr", {"receipt_image_url": presigned_url, "claimed_amount": claimed_amount, "expense_date": expense_date})
    except:
        return {"merchant": "UNKNOWN", "date": "UNKNOWN", "extracted_amount": 0.0, "gstin": "UNKNOWN", "receipt_phash": "UNKNOWN", "discrepancy_flags": ["OCR_FAILED"], "match_result": {"amount_match": False, "date_match": False}}

def run_full_analysis(receipt_url: str, claimed_amount: float, title: str, description: str, employee_id: int, category: str, date: str, department_id: int, role: str, recent_same_category_count: int, recent_same_amount_count: int):
    presigned_url = ensure_presigned_url(receipt_url)
    payload = {
        "receipt_image_url": presigned_url,
        "claimed_amount": claimed_amount,
        "title": title,
        "description": description,
        "employee_id": employee_id,
        "category": category,
        "date": date,
        "department_id": department_id,
        "role": role,
        "recent_same_category_count": recent_same_category_count,
        "recent_same_amount_count": recent_same_amount_count
    }
    try:
        return post_with_retry("/analyze", payload)
    except:
        return {
            "ocr": None,
            "categorization": {"predicted_category": None, "confidence_score": None, "method": "fallback"},
            "fraud": {"risk_score": 0.5, "risk_flags": ["AI_SERVICE_UNAVAILABLE"], "recommendation": "REVIEW"}
        }
