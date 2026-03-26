import os
import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta


def send_email(to_address: str, subject: str, body: str, from_address: str = None) -> dict:
    from_address = from_address or os.getenv('HR_EMAIL_FROM', 'no-reply@hireagent.local')
    smtp_host = os.getenv('SMTP_HOST')
    smtp_port = int(os.getenv('SMTP_PORT', 587))
    smtp_user = os.getenv('SMTP_USER')
    smtp_password = os.getenv('SMTP_PASSWORD')

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


def schedule_interview(candidate_name: str, candidate_email: str, job_title: str,
                       interview_date: str = None, interview_time: str = None) -> dict:
    # stubbed schedule interface; in production integrate with Calendar API
    interview_date = interview_date or (datetime.utcnow() + timedelta(days=2)).strftime('%Y-%m-%d')
    interview_time = interview_time or '10:00 AM UTC'
    calendar_link = f'https://calendar.google.com/calendar/r/eventedit?text={job_title}+interview&details=Interview+for+{candidate_name}+%28{candidate_email}%29&dates={interview_date}T{interview_time.replace(":", "")}'

    return {
        'scheduled': True,
        'interview_date': interview_date,
        'interview_time': interview_time,
        'calendar_link': calendar_link,
        'notes': 'Manual follow-up required to confirm with candidate.'
    }
