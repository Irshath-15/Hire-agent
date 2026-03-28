#!/usr/bin/env python3
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.parser import extract_text

# Test PDF parsing
pdf_path = input("Enter path to PDF file: ").strip()
if not pdf_path:
    print("No path provided. Exiting.")
    sys.exit(1)

if not os.path.exists(pdf_path):
    print(f"File not found: {pdf_path}")
    sys.exit(1)

try:
    text, is_image_based = extract_text(pdf_path)
    print(f"Extracted text length: {len(text)}")
    print(f"Is image-based: {is_image_based}")
    print("First 500 characters:")
    print(text[:500])
    if len(text) > 500:
        print("... (truncated)")
except Exception as e:
    print(f"Error: {e}")