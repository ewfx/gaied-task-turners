import email
from email import policy
import os

def read_email_from_file(file_path):
    """Reads an email from an .eml file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            msg = email.message_from_file(f, policy=policy.default)
        return msg
    except Exception as e:
        print(f"Error reading email from {file_path}: {e}")
        return None

def get_email_body(msg):
    """Extracts the email's text body."""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                return part.get_payload(decode=True).decode()
    else:
        return msg.get_payload(decode=True).decode()

def get_email_details(msg):
    """Gets sender, subject, and body."""
    sender = msg['from']
    subject = msg['subject']
    body = get_email_body(msg)
    return sender, subject, body

def get_email_attachments(msg, output_dir="attachments"):
    """Extracts and saves attachments."""
    attachments =""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get('Content-Disposition') is None:
                continue
            filename = part.get_filename()
            if filename:
                filepath = os.path.join(output_dir, filename)
                with open(filepath, 'wb') as f:
                    f.write(part.get_payload(decode=True))
                attachments.append(filepath)
    return attachments