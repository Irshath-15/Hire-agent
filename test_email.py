#!/usr/bin/env python3
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.actions import send_email
from dotenv import load_dotenv
load_dotenv()

# Test email send
result = send_email(
    to_address="test@example.com",  # Replace with your test email
    subject="Test Email from HireAgent",
    body="This is a test email to verify SMTP/SendGrid configuration."
)

print("Email send result:")
print(f"Status: {result.get('status')}")
print(f"Message: {result.get('message', result.get('error', 'N/A'))}")
print(f"To: {result.get('to', 'N/A')}")
print(f"Subject: {result.get('subject', 'N/A')}")