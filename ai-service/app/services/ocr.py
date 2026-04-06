import io
import re
import requests
import cv2
import numpy as np
import imagehash
from PIL import Image, ImageOps
import pytesseract
from dateutil import parser
import base64

pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'

def preprocess_image(pil_img: Image.Image) -> Image.Image:
    # Convert to grayscale; Tesseract handles internal binarization better than manual cv2 sharpening for receipts.
    return pil_img.convert('L')

def extract_merchant(img: Image.Image) -> str:
    # psm 4: Assume a single column of text of variable sizes
    data = pytesseract.image_to_data(img, config='--psm 4', output_type=pytesseract.Output.DICT)
    for i in range(len(data['text'])):
        text = data['text'][i].strip()
        conf = float(data['conf'][i])
        if len(text) > 2 and conf > 50:
            line_num = data['line_num'][i]
            block_num = data['block_num'][i]
            line_words = [data['text'][j] for j in range(len(data['text'])) if data['block_num'][j] == block_num and data['line_num'][j] == line_num and float(data['conf'][j]) > 50]
            if line_words:
                return " ".join(line_words).strip()
    return "UNKNOWN"

def extract_amount(text: str) -> float:
    # Broadly search for currency signs, total/net identifiers, and common receipt terms worldwide
    pattern = r'(?:₹|Rs\.?|INR|\$|Total|Amount|Net|Pay|Sum|Due|Cost|USD)\s*[:\-]?\s*([\d,]+\.\d{2})'
    matches = re.findall(pattern, text, re.IGNORECASE)
    amounts = []
    
    for match in matches:
        clean_str = match.replace(',', '')
        try:
            amounts.append(float(clean_str))
        except ValueError:
            pass
            
    if amounts:
        return max(amounts)
        
    # Extremely relaxed fallback: Identify any standalone decimal that looks like a plausible price 
    # capturing trailing 2 digits mostly to avoid random dates or phone numbers
    fallback_pattern = r'\b(\d{1,6}[\.,]\d{2})\b'
    fallback_matches = re.findall(fallback_pattern, text)
    for match in fallback_matches:
        clean_str = match.replace(',', '.')
        try:
            amounts.append(float(clean_str))
        except ValueError:
            pass
            
    if amounts:
        # Heavily assume the single largest number on a typical receipt is the Grand Total
        return max(amounts)
        
    return 0.0

def extract_date(text: str) -> str:
    lines = text.split('\n')
    for line in lines:
        if len(line.strip()) < 5:
            continue
        try:
            parsed_date = parser.parse(line, fuzzy=False)
            return parsed_date.strftime("%Y-%m-%d")
        except (ValueError, OverflowError):
            pass
            
        try:
            parsed_date = parser.parse(line, fuzzy=True)
            return parsed_date.strftime("%Y-%m-%d")
        except (ValueError, OverflowError):
            continue
    return "UNKNOWN"

def extract_gstin(text: str) -> str:
    pattern = r'\b\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}Z[A-Z\d]{1}\b'
    match = re.search(pattern, text)
    if match:
        return match.group(0)
    return "UNKNOWN"

def perform_ocr(image_url_or_base64: str, claimed_amount: float, claimed_date: str = None) -> dict:
    try:
        if image_url_or_base64.startswith('http'):
            response = requests.get(image_url_or_base64, timeout=15)
            response.raise_for_status()
            img = Image.open(io.BytesIO(response.content))
        elif image_url_or_base64.startswith('data:image'):
            b64data = image_url_or_base64.split(',', 1)[1]
            img = Image.open(io.BytesIO(base64.b64decode(b64data)))
        else:
            img = Image.open(image_url_or_base64)
            
        phash_val = str(imagehash.phash(img))
        processed_img = preprocess_image(img)
        
        # PSM 4 parses columns better (like quantity vs price on receipts)
        text = pytesseract.image_to_string(processed_img, config='--psm 4')
        
        merchant = extract_merchant(processed_img)
        extracted_amount = extract_amount(text)
        extracted_date = extract_date(text)
        gstin = extract_gstin(text)
        
        discrepancy_flags = []
        
        amount_match = True
        if extracted_amount > 0:
            if abs(extracted_amount - claimed_amount) / claimed_amount > 0.05:
                discrepancy_flags.append("AMOUNT_MISMATCH")
                amount_match = False
        else:
            amount_match = False
            
        date_match = True
        if claimed_date and extracted_date != "UNKNOWN":
            claimed_prefix = claimed_date[:10]  # Just the YYYY-MM-DD
            if claimed_prefix != extracted_date:
                date_match = False
                discrepancy_flags.append("DATE_MISMATCH")
                
        return {
            "merchant": merchant,
            "date": extracted_date,
            "extracted_amount": extracted_amount,
            "gstin": gstin,
            "receipt_phash": phash_val,
            "discrepancy_flags": discrepancy_flags,
            "match_result": {
                "amount_match": amount_match,
                "date_match": date_match
            }
        }
    except Exception as e:
        import traceback
        print(f"[OCR ERROR] {e}")
        traceback.print_exc()
        return {
            "merchant": "UNKNOWN",
            "date": "UNKNOWN",
            "extracted_amount": 0.0,
            "gstin": "UNKNOWN",
            "receipt_phash": "UNKNOWN",
            "discrepancy_flags": ["OCR_FAILED"],
            "match_result": {
                "amount_match": False,
                "date_match": False
            }
        }
