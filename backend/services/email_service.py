from azure.identity.aio import ClientSecretCredential
from kiota_authentication_azure.azure_identity_authentication_provider import AzureIdentityAuthenticationProvider
from msgraph import GraphServiceClient
from msgraph.generated.users.item.send_mail.send_mail_post_request_body import SendMailPostRequestBody
from msgraph.generated.models.message import Message
from msgraph.generated.models.item_body import ItemBody
from msgraph.generated.models.body_type import BodyType
from msgraph.generated.models.recipient import Recipient
from msgraph.generated.models.email_address import EmailAddress
from config import settings
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        if settings.azure_client_id and settings.azure_client_secret and settings.azure_tenant_id:
            self.credential = ClientSecretCredential(
                tenant_id=settings.azure_tenant_id,
                client_id=settings.azure_client_id,
                client_secret=settings.azure_client_secret
            )
            self.enabled = True
        else:
            self.enabled = False
            logger.warning("Email service disabled: Azure credentials not configured")
    
    async def get_graph_client(self):
        """Get authenticated Microsoft Graph client"""
        if not self.enabled:
            return None
        
        scopes = ["https://graph.microsoft.com/.default"]
        auth_provider = AzureIdentityAuthenticationProvider(
            self.credential,
            scopes=scopes
        )
        return GraphServiceClient(auth_provider)
    
    async def send_email(
        self,
        recipient_email: str,
        subject: str,
        body: str,
        cc_recipients: Optional[List[str]] = None
    ) -> bool:
        """Send email using Microsoft Graph API"""
        if not self.enabled:
            logger.info(f"Email would be sent to {recipient_email}: {subject}")
            return True
        
        try:
            graph_client = await self.get_graph_client()
            
            # Create message
            message = Message()
            message.subject = subject
            
            # Set body
            body_obj = ItemBody()
            body_obj.content_type = BodyType.Html
            body_obj.content = body
            message.body = body_obj
            
            # Set recipient
            to_recipients = []
            recipient = Recipient()
            email_address = EmailAddress()
            email_address.address = recipient_email
            recipient.email_address = email_address
            to_recipients.append(recipient)
            message.to_recipients = to_recipients
            
            # Set CC recipients if provided
            if cc_recipients:
                cc_list = []
                for cc_email in cc_recipients:
                    cc_recipient = Recipient()
                    cc_address = EmailAddress()
                    cc_address.address = cc_email
                    cc_recipient.email_address = cc_address
                    cc_list.append(cc_recipient)
                message.cc_recipients = cc_list
            
            # Create request body
            request_body = SendMailPostRequestBody()
            request_body.message = message
            
            # Send email
            await graph_client.me.send_mail.post(request_body)
            logger.info(f"Email sent successfully to {recipient_email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return False

email_service = EmailService()
