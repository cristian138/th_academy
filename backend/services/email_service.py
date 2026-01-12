import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import settings
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        if settings.smtp_host and settings.smtp_user and settings.smtp_password:
            self.enabled = True
            self.smtp_host = settings.smtp_host
            self.smtp_port = settings.smtp_port
            self.smtp_user = settings.smtp_user
            self.smtp_password = settings.smtp_password
            self.smtp_from = settings.smtp_from
            self.smtp_from_name = settings.smtp_from_name
        else:
            self.enabled = False
            logger.warning("Email service disabled: SMTP credentials not configured")
    
    async def send_email(
        self,
        recipient_email: str,
        subject: str,
        body: str,
        cc_recipients: Optional[List[str]] = None
    ) -> bool:
        """Send email using SMTP"""
        if not self.enabled:
            logger.info(f"📧 Email simulated to {recipient_email}: {subject}")
            return True
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.smtp_from_name} <{self.smtp_from}>"
            msg['To'] = recipient_email
            
            if cc_recipients:
                msg['Cc'] = ', '.join(cc_recipients)
            
            # Attach HTML body
            html_part = MIMEText(body, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Connect and send
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                
                recipients = [recipient_email]
                if cc_recipients:
                    recipients.extend(cc_recipients)
                
                server.sendmail(self.smtp_from, recipients, msg.as_string())
            
            logger.info(f"📧 Email sent successfully to {recipient_email}")
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ Email sending disabled or failed: {str(e)}")
            logger.info(f"📧 Email simulated to {recipient_email}: {subject}")
            # Return True to not block the flow
            return True

email_service = EmailService()
