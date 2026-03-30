import fitz
import docx
import os
import json
import tempfile
import subprocess
import platform
from groq import Groq
from dotenv import load_dotenv
from PIL import Image
import io

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def ocr_image_with_tesseract(image: Image.Image) -> str:
    """Use Tesseract OCR via pytesseract library."""
    try:
        import pytesseract
        
        # Set tesseract path based on OS
        system = platform.system()
        
        if system == "Windows":
            # Windows path
            pytesseract.pytesseract.pytesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        elif system == "Linux":
            # Linux/Streamlit Cloud - try common paths
            try:
                # Try to find tesseract in PATH
                result = subprocess.run(['which', 'tesseract'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    pytesseract.pytesseract.pytesseract_cmd = result.stdout.strip()
            except:
                # Use default Linux path
                pytesseract.pytesseract.pytesseract_cmd = '/usr/bin/tesseract'
        
        # Try OCR with timeout
        result = pytesseract.image_to_string(image, timeout=10)
        return result.strip() if result else ""
    except Exception as e:
        print(f"OCR Error: {type(e).__name__}: {str(e)}")
        return ""


def extract_text_from_pdf(file_path: str) -> tuple:
    """Extract text from PDF. Handles both searchable and image-based PDFs with Tesseract OCR."""
    try:
        doc = fitz.open(file_path)
    except Exception as e:
        print(f"PDF open error: {e}")
        return f"[ERROR] Could not open PDF: {str(e)}", True
    
    text = ""
    image_based = False
    has_searchable_content = False
    
    # First try to extract text normally
    try:
        for page in doc:
            page_text = page.get_text()
            if page_text.strip():
                text += page_text + "\n"
                has_searchable_content = True
    except Exception as e:
        print(f"PDF text extraction error: {e}")
    
    # If no searchable text found, try OCR on rendered images
    if not has_searchable_content:
        image_based = True
        ocr_attempted = False
        
        try:
            for page_num, page in enumerate(doc):
                try:
                    # Render page to image using fitz
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                    img_data = pix.tobytes("ppm")
                    img = Image.open(io.BytesIO(img_data))
                    
                    # OCR the image using Tesseract via pytesseract
                    ocr_attempted = True
                    ocr_text = ocr_image_with_tesseract(img)
                    if ocr_text.strip():
                        text += ocr_text + "\n"
                except Exception as page_err:
                    print(f"Page {page_num} OCR error: {page_err}")
                    continue
                    
        except Exception as e:
            print(f"PDF OCR loop error: {e}")
            text = ""
        
        # If still no text extracted
        if image_based and not text.strip():
            if ocr_attempted:
                text = "[IMAGE-BASED PDF] OCR processing failed. Please try: 1) Converting PDF to searchable format, 2) Uploading .docx or .txt instead, 3) Using iLovePDF or similar tool to convert"
            else:
                text = "[IMAGE-BASED PDF] Could not extract text using OCR. Please upload a searchable/text-based PDF instead."
    
    try:
        doc.close()
    except:
        pass
    
    return text.strip(), image_based

def extract_text_from_docx(file_path: str) -> tuple:
    """Extract text from DOCX file."""
    doc = docx.Document(file_path)
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text.strip(), False  # DOCX is never image-based

def extract_text(file_path: str) -> tuple:
    """Extract text from various file formats. Returns (text, is_image_based)."""
    ext = os.path.splitext(file_path)[1].lower()
    image_based = False
    
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext == ".docx":
        return extract_text_from_docx(file_path)
    elif ext in [".png", ".jpg", ".jpeg"]:
        try:
            image = Image.open(file_path)
            ocr_text = ocr_image_with_tesseract(image).strip()
            if ocr_text:
                return ocr_text, True
            else:
                return f"[Image file: {os.path.basename(file_path)} -- no text detected]", True
        except Exception as e:
            return f"[Image file: {os.path.basename(file_path)} -- OCR failed: {str(e)}]", True
    else:
        raise ValueError(f"Unsupported file type: {ext}")

def parse_resume_with_ai(raw_text: str) -> dict:
    prompt = f"""You are a resume parser. Extract information from this resume and return ONLY a valid JSON object with no markdown, no code blocks, and no explanation. Return ONLY the JSON.

{{
  "name": "full name or null",
  "email": "email address or null",
  "phone": "phone number or null",
  "current_role": "most recent job title or null",
  "experience_years": "total years of experience as a number or null",
  "skills": "comma separated list of skills or null",
  "education": "highest qualification and institution or null",
  "red_flags": "any employment gaps, inconsistencies, vague roles — or null if none"
}}

Resume text:
{raw_text}"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=800,
            timeout=15.0,
            messages=[{"role": "user", "content": prompt}]
        )
    except Exception as e:
        print(f"Warning: Parser API timeout: {e}")
        # Return fallback with inferred data
        return {
            "name": infer_name_from_text(raw_text),
            "email": None,
            "phone": None,
            "current_role": None,
            "experience_years": None,
            "skills": None,
            "education": None,
            "red_flags": None
        }

    raw = response.choices[0].message.content
    
    # Clean the response: remove markdown code blocks
    clean = raw.replace("```json", "").replace("```", "").strip()
    
    # Try to extract JSON if it's wrapped in extra text
    if "{" in clean and "}" in clean:
        start = clean.find("{")
        end = clean.rfind("}") + 1
        clean = clean[start:end]

    try:
        result = json.loads(clean)
        # Ensure all required fields exist
        required_fields = ["name", "email", "phone", "current_role", "experience_years", "skills", "education", "red_flags"]
        for field in required_fields:
            if field not in result:
                result[field] = None
        return result
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}, raw response: {raw[:200]}")
        return {
            "name": infer_name_from_text(raw_text),
            "email": None,
            "phone": None,
            "current_role": None,
            "experience_years": None,
            "skills": None,
            "education": None,
            "red_flags": None
        }

def infer_name_from_text(raw_text: str) -> str | None:
    """Try to infer candidate name from raw resume text."""
    import re

    if not raw_text or not raw_text.strip():
        return None

    # 1) Look for explicit "Name:" line
    m = re.search(r"^\s*name\s*[:\-]\s*([A-Za-zÀ-ÖØ-öø-ÿ .,'-]{2,80})$", raw_text, re.I | re.M)
    if m:
        candidate = m.group(1).strip()
        if candidate and len(candidate.split()) <= 5:
            return candidate

    # 2) Take first non-empty line, avoid headings and generic lines
    for line in [l.strip() for l in raw_text.splitlines() if l.strip()]:
        lc = line.lower()
        if any(w in lc for w in ["resume", "curriculum", "email", "phone", "experience", "summary", "objective", "profile"]):
            continue
        words = line.split()
        if 1 < len(words) <= 5 and all(re.match(r"^[A-Za-zÀ-ÖØ-öø-ÿ.'-]+$", w) for w in words):
            return line
        break

    # 3) Use email local part if available
    m2 = re.search(r"([\w.%+-]+)@([\w.-]+\.[A-Za-z]{2,})", raw_text)
    if m2:
        local = m2.group(1).replace('.', ' ').replace('_', ' ').title()
        if local and len(local.split()) <= 5:
            return local

    return None


def parse_resume(file_path: str) -> dict:
    raw_text, is_image_based = extract_text(file_path)
    
    # If no text could be extracted, return appropriate error
    if raw_text.startswith('['):
        return {
            'name': None,
            'email': None,
            'phone': None,
            'current_role': None,
            'experience_years': None,
            'skills': None,
            'education': None,
            'red_flags': raw_text,
            'raw_text': raw_text,
            'is_image_based': True
        }

    parsed = parse_resume_with_ai(raw_text)
    parsed['raw_text'] = raw_text
    parsed['is_image_based'] = is_image_based

    if not parsed.get('name'):
        inferred = infer_name_from_text(raw_text)
        if inferred:
            parsed['name'] = inferred
    
    return parsed