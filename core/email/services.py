"""
Email Service for IPAWAS Platform using Mailjet.

This module handles all email communications including:
- Invitation emails
- Inquiry notifications
- System alerts
- Password reset emails
"""

import logging
from typing import Dict, List, Optional

from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from mailjet_rest import Client

logger = logging.getLogger(__name__)


class MailjetService:
    """
    Service class for sending emails via Mailjet.

    Provides:
    - Template-based email sending
    - HTML + plain text fallback
    - Attachment support
    - Error handling and logging
    - Email tracking
    """

    def __init__(self):
        """Initialize Mailjet client"""
        self.api_key = getattr(settings, "MAILJET_API_KEY", "")
        self.api_secret = getattr(settings, "MAILJET_SECRET_KEY", "")
        self.sender_email = getattr(settings, "MAILJET_SENDER_EMAIL", "noreply@ipawas.org")
        self.sender_name = getattr(settings, "MAILJET_SENDER_NAME", "IPAWAS Platform")

        if self.api_key and self.api_secret:
            self.client = Client(auth=(self.api_key, self.api_secret), version="v3.1")
        else:
            self.client = None
            logger.warning("Mailjet credentials not configured. Emails will not be sent.")

    def send_email(
        self,
        to_email: str,
        to_name: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        cc: Optional[List[Dict]] = None,
        bcc: Optional[List[Dict]] = None,
        attachments: Optional[List[Dict]] = None,
        custom_id: Optional[str] = None,
        track_opens: bool = True,
        track_clicks: bool = True,
    ) -> bool:
        """
        Send an email via Mailjet.

        Args:
            to_email: Recipient email address
            to_name: Recipient name
            subject: Email subject
            html_content: HTML version of email
            text_content: Plain text version (auto-generated if not provided)
            cc: List of CC recipients [{'Email': 'email@example.com', 'Name': 'Name'}]
            bcc: List of BCC recipients
            attachments: List of attachments
            custom_id: Custom ID for tracking
            track_opens: Enable open tracking
            track_clicks: Enable click tracking

        Returns:
            bool: True if sent successfully, False otherwise
        """
        if not self.client:
            logger.error("Cannot send email: Mailjet not configured")
            return False

        # Generate plain text if not provided
        if not text_content:
            text_content = strip_tags(html_content)

        # Prepare email data
        email_data = {
            "Messages": [
                {
                    "From": {
                        "Email": self.sender_email,
                        "Name": self.sender_name,
                    },
                    "To": [
                        {
                            "Email": to_email,
                            "Name": to_name,
                        }
                    ],
                    "Subject": subject,
                    "TextPart": text_content,
                    "HTMLPart": html_content,
                    "TrackOpens": "enabled" if track_opens else "disabled",
                    "TrackClicks": "enabled" if track_clicks else "disabled",
                }
            ]
        }

        # Add custom ID if provided
        if custom_id:
            email_data["Messages"][0]["CustomID"] = custom_id

        # Add CC recipients
        if cc:
            email_data["Messages"][0]["Cc"] = cc

        # Add BCC recipients
        if bcc:
            email_data["Messages"][0]["Bcc"] = bcc

        # Add attachments
        if attachments:
            email_data["Messages"][0]["Attachments"] = attachments

        try:
            # Send email
            result = self.client.send.create(data=email_data)

            if result.status_code == 200:
                logger.info(f"Email sent successfully to {to_email}: {subject}")
                return True
            else:
                logger.error(
                    f"Failed to send email to {to_email}: {result.status_code} - {result.json()}"
                )
                return False

        except Exception as e:
            logger.exception(f"Error sending email to {to_email}: {str(e)}")
            return False

    def add_to_newsletter_list(self, email: str) -> bool:
        """
        Add an email address to the Mailjet newsletter contact list.

        Uses the v3 REST API (contactslist_managecontact action) which is separate
        from the v3.1 send API used by self.client.

        Returns True on success, False on any failure (caller should treat as non-critical).
        """
        list_id = getattr(settings, "MAILJET_NEWSLETTER_LIST_ID", "")
        if not list_id or not self.api_key or not self.api_secret:
            logger.debug("Newsletter list sync skipped: credentials or list ID not configured.")
            return False

        try:
            v3_client = Client(auth=(self.api_key, self.api_secret), version="v3")
            data = {"Email": email, "Action": "addnoforce"}
            result = v3_client.contactslist_managecontact.create(id=list_id, data=data)
            if result.status_code in (200, 201):
                logger.info(f"Added {email} to Mailjet newsletter list {list_id}")
                return True
            logger.warning(
                f"Mailjet newsletter list add returned {result.status_code} for {email}: {result.json()}"
            )
            return False
        except Exception as e:
            logger.exception(f"Error adding {email} to Mailjet newsletter list: {e}")
            return False

    def send_template_email(
        self, to_email: str, to_name: str, subject: str, template_name: str, context: Dict, **kwargs
    ) -> bool:
        """
        Send email using Django template.

        Args:
            to_email: Recipient email
            to_name: Recipient name
            subject: Email subject
            template_name: Name of template file (without extension)
            context: Context data for template
            **kwargs: Additional arguments for send_email

        Returns:
            bool: True if sent successfully
        """
        try:
            # Render HTML template
            html_content = render_to_string(f"invitations/{template_name}.html", context)
            # Try to render text template (fallback to stripping HTML)
            try:
                text_content = render_to_string(f"invitations/{template_name}.txt", context)
            except Exception:
                text_content = strip_tags(html_content)

            return self.send_email(
                to_email=to_email,
                to_name=to_name,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                **kwargs,
            )

        except Exception as e:
            logger.exception(
                f"Error sending template email {template_name} to {to_email}: {str(e)}"
            )
            return False


