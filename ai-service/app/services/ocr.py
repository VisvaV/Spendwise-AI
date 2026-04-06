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
    return pil_img.convert('L')

def extract_merchant(img: Image.Image) -> str:
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
    lines = [l.strip() for l in text.split('\n')]

    # =====================================================
    # UPDATED LOGIC: Prioritize Grand Total / Final Total
    # =====================================================

    # Strategy 1: Strong Grand Total patterns (highest priority)
    grand_total_patterns = [
        r'(?:Grand\s*Total|Net\s*Total|Final\s*Total|Total\s*Amount|Amount\s*Payable|Bill\s*Total|Invoice\s*Total)\s*[:\-=]?\s*₹?[\s]*([\d,]+(?:\.\d{1,2})?)',
        r'(?:Total)\s*[:\-=]?\s*₹?[\s]*([\d,]+(?:\.\d{1,2})?)',  # "Total" but we'll filter later
    ]

    for pattern in grand_total_patterns:
        for match in re.findall(pattern, text, re.IGNORECASE):
            try:
                amount = float(match.replace(',', ''))
                amounts.append(amount)
            except ValueError:
                pass

    # Strategy 2: Look for lines containing "Total" but NOT "Sub"
    # This is the key improvement to avoid Sub-Total
    bare_total_pattern = re.compile(
        r'(?<!Sub[-\s]?)(?<!Sub)(Total)\s*[:\-=]?\s*₹?[\s]*([\d,]+(?:\.\d{1,2})?)',
        re.IGNORECASE
    )

    for line in lines:
        # Skip any line that contains "Sub" anywhere
        if 'sub' in line.lower():
            continue
            
        # Match Total only if it's not part of Sub-Total
        match = bare_total_pattern.search(line)
        if match:
            try:
                amount = float(match.group(2).replace(',', ''))
                amounts.append(amount)
            except ValueError:
                pass

    # Strategy 3: Look for "Total" on one line and amount on next line (common in receipts)
    keyword_pattern = re.compile(r'(?:Grand\s*Total|Net\s*Total|Final\s*Total|Total\s*Amount|Bill\s*Total|Invoice\s*Total|Total)', re.IGNORECASE)
    number_pattern = re.compile(r'^₹?[\s]*([\d,]+(?:\.\d{1,2})?)$')

    for i, line in enumerate(lines):
        if keyword_pattern.search(line) and 'sub' not in line.lower():
            for j in range(i + 1, min(i + 4, len(lines))):
                m = number_pattern.match(lines[j])
                if m:
                    try:
                        amount = float(m.group(1).replace(',', ''))
                        amounts.append(amount)
                        break
                    except ValueError:
                        pass

    # If we found any candidate amounts, return the largest one (usually the final total)
    if amounts:
        return max(amounts)

    # =====================================================
    # Fallbacks (only if above strategies fail)
    # =====================================================

    # Strategy 4: General amount with currency near Total keywords (but still avoid Sub)
    fallback_pattern = re.compile(
        r'(?:Total|Grand|Net|Payable|Due)\s*[:\-=]?\s*₹?[\s]*([\d,]+(?:\.\d{1,2})?)',
        re.IGNORECASE
    )
    for match in fallback_pattern.findall(text):
        if 'sub' not in text.lower():  # extra safety
            try:
                amounts.append(float(match.replace(',', '')))
            except ValueError:
                pass

    if amounts:
        return max(amounts)

    # Strategy 5: Last resort - largest number that appears after "Total" in the entire text
    last_resort = re.findall(r'Total[^\d]*([\d,]+(?:\.\d{1,2})?)', text, re.IGNORECASE)
    for m in last_resort:
        try:
            amounts.append(float(m.replace(',', '')))
        except ValueError:
            pass

    if amounts:
        return max(amounts)

    # Strategy 6: Very last fallback - largest standalone number (with 2 decimal or whole)
    very_last = re.findall(r'\b(\d{1,6}[.,]\d{2})\b', text)
    for m in very_last:
        try:
            amounts.append(float(m.replace(',', '')))
        except ValueError:
            pass

    return max(amounts) if amounts else 0.0


def extract_date(text: str) -> str:
    explicit_patterns = [
        r'\b(\d{1,2}[\s\-/](?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s\-/]\d{4})\b',
        r'\b(\d{4}[-/]\d{1,2}[-/]\d{1,2})\b',
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

    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if len(line) < 5:
            continue
        if re.search(r'GST|GSTIN|Ph:|Tel:|www\.|@|Karnataka|Bengaluru|Layout', line, re.IGNORECASE):
            continue
        try:
            parsed_date = parser.parse(line, fuzzy=False)
            if 2000 <= parsed_date.year <= 2099:
                return parsed_date.strftime("%Y-%m-%d")
        except (ValueError, OverflowError):
            pass

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
            claimed_prefix = claimed_date[:10]
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