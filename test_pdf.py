import sys
sys.path.append('.')
from agent.parser import extract_text
import re

try:
    text, is_image = extract_text('uploads/divya.resume.pdf')
    print('=== FIRST 20 LINES ===')
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for i, line in enumerate(lines[:20]):
        print(f'{i}: "{line}"')
    print('=== EMAIL SEARCH ===')
    email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    if email_match:
        print(f'Found email: {email_match.group(0)}')
    print('=== NAME PATTERN SEARCH ===')
    for i, line in enumerate(lines[:10]):
        if re.match(r'^[A-Z]\.\s+[A-Z]+', line):
            print(f'Found initial.name pattern at line {i}: "{line}"')
except Exception as e:
    print(f'Error: {e}')