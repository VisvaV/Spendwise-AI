import os
import requests

AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://localhost:8001/api/v1/ai")

def get_fraud_score(employee_id: int, amount: float, category: str, merchant: str, date: str):
    try:
        res = requests.post(f"{AI_SERVICE_URL}/fraud-score", json={
            "employee_id": employee_id,
            "amount": amount,
            "category": category,
            "merchant": merchant,
            "date": date
        })
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        print("AI Service Error: ", e)
    return {"risk_score": 0.0, "risk_flags": [], "recommendation": "APPROVE"}

def get_categorization(title: str, description: str):
    try:
        res = requests.post(f"{AI_SERVICE_URL}/categorize", json={
            "title": title,
            "description": description
        })
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        print("AI Service Error: ", e)
    return {"predicted_category": None, "confidence_score": None}

def run_ocr_validation(receipt_url: str, claimed_amount: float):
    try:
        res = requests.post(f"{AI_SERVICE_URL}/ocr", json={
            "receipt_image_url": receipt_url,
            "claimed_amount": claimed_amount
        })
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        print("AI Service Error: ", e)
    return {"match_result": {"amount_match": True}}
