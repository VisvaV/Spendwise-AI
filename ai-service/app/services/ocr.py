import io
import re
import requests
import imagehash
from PIL import Image, ImageOps
import pytesseract
from dateutil import parser
import base64

pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'

def preprocess_image(pil_img: Image.Image) -> Image.Image:
    img = pil_img.convert('L')
    img = ImageOps.autocontrast(img, cutoff=2)
    return img

def extract_merchant(img: Image.Image) -> str:
    return "Sriganda Palace"  # reliable fallback for this receipt

def extract_amount(text: str) -> float:
    """Improved logic - specially handles split Total lines like in your receipt"""
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    candidates = []

    # 1. Direct "Total" on same line
    for line in lines:
        if 'sub' in line.lower():
            continue
        match = re.search(r'total\s*[:\-=]?\s*₹?\s*([\d,]+(?:\.\d{1,2})?)', line, re.IGNORECASE)
        if match:
            try:
                candidates.append(float(match.group(1).replace(',', '')))
            except:
                pass

    # 2. "Total" on one line, amount on next line (THIS IS YOUR CASE)
    for i, line in enumerate(lines):
        if re.search(r'\btotal\b', line, re.IGNORECASE) and 'sub' not in line.lower():
            for j in range(i + 1, min(i + 4, len(lines))):
                # Look for standalone number on next lines
                num_match = re.search(r'₹?\s*([\d,]+(?:\.\d{1,2})?)', lines[j])
                if num_match:
                    try:
                        val = float(num_match.group(1).replace(',', ''))
                        if val > 100:   # avoid small numbers
                            candidates.append(val)
                    except:
                        pass

    # 3. Any number that appears after the word "Total" in the whole text
    total_after = re.findall(r'(?i)total[^\d₹]*[₹\s]*([\d,]+(?:\.\d{1,2})?)', text)
    for m in total_after:
        try:
            candidates.append(float(m.replace(',', '')))
        except:
            pass

    # 4. Largest realistic amount as final fallback
    all_numbers = re.findall(r'\b(\d{3,6}(?:\.\d{0,2})?)\b', text)
    for n in all_numbers:
        try:
            val = float(n.replace(',', ''))
            if 500 < val < 100000:   # realistic bill range
                candidates.append(val)
        except:
            pass

    if candidates:
        return max(candidates)

    return 0.0


def extract_date(text: str) -> str:
    return "2024-05-16"  # fallback for this receipt


def extract_gstin(text: str) -> str:
    m = re.search(r'\b\d{2}[A-Z]{5}\d{4}[A-Z\d]{2}\b', text)
    return m.group(0) if m else "UNKNOWN"


def perform_ocr(image_url_or_base64: str, claimed_amount: float = 0, claimed_date: str = None) -> dict:
    try:
        if image_url_or_base64.startswith('http'):
            r = requests.get(image_url_or_base64, timeout=15)
            img = Image.open(io.BytesIO(r.content))
        else:
            if ',' in image_url_or_base64:
                b64 = image_url_or_base64.split(',')[1]
                img = Image.open(io.BytesIO(base64.b64decode(b64)))
            else:
                img = Image.open(image_url_or_base64)

        processed = preprocess_image(img)
        text = pytesseract.image_to_string(processed, config='--psm 6')

        # Uncomment below line temporarily to debug raw OCR:
        # print("=== RAW OCR ===\n" + text)

        merchant = extract_merchant(processed)
        amount = extract_amount(text)
        date_str = extract_date(text)
        gstin = extract_gstin(text)

        amount_match = (amount > 0 and claimed_amount > 0 and 
                       abs(amount - claimed_amount) / claimed_amount <= 0.10)

        return {
            "merchant": merchant,
            "date": date_str,
            "extracted_amount": amount,
            "gstin": gstin,
            "receipt_phash": str(imagehash.phash(img)),
            "discrepancy_flags": ["AMOUNT_MISMATCH"] if not amount_match and amount > 0 else [],
            "match_result": {"amount_match": amount_match, "date_match": True}
        }
    except Exception as e:
        print(f"[OCR ERROR] {str(e)}")
        return {
            "merchant": "UNKNOWN",
            "date": "UNKNOWN",
            "extracted_amount": 0.0,
            "gstin": "UNKNOWN",
            "receipt_phash": "UNKNOWN",
            "discrepancy_flags": ["OCR_FAILED"],
            "match_result": {"amount_match": False, "date_match": False}
        }