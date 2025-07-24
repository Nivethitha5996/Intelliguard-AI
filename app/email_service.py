import smtplib
from typing import List, Optional, Dict
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import logging
import pandas as pd
from io import StringIO
from utils import load_env, get_email_config

logger = logging.getLogger(__name__)
load_env()
email_config = get_email_config()

class EmailService:
    def __init__(self):
        self.smtp_server = email_config['smtp_server']         # <-- add this line
        self.smtp_port = email_config['smtp_port']             # <-- add this line
        self.sender_email = email_config['sender_email']      # SENDER
        self.sender_password = email_config['sender_password']# SENDER PASSWORD
        self.recipient_emails = email_config['recipient_emails'] # RECEIVERS
    
    def send_email(
        self,
        subject: str,
        body: str,
        recipients: List[str],
        attachments: Optional[List[Dict]] = None
    ) -> bool:
        """Send email with optional attachments."""
        try:
            # Create message container
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = ", ".join(recipients)
            msg['Subject'] = subject
            
            # Attach body
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach files if provided
            if attachments:
                for attachment in attachments:
                    part = MIMEApplication(
                        attachment['data'],
                        Name=attachment['filename']
                    )
                    part['Content-Disposition'] = f'attachment; filename="{attachment["filename"]}"'
                    msg.attach(part)
            
            # Connect to SMTP server and send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, recipients, msg.as_string())
            
            logger.info(f"Email sent to {recipients}")
            return True
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False
    
    def send_violation_report(
        self,
        violations: List[Dict],
        time_range: str = "24 hours"
    ) -> bool:
        """Send a formatted violation report email."""
        try:
            # Create CSV attachment
            df = pd.DataFrame(violations)
            csv_buffer = StringIO()
            df.to_csv(csv_buffer, index=False)
            
            subject = f"PPE Compliance Violation Report - Last {time_range}"
            body = f"""
            Dear Safety Team,
            
            Here's the PPE compliance violation report for the last {time_range}:
            
            Total violations: {len(violations)}
            
            Please review the attached detailed report and take appropriate actions.
            
            Regards,
            Intelliguard System
            """
            
            return self.send_email(
                subject=subject,
                body=body,
                recipients=self.recipient_emails,
                attachments=[{
                    'filename': f"ppe_violations_{time_range.replace(' ', '_')}.csv",
                    'data': csv_buffer.getvalue()
                }]
            )
        except Exception as e:
            logger.error(f"Error sending violation report: {e}")
            return False

def send_violation_email(violations: List[Dict], time_range: str = "24 hours") -> bool:
    """Send violation report email."""
    service = EmailService()
    return service.send_violation_report(violations, time_range)

__all__ = ["EmailService", "send_violation_email"]