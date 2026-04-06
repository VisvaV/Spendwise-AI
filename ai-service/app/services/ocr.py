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
    amounts = []

    # Strategy 1: keyword and amount on the SAME line (e.g. "Total: 3150.00" or "Total: ₹3,150")
    same_line_pattern = r'(?:Total|Grand\s*Total|Net\s*Total|Amount|Sub[-\s]?Total|Pay|Due|Sum|Cost|₹|Rs\.?|INR|\$)\s*[:\-=]?\s*([\d,]+(?:\.\d{1,2})?)'
    for match in re.findall(same_line_pattern, text, re.IGNORECASE):
        try:
            amounts.append(float(match.replace(',', '')))
        except ValueError:
            pass

    if amounts:
        return max(amounts)

    # Strategy 2: keyword on one line, amount on the NEXT line
    # Handles OCR output like:  "Total: ="  followed by  "3150"
    lines = [l.strip() for l in text.split('\n')]
    keyword_pattern = re.compile(r'(?:Total|Grand\s*Total|Net\s*Total|Amount Due|Pay)', re.IGNORECASE)
    number_pattern = re.compile(r'^[\$₹Rs\.]*\s*([\d,]+(?:\.\d{1,2})?)$')
    for i, line in enumerate(lines):
        if keyword_pattern.search(line):
            # Check next 1-3 lines for a standalone number
            for j in range(i + 1, min(i + 4, len(lines))):
                m = number_pattern.match(lines[j])
                if m:
                    try:
                        amounts.append(float(m.group(1).replace(',', '')))
                        break
                    except ValueError:
                        pass

    if amounts:
        return max(amounts)

    # Strategy 3: Fallback — largest standalone decimal on the receipt
    fallback_pattern = r'\b(\d{1,6}[.,]\d{2})\b'
    for match in re.findall(fallback_pattern, text):
        try:
            amounts.append(float(match.replace(',', '.')))
        except ValueError:
            pass

    if amounts:
        return max(amounts)

    # Strategy 4: Last resort — largest plain integer >= 10 on its own line
    # (catches cases like "3150" with no decimal at all)
    for line in lines:
        clean = line.strip().lstrip('₹$Rs. ')
        if re.fullmatch(r'\d{2,7}', clean):
            try:
                amounts.append(float(clean))
            except ValueError:
                pass

    return max(amounts) if amounts else 0.0


def extract_date(text: str) -> str:
    # First pass: look for explicit date patterns to avoid fuzzy misfires
    explicit_patterns = [
        # "16 May 2024", "16-May-2024", "16/May/2024"
        r'\b(\d{1,2}[\s\-/](?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s\-/]\d{4})\b',
        # "2024-04-16", "2024/04/16"
        r'\b(\d{4}[-/]\d{1,2}[-/]\d{1,2})\b',
        # "16/04/2024", "16-04-2024"
        r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{4})\b',
    ]
    for pat in explicit_patterns:
        match = re.search(pat, text, re.IGNORECASE)
        if match:
            try:
                parsed_date = parser.parse(match.group(1), fuzzy=False)
                return parsed_date.strftime("%Y-%m-%d")
            except (ValueError, OverflowError):
                pass

    # Second pass: line-by-line strict parse (no fuzzy)
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if len(line) < 5:
            continue
        # Skip lines that look like addresses, GST numbers, phone numbers etc.
        if re.search(r'GST|GSTIN|Ph:|Tel:|www\.|@|Karnataka|Bengaluru|Layout', line, re.IGNORECASE):
            continue
        try:
            parsed_date = parser.parse(line, fuzzy=False)
            # Sanity check: reject years before 2000 or in the far future
            if 2000 <= parsed_date.year <= 2099:
                return parsed_date.strftime("%Y-%m-%d")
        except (ValueError, OverflowError):
            pass

    # Third pass: fuzzy parse with year sanity check
    for line in lines:
        line = line.strip()
        if len(line) < 5:
            continue
        if re.search(r'GST|GSTIN|Ph:|Tel:|www\.|@|Karnataka|Bengaluru|Layout', line, re.IGNORECASE):
            continue
        try:
            parsed_date = parser.parse(line, fuzzy=True)
            if 2000 <= parsed_date.year <= 2099:
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