import fitz
import docx
import os
import json
from groq import Groq
from dotenv import load_dotenv
from PIL import Image
import io

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def extract_text_from_pdf(file_path: str) -> tuple:
    """Extract text from PDF. Handles both searchable and image-based PDFs."""
    doc = fitz.open(file_path)
    text = ""
    image_based = False
    has_searchable_content = False
    
    # First try to extract text normally
    for page in doc:
        page_text = page.get_text()
        if page_text.strip():
            text += page_text + "\n"
            has_searchable_content = True
    
    # If no searchable text found, try OCR on rendered images
    if not has_searchable_content:
        image_based = True
        ocr_attempted = False
        ocr_succeeded = False
        
        try:
            import pytesseract
            ocr_attempted = True
            pytesseract.pytesseract.pytesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
            
            for page_num, page in enumerate(doc):
                try:
                    # Render page to image using fitz
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                    img_data = pix.tobytes("ppm")
                    img = Image.open(io.BytesIO(img_data))
                    
                    # OCR the image
                    ocr_text = pytesseract.image_to_string(img)
                    if ocr_text.strip():
                        text += ocr_text + "\n"
                        ocr_succeeded = True
                except Exception:
                    continue
                    
        except ImportError:
            text = "[Image-based PDF] pytesseract not installed. Cannot process image-based resume."
        except Exception as e:
            if ocr_attempted and not ocr_succeeded:
                text = "[Image-based PDF] Tesseract-OCR not properly configured on system. Cannot extract text."
            else:
                text = f"[Image-based PDF] Could not process: {type(e).__name__}"
        finally:
            # If we attempted OCR but got nothing, set error message
            if image_based and not text:
                text = "[Image-based PDF] Cannot extract text. Tesseract-OCR may not be installed. Please upload a searchable PDF instead."
    
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
            import pytesseract
            image = Image.open(file_path)
            ocr_text = pytesseract.image_to_string(image).strip()
            if ocr_text:
                return ocr_text, True
            else:
                return f"[Image file: {os.path.basename(file_path)} -- no text detected]", True
        except ImportError:
            return f"[Image file: {os.path.basename(file_path)} -- OCR not configured]", True
        except Exception as e:
            raise ValueError(f"Failed to read image file {file_path}: {e}")
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

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )

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
            "name": None,
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