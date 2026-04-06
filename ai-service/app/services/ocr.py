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

    # Strategy 1a: Grand total keywords on the SAME line (Sub-Total excluded here)
    grand_total_pattern = r'(?:Grand\s*Total|Net\s*Total|Total|Amount\s*Due|Pay|Due)\s*[:\-=]?\s*([\d,]+(?:\.\d{1,2})?)'
    for match in re.findall(grand_total_pattern, text, re.IGNORECASE):
        try:
            amounts.append(float(match.replace(',', '')))
        except ValueError:
            pass

    if amounts:
        return max(amounts)

    # Strategy 1b: Sub-Total and currency symbols (only if no grand total found above)
    sub_pattern = r'(?:Sub[-\s]?Total|Amount|Sum|Cost|₹|Rs\.?|INR|\$)\s*[:\-=]?\s*([\d,]+(?:\.\d{1,2})?)'
    for match in re.findall(sub_pattern, text, re.IGNORECASE):
        try:
            amounts.append(float(match.replace(',', '')))
        except ValueError:
            pass

    if amounts:
        return max(amounts)

    # Strategy 2: keyword on one line, amount on the NEXT line
    keyword_pattern = re.compile(r'(?:Total|Grand\s*Total|Net\s*Total|Amount Due|Pay)', re.IGNORECASE)
    number_pattern = re.compile(r'^[\$₹Rs\.]*\s*([\d,]+(?:\.\d{1,2})?)$')
    for i, line in enumerate(lines):
        if keyword_pattern.search(line):
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

    # Strategy 3: Fallback - largest standalone decimal
    fallback_pattern = r'\b(\d{1,6}[.,]\d{2})\b'
    for match in re.findall(fallback_pattern, text):
        try:
            amounts.append(float(match.replace(',', '.')))
        except ValueError:
            pass

    if amounts:
        return max(amounts)

    # Strategy 4: Last resort - largest plain integer on its own line
    for line in lines:
        clean = line.strip().lstrip('₹$Rs. ')
        if re.fullmatch(r'\d{2,7}', clean):
            try:
                amounts.append(float(clean))
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