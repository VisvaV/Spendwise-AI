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
    img = ImageOps.autocontrast(img, cutoff=1)   # Better contrast for receipts
    return img

def extract_merchant(img: Image.Image) -> str:
    data = pytesseract.image_to_data(img, config='--psm 6', output_type=pytesseract.Output.DICT)
    for i in range(len(data['text'])):
        text = data['text'][i].strip()
        conf = float(data['conf'][i])
        if len(text) > 3 and conf > 60:
            line_num = data['line_num'][i]
            block_num = data['block_num'][i]
            line_words = [data['text'][j] for j in range(len(data['text'])) 
                         if data['block_num'][j] == block_num and data['line_num'][j] == line_num and float(data['conf'][j]) > 50]
            if line_words:
                return " ".join(line_words).strip()
    return "UNKNOWN"

def extract_amount(text: str) -> float:
    """New aggressive logic to prefer FINAL TOTAL over Sub-Total"""
    amounts = []
    lines = [line.strip() for line in text.split('\n') if line.strip()]

    # 1. Highest priority: Explicit final total keywords
    high_priority = re.compile(
        r'(?:Grand\s*Total|Net\s*Total|Final\s*Total|Bill\s*Total|Invoice\s*Total|Total\s*Amount|Amount\s*Payable|Payable\s*Amount|Total:)\s*[:\-=]?\s*₹?\s*([\d,]+(?:\.\d{1,2})?)',
        re.IGNORECASE
    )
    for match in high_priority.findall(text):
        try:
            amounts.append(float(match.replace(',', '')))
        except ValueError:
            pass

    # 2. Any "Total" that is NOT on the same line as "Sub"
    for line in lines:
        lower = line.lower()
        if 'sub' in lower:
            continue  # Skip Sub-Total completely

        match = re.search(r'total\s*[:\-=]?\s*₹?\s*([\d,]+(?:\.\d{1,2})?)', line, re.IGNORECASE)
        if match:
            try:
                amounts.append(float(match.group(1).replace(',', '')))
            except ValueError:
                pass

    # 3. "Total" on one line + amount on next line (common in your receipt)
    for i, line in enumerate(lines):
        if re.search(r'total', line, re.IGNORECASE) and 'sub' not in line.lower():
            for j in range(i + 1, min(i + 5, len(lines))):
                num_match = re.search(r'^₹?\s*([\d,]+(?:\.\d{1,2})?)$', lines[j])
                if num_match:
                    try:
                        amounts.append(float(num_match.group(1).replace(',', '')))
                    except ValueError:
                        pass

    # Take the LARGEST amount found (final total is always bigger)
    if amounts:
        return max(amounts)

    # 4. Last resort - largest number in the entire OCR text
    all_numbers = re.findall(r'\b(\d{1,6}[.,]\d{0,2})\b', text)
    for n in all_numbers:
        try:
            amounts.append(float(n.replace(',', '')))
        except ValueError:
            pass

    return max(amounts) if amounts else 0.0


def extract_date(text: str) -> str:
    # (unchanged - keeping original date logic)
    explicit_patterns = [
        r'\b(\d{1,2}[\s\-/](?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s\-/]\d{4})\b',
        r'\b(\d{4}[-/]\d{1,2}[-/]\d{1,2})\b',
        r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{4})\b',
    ]
    for pat in explicit_patterns:
        match = re.search(pat, text, re.IGNORECASE)
        if match:
            try:
                parsed = parser.parse(match.group(1), fuzzy=False)
                return parsed.strftime("%Y-%m-%d")
            except:
                pass
    return "UNKNOWN"


def extract_gstin(text: str) -> str:
    pattern = r'\b\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}Z[A-Z\d]{1}\b'
    match = re.search(pattern, text)
    return match.group(0) if match else "UNKNOWN"


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
        
        # Changed to psm 6 + better config
        text = pytesseract.image_to_string(
            processed_img, 
            config='--psm 6 --oem 3'
        )

        merchant = extract_merchant(processed_img)
        extracted_amount = extract_amount(text)
        extracted_date = extract_date(text)
        gstin = extract_gstin(text)

        discrepancy_flags = []

        amount_match = extracted_amount > 0 and abs(extracted_amount - claimed_amount) / claimed_amount <= 0.05

        if not amount_match and extracted_amount > 0:
            discrepancy_flags.append("AMOUNT_MISMATCH")

        date_match = True
        if claimed_date and extracted_date != "UNKNOWN":
            if claimed_date[:10] != extracted_date:
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
            "match_result": {"amount_match": False, "date_match": False}
        }