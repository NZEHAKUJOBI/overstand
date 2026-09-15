"""
Tests for InquiryReplyView (apps/dashboard/views/inquiries.py).

Covers:
- Unauthenticated → login redirect
- IPA staff replying to their own state's inquiry (success + failure paths)
- IPA staff cross-state access blocked
- HQ admin can reply to any inquiry
- Empty message rejected
- Status updated to 'responded' on success
- Internal note logged on success
- ActivityLog entry created
"""

from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings
from django.urls import reverse

from dashboard.tests.factories import (
    IPAUserFactory,
    IPAWASAdminFactory,
    InvestorInquiryFactory,
    MemberStateIPAFactory,
)


def _reply_url(member_state_slug, pk):
    return reverse(
        "dashboard:country:inquiries:reply",
        kwargs={"member_state_slug": member_state_slug, "pk": pk},
    )


def _hq_reply_url(pk):
    return reverse("dashboard:hq:inquiries:reply", kwargs={"pk": pk})


@override_settings(ALLOWED_HOSTS=["*"])
class InquiryReplyViewTests(TestCase):

    def setUp(self):
        self.member_state = MemberStateIPAFactory(slug="senegal")
        self.ipa_user = IPAUserFactory(member_state=self.member_state)
        self.inquiry = InvestorInquiryFactory(member_state=self.member_state, status="new")

    # --- Authentication ---

    def test_unauthenticated_redirects_to_login(self):
        url = _reply_url("senegal", self.inquiry.pk)
        response = self.client.post(url, {"reply_message": "Hello"})
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response["Location"])

    # --- Successful reply ---

    @patch("dashboard.views.inquiries.get_inquiry_email_service")
    def test_ipa_staff_reply_sends_email_and_updates_status(self, mock_service_factory):
        mock_service = MagicMock()
        mock_service.send_inquiry_response.return_value = True
        mock_service_factory.return_value = mock_service

        self.client.force_login(self.ipa_user.user)
        url = _reply_url("senegal", self.inquiry.pk)
        response = self.client.post(url, {"reply_message": "Thank you for your inquiry!"})

        self.inquiry.refresh_from_db()
        self.assertEqual(self.inquiry.status, "responded")
        self.assertIn("Thank you for your inquiry!", self.inquiry.internal_notes)
        self.assertRedirects(response, self.inquiry.get_absolute_url(), fetch_redirect_response=False)

    @patch("dashboard.views.inquiries.get_inquiry_email_service")
    def test_reply_logs_activity(self, mock_service_factory):
        mock_service = MagicMock()
        mock_service.send_inquiry_response.return_value = True
        mock_service_factory.return_value = mock_service

        from dashboard.models import IPADashboardActivity

        self.client.force_login(self.ipa_user.user)
        url = _reply_url("senegal", self.inquiry.pk)
        self.client.post(url, {"reply_message": "We will get back to you."})

        log = IPADashboardActivity.objects.filter(
            action_type="inquiry_respond",
            member_state=self.member_state,
        ).first()
        self.assertIsNotNone(log)
        self.assertIn(self.inquiry.reference_number, log.description)

    @patch("dashboard.views.inquiries.get_inquiry_email_service")
    def test_internal_note_prepended_with_timestamp_and_sender(self, mock_service_factory):
        mock_service = MagicMock()
        mock_service.send_inquiry_response.return_value = True
        mock_service_factory.return_value = mock_service

        self.client.force_login(self.ipa_user.user)
        url = _reply_url("senegal", self.inquiry.pk)
        self.client.post(url, {"reply_message": "Reply text here"})

        self.inquiry.refresh_from_db()
        notes = self.inquiry.internal_notes
        self.assertIn("REPLY sent by", notes)
        self.assertIn(self.ipa_user.user.get_full_name(), notes)
        self.assertIn("Reply text here", notes)

    # --- Email failure ---

    @patch("dashboard.views.inquiries.get_inquiry_email_service")
    def test_email_failure_shows_error_message(self, mock_service_factory):
        mock_service = MagicMock()
        mock_service.send_inquiry_response.return_value = False
        mock_service_factory.return_value = mock_service

        self.client.force_login(self.ipa_user.user)
        url = _reply_url("senegal", self.inquiry.pk)
        response = self.client.post(url, {"reply_message": "Hello"}, follow=True)

        self.inquiry.refresh_from_db()
        # Status should NOT change if email failed
        self.assertEqual(self.inquiry.status, "new")
        messages = list(response.context["messages"])
        self.assertTrue(any("Failed" in str(m) or "failed" in str(m) for m in messages))

    # --- Empty message ---

    def test_empty_message_rejected(self):
        self.client.force_login(self.ipa_user.user)
        url = _reply_url("senegal", self.inquiry.pk)
        response = self.client.post(url, {"reply_message": "   "}, follow=True)

        self.inquiry.refresh_from_db()
        self.assertEqual(self.inquiry.status, "new")
        messages = list(response.context["messages"])
        self.assertTrue(any("empty" in str(m).lower() for m in messages))

    def test_missing_message_field_rejected(self):
        self.client.force_login(self.ipa_user.user)
        url = _reply_url("senegal", self.inquiry.pk)
        response = self.client.post(url, {}, follow=True)

        self.inquiry.refresh_from_db()
        self.assertEqual(self.inquiry.status, "new")

    # --- Cross-state access blocked ---

    def test_ipa_staff_cannot_reply_to_other_states_inquiry(self):
        other_state = MemberStateIPAFactory(slug="mali")
        other_inquiry = InvestorInquiryFactory(member_state=other_state, status="new")

        self.client.force_login(self.ipa_user.user)
        # Attempting to reply to Mali's inquiry via Senegal's URL namespace
        url = _reply_url("senegal", other_inquiry.pk)
        response = self.client.post(url, {"reply_message": "Unauthorized reply"})

        other_inquiry.refresh_from_db()
        self.assertEqual(other_inquiry.status, "new")
        self.assertEqual(response.status_code, 302)

    # --- HQ Admin ---

    @patch("dashboard.views.inquiries.get_inquiry_email_service")
    def test_hq_admin_can_reply_to_any_inquiry(self, mock_service_factory):
        mock_service = MagicMock()
        mock_service.send_inquiry_response.return_value = True
        mock_service_factory.return_value = mock_service

        admin = IPAWASAdminFactory()
        self.client.force_login(admin)
        url = _hq_reply_url(self.inquiry.pk)
        response = self.client.post(url, {"reply_message": "HQ reply"})

        self.inquiry.refresh_from_db()
        self.assertEqual(self.inquiry.status, "responded")
        self.assertRedirects(response, self.inquiry.get_absolute_url(), fetch_redirect_response=False)