class InvitationEmailService:
    """Service for sending invitation emails"""

    def __init__(self):
        self.mailjet = MailjetService()

    def send_invitation_email(self, invitation) -> bool:
        """
        Send invitation email to new IPA staff member.

        Args:
            invitation: Invitation instance

        Returns:
            bool: True if sent successfully
        """

        registration_url = settings.SITE_URL + invitation.get_registration_url()

        context = {
            "invitation": invitation,
            "member_state": invitation.member_state,
            "role": invitation.get_role_display(),
            "registration_url": registration_url,
            "expires_at": invitation.expires_at,
            "days_until_expiry": invitation.days_until_expiry,
            "inviter_name": invitation.get_inviter_name(),
            "invitation_message": invitation.invitation_message,
            "site_name": "IPAWAS",
            "site_url": settings.SITE_URL,
        }

        if invitation.member_state:
            subject = f"You're invited to join {invitation.member_state.ipa_acronym} on IPAWAS"
        else:
            subject = "You're invited to join IPAWAS as an HQ Administrator"

        success = self.mailjet.send_template_email(
            to_email=invitation.email,
            to_name=invitation.email.split("@")[0],  # Use email username if name not available
            subject=subject,
            template_name="invitation_email",
            context=context,
            custom_id=f"invitation_{invitation.token}",
        )

        if success:
            invitation.mark_email_sent()

        return success

    def send_invitation_reminder(self, invitation) -> bool:
        """
        Send reminder email for pending invitation.

        Args:
            invitation: Invitation instance

        Returns:
            bool: True if sent successfully
        """
        registration_url = settings.SITE_URL + invitation.get_registration_url()

        context = {
            "invitation": invitation,
            "member_state": invitation.member_state,
            "registration_url": registration_url,
            "expires_at": invitation.expires_at,
            "days_until_expiry": invitation.days_until_expiry,
            "is_reminder": True,
            "site_name": "IPAWAS",
            "site_url": settings.SITE_URL,
        }

        if invitation.member_state:
            subject = f"Reminder: Your invitation to join {invitation.member_state.ipa_acronym} on IPAWAS"
        else:
            subject = "Reminder: Your invitation to join IPAWAS as an HQ Administrator"

        return self.mailjet.send_template_email(
            to_email=invitation.email,
            to_name=invitation.email.split("@")[0],
            subject=subject,
            template_name="invitation_reminder",
            context=context,
            custom_id=f"invitation_reminder_{invitation.token}",
        )


class InquiryEmailService:
    """Service for sending inquiry-related emails"""

    def __init__(self):
        self.mailjet = MailjetService()

    def send_new_inquiry_notification(self, inquiry, recipients: List) -> bool:
        """
        Notify IPA staff of new investor inquiry.

        Args:
            inquiry: InvestorInquiry instance
            recipients: List of IPAUser instances to notify

        Returns:
            bool: True if all emails sent successfully
        """
        inquiry_url = settings.SITE_URL + inquiry.get_absolute_url()

        context = {
            "inquiry": inquiry,
            "inquiry_url": inquiry_url,
            "member_state": inquiry.member_state,
            "site_name": "IPAWAS",
            "site_url": settings.SITE_URL,
        }

        subject = f"New Investor Inquiry: {inquiry.subject}"

        success_count = 0
        for ipa_user in recipients:
            if ipa_user.notify_on_inquiry and ipa_user.user.email_notifications:
                success = self.mailjet.send_template_email(
                    to_email=ipa_user.user.email,
                    to_name=ipa_user.user.get_full_name(),
                    subject=subject,
                    template_name="inquiry_notification",
                    context=context,
                    custom_id=f"inquiry_{inquiry.id}_notify",
                )
                if success:
                    success_count += 1

        return success_count > 0

    def send_inquiry_response(self, inquiry, response_message: str) -> bool:
        """
        Send response to investor inquiry.

        Args:
            inquiry: InvestorInquiry instance
            response_message: Response message from IPA staff

        Returns:
            bool: True if sent successfully
        """
        context = {
            "inquiry": inquiry,
            "response_message": response_message,
            "member_state": inquiry.member_state,
            "site_name": "IPAWAS",
            "site_url": settings.SITE_URL,
        }

        subject = f"Re: {inquiry.subject}"

        return self.mailjet.send_template_email(
            to_email=inquiry.email,
            to_name=inquiry.full_name,
            subject=subject,
            template_name="inquiry_response",
            context=context,
            custom_id=f"inquiry_{inquiry.id}_response",
            cc=(
                [
                    {
                        "Email": inquiry.member_state.contact_email,
                        "Name": inquiry.member_state.ipa_acronym,
                    }
                ]
                if inquiry.member_state.contact_email
                else None
            ),
        )

    def send_inquiry_confirmation(self, inquiry) -> bool:
        """
        Send automatic confirmation email to investor who submitted inquiry.

        Args:
            inquiry: InvestorInquiry instance

        Returns:
            bool: True if sent successfully
        """
        context = {
            "inquiry": inquiry,
            "reference_number": inquiry.reference_number,
            "member_state": inquiry.member_state,
            "inquiry_type": inquiry.get_inquiry_type_display(),
            "site_name": "IPAWAS",
            "site_url": settings.SITE_URL,
            "contact_email": "infodesk@ipawas.org",
            "contact_phone": "+234 (0) 906 204 0061",
        }

        subject = f"Inquiry Received - {inquiry.reference_number}"

        return self.mailjet.send_template_email(
            to_email=inquiry.email,
            to_name=inquiry.full_name,
            subject=subject,
            template_name="inquiry_confirmation",
            context=context,
            custom_id=f"inquiry_{inquiry.id}_confirmation",
        )


