import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import settings
import logging
from typing import List, Optional
import os

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        # Get SMTP host from either setting
        self.smtp_host = settings.get_smtp_host()
        self.smtp_port = settings.smtp_port
        self.smtp_user = settings.smtp_user
        self.smtp_password = settings.smtp_password
        self.smtp_from = settings.smtp_from or self.smtp_user
        self.smtp_from_name = settings.smtp_from_name
        
        if self.smtp_host and self.smtp_user and self.smtp_password:
            self.enabled = True
            print(f"✓ Email service enabled: {self.smtp_host}:{self.smtp_port} as {self.smtp_user}")
        else:
            self.enabled = False
            print(f"⚠ Email service disabled: host='{self.smtp_host}', user='{self.smtp_user}'")
    
    async def send_email(
        self,
        recipient_email: str,
        subject: str,
        body: str,
        cc_recipients: Optional[List[str]] = None
    ) -> bool:
        """Send email using SMTP"""
        if not self.enabled:
            logger.info(f"📧 Email NOT sent (disabled) to {recipient_email}: {subject}")
            return False
        
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
            logger.info(f"📧 Connecting to {self.smtp_host}:{self.smtp_port}...")
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                
                recipients = [recipient_email]
                if cc_recipients:
                    recipients.extend(cc_recipients)
                
                server.sendmail(self.smtp_from, recipients, msg.as_string())
            
            logger.info(f"✓ Email sent successfully to {recipient_email}: {subject}")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"✗ SMTP Authentication failed: {str(e)}")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"✗ SMTP Error: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"✗ Email error ({type(e).__name__}): {str(e)}")
            return False

email_service = EmailService()
