import os
import smtplib
import imaplib
import email
from email.message import EmailMessage
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import time
import re
from googleapiclient.discovery import build
from google.oauth2 import service_account


def send_email(to_address: str, subject: str, body: str, from_address: str = None) -> dict:
    from_address = from_address or os.getenv('HR_EMAIL_FROM', 'no-reply@hireagent.local')
    smtp_host = os.getenv('SMTP_HOST')
    smtp_port = int(os.getenv('SMTP_PORT', 587))
    smtp_user = os.getenv('SMTP_USER')
    smtp_password = os.getenv('SMTP_PASSWORD')

    # Use SendGrid if configured, fallback to SMTP
    if os.getenv('SENDGRID_API_KEY'):
        return send_sendgrid_email(to_address, subject, body, from_address)

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = from_address
    msg['To'] = to_address
    msg.set_content(body)

    if not smtp_host:
        return {'status': 'skipped', 'message': 'SMTP host not configured, email not sent', 'subject': subject}

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            server.starttls()
            if smtp_user and smtp_password:
                server.login(smtp_user, smtp_password)
            server.send_message(msg)
        return {'status': 'sent', 'to': to_address, 'subject': subject}
    except Exception as e:
        return {'status': 'failed', 'error': str(e)}


def send_sendgrid_email(to_address: str, subject: str, body: str, from_address: str) -> dict:
    """Send email using SendGrid API."""
    try:
        import sendgrid
        from sendgrid.helpers.mail import Mail, Email, To, Content

        sg = sendgrid.SendGridAPIClient(api_key=os.getenv('SENDGRID_API_KEY'))
        from_email = Email(from_address)
        to_email = To(to_address)
        content = Content("text/plain", body)
        mail = Mail(from_email, to_email, subject, content)
        response = sg.client.mail.send.post(request_body=mail.get())

        if response.status_code == 202:
            return {'status': 'sent', 'to': to_address, 'subject': subject, 'provider': 'sendgrid'}
        else:
            return {'status': 'failed', 'error': f'SendGrid error: {response.status_code}'}
    except ImportError:
        return {'status': 'failed', 'error': 'SendGrid package not installed'}
    except Exception as e:
        return {'status': 'failed', 'error': str(e)}


def check_rsvp_responses(candidate_email: str, job_title: str) -> dict:
    """Check Gmail/IMAP for RSVP responses to interview invitations."""
    imap_host = os.getenv('IMAP_HOST', 'imap.gmail.com')
    imap_user = os.getenv('IMAP_USER')
    imap_password = os.getenv('IMAP_PASSWORD')

    if not imap_user or not imap_password:
        return {'status': 'skipped', 'message': 'IMAP not configured'}

    try:
        mail = imaplib.IMAP4_SSL(imap_host)
        mail.login(imap_user, imap_password)
        mail.select('inbox')

        # Search for emails from candidate about this job
        search_criteria = f'FROM "{candidate_email}" SUBJECT "{job_title}"'
        status, messages = mail.search(None, search_criteria)

        responses = []
        if status == 'OK' and messages[0]:
            for msg_id in messages[0].split():
                status, msg_data = mail.fetch(msg_id, '(RFC822)')
                if status == 'OK':
                    email_body = msg_data[0][1]
                    email_message = email.message_from_bytes(email_body)
                    body = get_email_body(email_message)
                    responses.append({
                        'subject': email_message['Subject'],
                        'body': body,
                        'date': email_message['Date']
                    })

        mail.logout()
        return {'status': 'checked', 'responses': responses}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}


def get_email_body(email_message) -> str:
    """Extract plain text body from email message."""
    if email_message.is_multipart():
        for part in email_message.walk():
            if part.get_content_type() == "text/plain":
                return part.get_payload(decode=True).decode('utf-8', errors='ignore')
    else:
        return email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
    return ""


def auto_reschedule(candidate_email: str, job_title: str, current_date: str, current_time: str) -> dict:
    """Auto-reschedule interview if candidate declines or no-shows."""
    rsvp_check = check_rsvp_responses(candidate_email, job_title)

    if rsvp_check.get('status') == 'checked':
        responses = rsvp_check.get('responses', [])
        for response in responses:
            body_lower = response['body'].lower()
            if any(word in body_lower for word in ['decline', 'cannot attend', 'not available', 'conflict']):
                # Auto-reschedule to next available slot
                new_date = (datetime.strptime(current_date, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
                new_time = current_time  # Keep same time
                return {
                    'rescheduled': True,
                    'new_date': new_date,
                    'new_time': new_time,
                    'reason': 'Candidate declined original time'
                }

    return {'rescheduled': False, 'reason': 'No decline detected'}


def retry_email(to_address: str, subject: str, body: str, max_retries: int = 3) -> dict:
    """Retry email sending up to max_retries times."""
    for attempt in range(max_retries):
        result = send_email(to_address, subject, body)
        if result.get('status') == 'sent':
            return result
        time.sleep(2 ** attempt)  # Exponential backoff

    return {'status': 'failed', 'error': f'Failed after {max_retries} attempts'}


def schedule_interview(candidate_name: str, candidate_email: str, job_title: str,
                       interview_date: str = None, interview_time: str = None) -> dict:
    """Schedule interview with calendar integration."""
    interview_date = interview_date or (datetime.utcnow() + timedelta(days=2)).strftime('%Y-%m-%d')
    interview_time = interview_time or '10:00 AM UTC'

    # Integrate with Google Calendar / Cronofy / Nylas if configured
    calendar_link = create_calendar_event(candidate_name, candidate_email, job_title, interview_date, interview_time)

    return {
        'scheduled': True,
        'interview_date': interview_date,
        'interview_time': interview_time,
        'calendar_link': calendar_link,
        'notes': 'Interview scheduled. RSVP monitoring active.'
    }


def create_calendar_event(candidate_name: str, candidate_email: str, job_title: str, date: str, time: str) -> str:
    """Create calendar event using Google Calendar API."""
    try:
        # Use service account for automation
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        calendar_id = os.getenv('GOOGLE_CALENDAR_ID', 'primary')  # Default to primary calendar

        if not creds_path:
            # Fallback to manual link
            return f'https://calendar.google.com/calendar/r/eventedit?text={job_title}+interview&details=Interview+for+{candidate_name}+%28{candidate_email}%29&dates={date}T{time.replace(":", "").replace(" ", "")}'

        credentials = service_account.Credentials.from_service_account_file(
            creds_path, scopes=['https://www.googleapis.com/auth/calendar']
        )

        service = build('calendar', 'v3', credentials=credentials)

        # Parse date and time
        start_datetime = datetime.strptime(f"{date} {time}", "%Y-%m-%d %I:%M %p")
        end_datetime = start_datetime + timedelta(hours=1)  # Assume 1-hour interview

        event = {
            'summary': f'{job_title} Interview - {candidate_name}',
            'description': f'Interview for {candidate_name} ({candidate_email})',
            'start': {
                'dateTime': start_datetime.isoformat(),
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': end_datetime.isoformat(),
                'timeZone': 'UTC',
            },
            'attendees': [
                {'email': candidate_email},
            ],
            'reminders': {
                'useDefault': True,
            },
        }

        created_event = service.events().insert(calendarId=calendar_id, body=event).execute()
        return created_event.get('htmlLink', f'Event created: {created_event["id"]}')

    except Exception as e:
        # Fallback to link
        return f'https://calendar.google.com/calendar/r/eventedit?text={job_title}+interview&details=Interview+for+{candidate_name}+%28{candidate_email}%29&dates={date}T{time.replace(":", "").replace(" ", "")} (Error: {str(e)})'
