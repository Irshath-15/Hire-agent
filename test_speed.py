import time
from agent.parser import parse_resume

print('Testing optimized PDF parsing...')
start = time.time()
result = parse_resume('sample-shortlist-resume.pdf')
elapsed = time.time() - start

print(f'✓ Completed in {elapsed:.1f} seconds')
print(f'Name: {result.get("name")}')
print(f'Email: {result.get("email")}')
print(f'Text length: {len(result.get("raw_text", ""))} chars')