#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, '.')
from agent.parser import parse_resume

print('Testing other resume files...\n')

files_to_test = ['uploads/resume_selected_1.pdf', 'uploads/resume_reject_1.pdf']

for file in files_to_test:
    try:
        result = parse_resume(file)
        print(f'✓ {file}')
        print(f'  Name: {result.get("name")}')
        print(f'  Email: {result.get("email")}')
        print(f'  Image-based: {result.get("is_image_based")}')
        red_flag = result.get('red_flags')
        if red_flag:
            print(f'  Red Flags: {red_flag[:100]}')
        print()
    except Exception as e:
        print(f'✗ {file} - Error: {str(e)[:80]}\n')
