"""
Onboarding Email Helpers — IPAWAS Platform

notify_admins_new_request  : email all HQ admins when a new request arrives
send_rejection_email       : email applicant when their request is rejected
"""

import logging

from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


def _get_hq_admin_emails():
    """Return list of (email, full_name) for all active HQ admins."""
    return list(
        User.objects.filter(user_type="ipawas_admin", is_active=True)
        .exclude(email="")
        .values_list("email", "first_name", "last_name")
    )


def notify_admins_new_request(onboarding_request, review_url):
    """
    Email all active HQ admins about a new pending onboarding request.

    Args:
        onboarding_request: OnboardingRequest instance
        review_url: Absolute URL to the dashboard review page
    """
    try:
        from core.email.services import get_system_email_service

        admins = _get_hq_admin_emails()
        if not admins:
            logger.warning("No active HQ admin emails — skipping onboarding notification.")
            return

        svc = get_system_email_service()
        req = onboarding_request

        subject = (
            f"[IPAWAS] New onboarding request — "
            f"{req.full_name} ({req.member_state.ipa_acronym})"
        )
        html = f"""
        <p>A new onboarding request requires your review.</p>
        <table style="border-collapse:collapse;font-family:Arial,sans-serif;font-size:14px;">
          <tr><td style="padding:4px 12px 4px 0;font-weight:bold;color:#555;">Applicant</td>
              <td style="padding:4px 0;">{req.full_name}</td></tr>
          <tr><td style="padding:4px 12px 4px 0;font-weight:bold;color:#555;">Email</td>
              <td style="padding:4px 0;">{req.email}</td></tr>
          <tr><td style="padding:4px 12px 4px 0;font-weight:bold;color:#555;">Member State</td>
              <td style="padding:4px 0;">{req.member_state.country_name} ({req.member_state.ipa_acronym})</td></tr>
          <tr><td style="padding:4px 12px 4px 0;font-weight:bold;color:#555;">Job Title</td>
              <td style="padding:4px 0;">{req.job_title}</td></tr>
          <tr><td style="padding:4px 12px 4px 0;font-weight:bold;color:#555;">Requested Role</td>
              <td style="padding:4px 0;">{req.get_requested_role_display()}</td></tr>
          <tr><td style="padding:4px 12px 4px 0;font-weight:bold;color:#555;">Submitted</td>
              <td style="padding:4px 0;">{req.submitted_at.strftime('%Y-%m-%d %H:%M UTC')}</td></tr>
          <tr><td style="padding:4px 12px 4px 0;font-weight:bold;color:#555;">IP Address</td>
              <td style="padding:4px 0;">{req.ip_address or 'Unknown'}</td></tr>
        </table>
        <p style="margin-top:20px;">
          <a href="{review_url}"
             style="background:#1b7a4c;color:white;padding:10px 20px;border-radius:6px;
                    text-decoration:none;font-weight:bold;display:inline-block;">
            Review Request
          </a>
        </p>
        <p style="color:#888;font-size:12px;">— IPAWAS Platform</p>
        """

        for email, first, last in admins:
            name = f"{first} {last}".strip() or "Admin"
            try:
                svc.send_email(
                    to_email=email,
                    to_name=name,
                    subject=subject,
                    html_content=html,
                )
            except Exception as exc:
                logger.error(
                    "Failed to notify admin %s about onboarding request %d: %s",
                    email, req.pk, exc,
                )

    except Exception as exc:
        logger.error(
            "notify_admins_new_request failed for request %d: %s",
            onboarding_request.pk, exc,
        )


def send_rejection_email(onboarding_request):
    """
    Notify the applicant that their request was not approved.

    Args:
        onboarding_request: OnboardingRequest instance (status='rejected')
    """
    try:
        from core.email.services import get_system_email_service

        svc = get_system_email_service()
        req = onboarding_request

        reason_block = ""
        if req.rejection_reason:
            reason_block = (
                f"<p><strong>Reason:</strong></p>"
                f"<p style='padding:10px;background:#f9f9f9;border-left:3px solid #ccc;'>"
                f"{req.rejection_reason}</p>"
            )

        html = f"""
        <p>Dear {req.full_name},</p>
        <p>Thank you for your interest in joining the IPAWAS platform.</p>
        <p>After reviewing your request, we are unable to grant access at this time.</p>
        {reason_block}
        <p>If you believe this is an error or have questions, please contact the
           IPAWAS Secretariat directly.</p>
        <p>Best regards,<br>
           <strong>IPAWAS Secretariat</strong><br>
           Investment Promotion Agencies of West Africa</p>
        """

        svc.send_email(
            to_email=req.email,
            to_name=req.full_name,
            subject="Your IPAWAS platform access request",
            html_content=html,
        )

    except Exception as exc:
        logger.error(
            "send_rejection_email failed for onboarding request %d: %s",
            onboarding_request.pk, exc,
        )