class SystemEmailService:
    """Service for system emails (password reset, notifications, etc.)"""

    def __init__(self):
        self.mailjet = MailjetService()

    def send_password_reset_email(self, user, reset_url: str) -> bool:
        """
        Send password reset email.

        Args:
            user: User instance
            reset_url: Password reset URL with token

        Returns:
            bool: True if sent successfully
        """
        context = {
            "user": user,
            "reset_url": reset_url,
            "site_name": "IPAWAS",
            "site_url": settings.SITE_URL,
        }

        subject = "Reset your IPAWAS password"

        return self.mailjet.send_template_email(
            to_email=user.email,
            to_name=user.get_full_name(),
            subject=subject,
            template_name="password_reset",
            context=context,
            custom_id=f"password_reset_{user.id}",
        )

    def send_welcome_email(self, user, ipa_user=None) -> bool:
        """
        Send welcome email to new staff member.

        Args:
            user: User instance
            ipa_user: IPAUser instance (None for HQ admin users)

        Returns:
            bool: True if sent successfully
        """
        if ipa_user is not None:
            dashboard_url = settings.SITE_URL + ipa_user.get_dashboard_url()
            member_state = ipa_user.member_state
            subject = f"Welcome to IPAWAS - {ipa_user.member_state.ipa_acronym}"
        else:
            from django.urls import reverse
            dashboard_url = settings.SITE_URL + reverse("dashboard:hq:overview")
            member_state = None
            subject = "Welcome to IPAWAS - HQ Administration"

        context = {
            "user": user,
            "ipa_user": ipa_user,
            "member_state": member_state,
            "dashboard_url": dashboard_url,
            "site_name": "IPAWAS",
            "site_url": settings.SITE_URL,
        }

        success = self.mailjet.send_template_email(
            to_email=user.email,
            to_name=user.get_full_name(),
            subject=subject,
            template_name="welcome_email",
            context=context,
            custom_id=f"welcome_{user.id}",
        )

        return success

    def send_account_deactivated_email(self, user) -> bool:
        """
        Notify user their account has been deactivated.

        Args:
            user: User instance

        Returns:
            bool: True if sent successfully
        """
        context = {
            "user": user,
            "site_name": "IPAWAS",
            "site_url": settings.SITE_URL,
            "support_email": settings.SUPPORT_EMAIL,
        }

        subject = "Your IPAWAS account has been deactivated"

        return self.mailjet.send_template_email(
            to_email=user.email,
            to_name=user.get_full_name(),
            subject=subject,
            template_name="account_deactivated",
            context=context,
        )

    def send_permission_changed_email(self, user, ipa_user, changed_permissions: Dict) -> bool:
        """
        Notify user their permissions have changed.

        Args:
            user: User instance
            ipa_user: IPAUser instance
            changed_permissions: Dict of permission changes

        Returns:
            bool: True if sent successfully
        """
        context = {
            "user": user,
            "ipa_user": ipa_user,
            "changed_permissions": changed_permissions,
            "site_name": "IPAWAS",
            "site_url": settings.SITE_URL,
        }

        subject = "Your IPAWAS permissions have been updated"

        return self.mailjet.send_template_email(
            to_email=user.email,
            to_name=user.get_full_name(),
            subject=subject,
            template_name="permission_changed",
            context=context,
        )


# Convenience function to get email services
def get_invitation_email_service():
    """Get InvitationEmailService instance"""
    return InvitationEmailService()


def get_inquiry_email_service():
    """Get InquiryEmailService instance"""
    return InquiryEmailService()


def get_system_email_service():
    """Get SystemEmailService instance"""
    return SystemEmailService()
