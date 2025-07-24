import os
import csv
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path='.env')

def export_logs_to_csv(logs, csv_path):
    # logs: list of dicts, e.g. [{'id': 1, 'desc': 'violation', ...}, ...]
    if not logs:
        return
    with open(csv_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=logs[0].keys())
        writer.writeheader()
        writer.writerows(logs)

def send_logs_email(logs):
    """
    Export logs to CSV and send as email attachment with fixed body and subject.
    """
    if not logs:
        print("No logs to send.")
        return
    csv_file = 'violation_logs.csv'
    export_logs_to_csv(logs, csv_file)
    email_body = (
        "Dear Safety Team,\n\n"
        "Here's the PPE compliance violation report for the last test run:\n\n"
        f"Total violations: {len(logs)}\n\n"
        "Please review the attached detailed report and take appropriate actions.\n\n"
        "Regards,\n"
        "Intelliguard System"
    )
    msg = EmailMessage()
    msg['Subject'] = "PPE Compliance Violation Report"
    msg['From'] = os.getenv('SENDER_EMAIL')
    msg['To'] = os.getenv('ALERT_RECIPIENTS')
    msg.set_content(email_body)
    with open(csv_file, 'rb') as f:
        msg.add_attachment(f.read(), maintype='application', subtype='octet-stream', filename=csv_file)
    try:
        with smtplib.SMTP(os.getenv('SMTP_SERVER'), int(os.getenv('SMTP_PORT'))) as server:
            server.starttls()
            server.login(os.getenv('SMTP_USER'), os.getenv('SMTP_PASSWORD'))
            server.send_message(msg)
        print("Email sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {e}")

# Example usage:
if __name__ == '__main__':
    # Replace with actual log fetching logic
    violation_logs = [
        {'id': 1, 'desc': 'No helmet', 'timestamp': '2024-06-01 10:00'},
        {'id': 2, 'desc': 'Speeding', 'timestamp': '2024-06-01 10:05'},
    ]
    send_logs_email(violation_logs)
