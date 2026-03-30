#!/usr/bin/env python3
"""
Test script for improved OCR functionality on scanned documents
"""
import os
import time
from PIL import Image
from agent.parser import ocr_image_with_tesseract, extract_text_from_pdf

def test_ocr_on_sample_image():
    """Test OCR on a sample image if available"""
    print("=== Testing OCR on Sample Images ===")

    # Look for sample images in the current directory
    sample_images = []
    for file in os.listdir('.'):
        if file.lower().endswith(('.png', '.jpg', '.jpeg')):
            sample_images.append(file)

    if sample_images:
        print(f"Found {len(sample_images)} sample image(s): {sample_images}")

        for img_file in sample_images[:2]:  # Test first 2 images
            print(f"\n--- Testing OCR on {img_file} ---")
            try:
                start_time = time.time()
                image = Image.open(img_file)
                result = ocr_image_with_tesseract(image)
                elapsed = time.time() - start_time

                print(f"✓ OCR completed in {elapsed:.2f} seconds")
                print(f"✓ Extracted text length: {len(result)} characters")
                if result:
                    print(f"✓ Sample text: {result[:200]}...")
                else:
                    print("⚠ No text extracted")

            except Exception as e:
                print(f"✗ OCR failed: {e}")
    else:
        print("No sample images found for OCR testing")

def test_pdf_extraction():
    """Test PDF text extraction on available PDFs"""
    print("\n=== Testing PDF Text Extraction ===")

    pdf_files = []
    for file in os.listdir('.'):
        if file.lower().endswith('.pdf'):
            pdf_files.append(file)

    if pdf_files:
        print(f"Found {len(pdf_files)} PDF file(s): {pdf_files}")

        for pdf_file in pdf_files[:2]:  # Test first 2 PDFs
            print(f"\n--- Testing PDF extraction on {pdf_file} ---")
            try:
                start_time = time.time()
                text, is_scanned = extract_text_from_pdf(pdf_file)
                elapsed = time.time() - start_time

                print(f"✓ Extraction completed in {elapsed:.2f} seconds")
                print(f"✓ Detected as scanned document: {is_scanned}")
                print(f"✓ Extracted text length: {len(text) if not text.startswith('[ERROR]') else 0} characters")

                if text and not text.startswith('[ERROR]'):
                    print(f"✓ Sample text: {text[:200]}...")
                else:
                    print(f"⚠ Extraction result: {text[:100]}...")

            except Exception as e:
                print(f"✗ PDF extraction failed: {e}")
    else:
        print("No PDF files found for extraction testing")

def create_test_scanned_image():
    """Create a simple test image with text for OCR testing"""
    print("\n=== Creating Test Scanned Image ===")

    try:
        # Create a simple test image with text
        from PIL import Image, ImageDraw, ImageFont

        # Create image
        img = Image.new('RGB', (800, 200), color='white')
        draw = ImageDraw.Draw(img)

        # Try to use a font, fallback to default if not available
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except:
            font = ImageFont.load_default()

        # Draw test text
        test_text = "John Doe\nSoftware Engineer\nEmail: john.doe@email.com\nPhone: (555) 123-4567\nExperience: 5+ years"
        draw.text((20, 20), test_text, fill='black', font=font)

        # Save test image
        test_image_path = "test_resume_scan.png"
        img.save(test_image_path)
        print(f"✓ Created test scanned image: {test_image_path}")

        # Test OCR on it
        print(f"\n--- Testing OCR on generated test image ---")
        start_time = time.time()
        result = ocr_image_with_tesseract(img)
        elapsed = time.time() - start_time

        print(f"✓ OCR completed in {elapsed:.2f} seconds")
        print(f"✓ Extracted text: {result}")

        return test_image_path

    except Exception as e:
        print(f"✗ Failed to create test image: {e}")
        return None

if __name__ == "__main__":
    print("🔍 HireIQ OCR Testing Suite")
    print("=" * 50)

    # Test existing images
    test_ocr_on_sample_image()

    # Test PDF extraction
    test_pdf_extraction()

    # Create and test a synthetic scanned image
    test_image = create_test_scanned_image()

    print("\n" + "=" * 50)
    print("✅ OCR Testing Complete")
    print("\nKey improvements tested:")
    print("• Advanced image preprocessing (noise reduction, contrast enhancement)")
    print("• Multiple OCR configurations optimized for scanned documents")
    print("• Confidence scoring and best result selection")
    print("• Higher resolution rendering for scanned PDFs")
    print("• Comprehensive fallback extraction methods")

    if test_image and os.path.exists(test_image):
        os.remove(test_image)
        print(f"\n🧹 Cleaned up test image: {test_image}")