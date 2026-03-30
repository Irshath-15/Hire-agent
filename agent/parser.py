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
        
        try:
            for page_num, page in enumerate(doc):
                try:
                    # Render page to image using fitz
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                    img_data = pix.tobytes("ppm")
                    img = Image.open(io.BytesIO(img_data))
                    
                    # OCR the image using Tesseract via pytesseract
                    ocr_text = ocr_image_with_tesseract(img)
                    if ocr_text.strip():
                        text += ocr_text + "\n"
                except Exception as page_err:
                    print(f"Page {page_num} OCR error: {page_err}")
                    continue
                    
        except Exception as e:
            print(f"PDF OCR loop error: {e}")
    
    try:
        doc.close()
    except:
        pass
    
    return text.strip(), image_based

def extract_text_from_docx(file_path: str) -> tuple:
    """Extract text from DOCX file - returns actual document text."""
    try:
        doc = docx.Document(file_path)
        text = ""
        
        # Extract from paragraphs
        for para in doc.paragraphs:
            if para.text.strip():
                text += para.text + "\n"
        
        # Extract from tables if present
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    if cell.text.strip():
                        text += cell.text + "\n"
        
        return text.strip(), False  # DOCX is never image-based
    except Exception as e:
        print(f"DOCX extraction error: {e}")
        return f"[ERROR] Could not read DOCX: {str(e)}", False

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
    # First try to extract name before AI processing
    inferred_name = infer_name_from_text(raw_text)
    
    prompt = f"""You are a resume parser. Extract information from this resume and return ONLY a valid JSON object with no markdown, no code blocks, and no explanation. Return ONLY the JSON.

{{
  "name": "{inferred_name or 'null'}",
  "email": "email address or null",
  "phone": "phone number or null",
  "current_role": "most recent job title or null",
  "experience_years": "total years of experience as a number or null",
  "skills": "comma separated list of skills or null",
  "education": "highest qualification and institution or null",
  "red_flags": "any employment gaps, inconsistencies, vague roles — or null if none"
}}

IMPORTANT: Do NOT change or generate the name field. Keep it as: {inferred_name or 'null'}
Only extract email, phone, skills, experience, education, and red_flags from the resume text.

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
            "name": inferred_name,
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
            value = result.get(field)
            # Convert string 'null'/'None' to Python None
            if value is None or value == 'null' or value == 'None' or value == '':
                result[field] = None
            else:
                result[field] = value
        
        # Force name to be the inferred one if available
        if inferred_name:
            result["name"] = inferred_name
        
        print(f"[PARSER] Parsed JSON successfully: name={result.get('name')}, email={result.get('email')}")
        return result
    except json.JSONDecodeError as e:
        print(f"[PARSER] JSON parse error: {e}, raw response: {raw[:200]}")
        return {
            "name": inferred_name,
            "email": None,
            "phone": None,
            "current_role": None,
            "experience_years": None,
            "skills": None,
            "education": None,
            "red_flags": None
        }

def infer_name_from_text(raw_text: str) -> str | None:
    """Try to infer candidate name from raw resume text - improved extraction."""
    import re

    if not raw_text or not raw_text.strip():
        return None

    lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
    print(f"[NAME_EXTRACT] First 10 lines: {[lines[i] for i in range(min(10, len(lines)))]}")
    
    # Strategy 1: Look for explicit "Name:" or "Contact:" patterns
    for line in lines:
        # Match patterns like "Name: John Doe" or "JOHN DOE"
        m = re.search(r"^\s*(?:name|candidate|applicant)\s*[:\-]\s*([A-Za-zÀ-ÖØ-öø-ÿ\s.,'-]+?)(?:\s*$|[,\|])", line, re.I)
        if m:
            candidate = m.group(1).strip()
            if candidate and 2 < len(candidate.split()) <= 5:
                return candidate
    
    # Strategy 2: Email prefix often contains name (PRIORITIZE THIS)
    email_match = re.search(r"([\w.%+-]+)@", raw_text)
    if email_match:
        local = email_match.group(1)
        # Convert email to name: john.doe → John Doe, john_silva → John Silva
        if '_' in local or '.' in local:
            name = re.sub(r'[._]', ' ', local).title()
            if name and len(name.split()) <= 5:
                print(f"[NAME_EXTRACT] Using email-derived name: '{name}'")
                return name
    
    # Strategy 3: First line that looks like a name (2-4 capitalized words)
    # But skip lines that are clearly not names
    for i, line in enumerate(lines[:15]):  # Check first 15 lines
        print(f"[NAME_EXTRACT] Checking line {i}: '{line}'")
        
        # Skip common headers and non-name content
        skip_keywords = ['resume', 'cv', 'curriculum', 'vitae', 'experience', 'summary', 'objective', 
                        'email', 'phone', 'address', 'linkedin', 'objective', 'skills', 'education',
                        'certifications', 'awards', 'projects', 'languages', 'level', 'contest',
                        'achievement', 'technical', 'additional', 'information', 'national', 'project',
                        'bachelor', 'technology', 'information', 'engineering', 'computer', 'science',
                        'university', 'college', 'school', 'institute', 'department', 'faculty']
        
        if any(skip in line.lower() for skip in skip_keywords):
            print(f"[NAME_EXTRACT] Skipping line {i} - contains skip keyword")
            continue
        
        words = line.split()
        
        # Good candidate if: 1-4 words, all start with capital, all alphabetic, no numbers
        if 1 <= len(words) <= 4:
            if all(re.match(r"^[A-Za-zÀ-ÖØ-öø-ÿ'-]+$", w) for w in words):
                # Extra check: if it looks like a real name pattern
                if all(w[0].isupper() for w in words if w):
                    # Additional validation: not too long, no common non-name patterns
                    if len(line) <= 50 and not re.search(r'\d', line):  # No numbers
                        print(f"[NAME_EXTRACT] Found potential name: '{line}'")
                        return line
    
    # Strategy 3.5: Look for initials + name pattern (S. DIVYA, etc.)
    for i, line in enumerate(lines[:10]):
        # Look for patterns like "S. DIVYA" or "JOHN DOE"
        if re.match(r'^[A-Z]\.\s+[A-Z]+', line):  # S. DIVYA
            print(f"[NAME_EXTRACT] Found initial.name pattern: '{line}'")
            return line
    
    # Strategy 4: Look for Phone/Email section header
    for i, line in enumerate(lines[:20]):
        if 'phone' in line.lower() or 'email' in line.lower():
            # Name is usually above contact info
            if i > 0:
                prev_line = lines[i-1]
                if len(prev_line.split()) <= 4 and all(w[0].isupper() for w in prev_line.split() if w):
                    return prev_line

    # Strategy 5: If no name found, try to derive from email as last resort
    email_match = re.search(r"([\w.%+-]+)@", raw_text)
    if email_match:
        local = email_match.group(1)
        # Try different variations
        variations = [
            local.replace('.', ' ').replace('_', ' ').title(),
            local.split('.')[0].title() if '.' in local else local.title(),
            local.split('_')[0].title() if '_' in local else local.title()
        ]
        for name in variations:
            if name and len(name.split()) <= 3:
                print(f"[NAME_EXTRACT] Last resort - using email variation: '{name}'")
                return name

    print("[NAME_EXTRACT] No name found")
    return None


def parse_resume(file_path: str) -> dict:
    try:
        raw_text, is_image_based = extract_text(file_path)
        print(f"[PARSER] Extracted {len(raw_text) if raw_text else 0} chars from {os.path.basename(file_path)}")
    except Exception as e:
        print(f"[PARSER] extract_text failed: {type(e).__name__}: {str(e)}")
        return {
            'name': None,
            'email': None,
            'phone': None,
            'current_role': None,
            'experience_years': None,
            'skills': None,
            'education': None,
            'red_flags': f'[ERROR] Text extraction failed: {str(e)}',
            'raw_text': '',
            'is_image_based': False
        }
    
    # If no text could be extracted, return appropriate error
    if not raw_text or raw_text.startswith('['):
        print(f"[PARSER] No text extracted or error: {raw_text[:100] if raw_text else 'empty'}")
        return {
            'name': None,
            'email': None,
            'phone': None,
            'current_role': None,
            'experience_years': None,
            'skills': None,
            'education': None,
            'red_flags': raw_text or '[ERROR] Could not extract text - ensure file is readable',
            'raw_text': raw_text or '',
            'is_image_based': is_image_based
        }

    # First, try to extract name BEFORE AI parsing
    try:
        inferred_name = infer_name_from_text(raw_text)
        print(f"[PARSER] Inferred name: {inferred_name}")
    except Exception as e:
        print(f"[PARSER] infer_name_from_text failed: {type(e).__name__}: {str(e)}")
        inferred_name = None
    
    # Then parse with AI - but use fallback if it fails
    try:
        parsed = parse_resume_with_ai(raw_text)
        print(f"[PARSER] AI parsing succeeded: {parsed.get('name')}")
    except Exception as e:
        print(f"[PARSER] parse_resume_with_ai failed: {type(e).__name__}: {str(e)}")
        # Use simple fallback parsing
        parsed = simple_extract(raw_text)
        parsed['name'] = inferred_name or parsed.get('name')
        print(f"[PARSER] Using fallback parser, name={parsed.get('name')}")
    
    parsed['raw_text'] = raw_text
    parsed['is_image_based'] = is_image_based

    # Ensure name is set
    if not parsed.get('name') and inferred_name:
        parsed['name'] = inferred_name
        print(f"[PARSER] Using inferred name: {inferred_name}")
    
    print(f"[PARSER] Final result: name={parsed.get('name')}, email={parsed.get('email')}")
    return parsed


def simple_extract(raw_text: str) -> dict:
    """Simple fallback extraction when AI parsing fails."""
    import re
    
    result = {
        'name': None,
        'email': None,
        'phone': None,
        'current_role': None,
        'experience_years': None,
        'skills': None,
        'education': None,
        'red_flags': None
    }
    
    try:
        # Try to find email
        email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', raw_text)
        if email_match:
            result['email'] = email_match.group(0)
        
        # Try to find phone
        phone_match = re.search(r'(?:\+\d{1,3}[-.]?)?\(?\d{3}\)?[-.]?\d{3}[-.]?\d{4}', raw_text)
        if phone_match:
            result['phone'] = phone_match.group(0)
        
        # Try to find name from first line or contact section
        lines = [l.strip() for l in raw_text.split('\n') if l.strip()]
        if lines:
            first_line = lines[0]
            if not any(x in first_line.lower() for x in ['phone', 'email', 'address', 'linkedin']):
                result['name'] = first_line[:100]  # Use first line as name if it looks reasonable
        
        print(f"[PARSER] Simple extract: name={result.get('name')}, email={result.get('email')}")
    except Exception as e:
        print(f"[PARSER] Simple extract error: {e}")
    
    return result