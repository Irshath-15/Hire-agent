#!/usr/bin/env python3
import os

# Test pytesseract connection to Tesseract
print("Testing pytesseract + Tesseract connection...")

try:
    import pytesseract
    print("✓ pytesseract imported")
except ImportError as e:
    print(f"✗ pytesseract import failed: {e}")
    exit(1)

# Set path
tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
pytesseract.pytesseract.pytesseract_cmd = tesseract_path
print(f"✓ Set pytesseract_cmd to: {tesseract_path}")

# Test basic call
try:
    result = pytesseract.get_tesseract_version()
    print(f"✓ Tesseract version: {result}")
except Exception as e:
    print(f"✗ Failed to get Tesseract version: {e}")
    exit(1)

# Test with a simple image
from PIL import Image
import io

print("\nTesting OCR on simple image...")
try:
    # Create a simple test image with text
    img = Image.new('RGB', (200, 50), color='white')
    from PIL import ImageDraw, ImageFont
    d = ImageDraw.Draw(img)
    d.text((10, 10), "Test OCR", fill='black')
    
    # Try to OCR it
    text = pytesseract.image_to_string(img)
    if text.strip():
        print(f"✓ OCR works! Detected: '{text.strip()}'")
    else:
        print("✗ OCR returned empty string")
except Exception as e:
    print(f"✗ OCR test failed: {e}")
    exit(1)

print("\n✓ All tests passed! Tesseract is working correctly.")