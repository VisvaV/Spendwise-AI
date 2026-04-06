import os
import requests
from requests.exceptions import RequestException

AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://localhost:8001/api/v1/ai")

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
        # Generate a short-lived presigned GET URL so the AI service can access the private S3 object
        import boto3, os
        from urllib.parse import urlparse

        s3 = boto3.client('s3', region_name=os.getenv("AWS_REGION", "ap-south-1"))
        parsed = urlparse(receipt_image_url)
        object_key = parsed.path.lstrip("/")
        bucket = os.getenv("S3_BUCKET_NAME", "spendwise-bucket-visva")

        presigned_url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket, 'Key': object_key},
            ExpiresIn=300
        )

        return post_with_retry("/ocr", {
            "receipt_image_url": presigned_url,
            "claimed_amount": claimed_amount,
            "expense_date": expense_date
        })
    except Exception as e:
        print(f"[OCR] Presign failed: {e}")
        return {
            "merchant": "UNKNOWN",
            "date": "UNKNOWN",
            "extracted_amount": 0.0,
            "gstin": "UNKNOWN",
            "receipt_phash": "UNKNOWN",
            "discrepancy_flags": ["OCR_FAILED"],
            "match_result": {"amount_match": False, "date_match": False}
        }

def run_full_analysis(receipt_url: str, claimed_amount: float, title: str, description: str, employee_id: int, category: str, date: str, department_id: int, role: str, recent_same_category_count: int, recent_same_amount_count: int):
    payload = {
        "receipt_image_url": receipt_url,
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
