import io
import requests
from PIL import Image
import pytesseract

def perform_ocr(image_url_or_base64: str, claimed_amount: float):
    # In a real environment we would download the image from S3
    # and decode using PIL. We use simple heuristics here for demonstration.
    try:
        if image_url_or_base64.startswith('http'):
            response = requests.get(image_url_or_base64)
            img = Image.open(io.BytesIO(response.content))
        else:
            # Assuming it's base64 locally passed or dummy path
            img = Image.open(image_url_or_base64)

        text = pytesseract.image_to_string(img)
        
        # Simple extraction logic (in reality use regex for money)
        extracted_amount = claimed_amount  # MOCK
        discrepancy_flags = []
        if abs(extracted_amount - claimed_amount) / claimed_amount > 0.05:
            discrepancy_flags.append("AMOUNT_MISMATCH_5_PERCENT")
            
        return {
            "merchant": "UNKNOWN",
            "date": "UNKNOWN",
            "extracted_amount": extracted_amount,
            "discrepancy_flags": discrepancy_flags,
            "match_result": {
                "amount_match": len(discrepancy_flags) == 0
            }
        }
    except Exception as e:
        return {"error": str(e), "discrepancy_flags": ["OCR_FAILED"]}
