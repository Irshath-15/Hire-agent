import fitz

doc = fitz.open('uploads/divya.resume.pdf')
print(f'PDF has {len(doc)} pages')

for page_num in range(len(doc)):
    page = doc.load_page(page_num)
    text = page.get_text()
    print(f'\n=== PAGE {page_num + 1} ===')
    print(f'Text length: {len(text)}')
    print('First 300 chars:')
    print(repr(text[:300]))
    print('All lines:')
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for i, line in enumerate(lines[:15]):
        print(f'{i}: "{line}"')

doc.close()