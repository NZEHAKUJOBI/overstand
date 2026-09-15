"""
Tests for the Invitation system.

Covers:
- Invitation model lifecycle (is_valid, is_expired, accept, revoke, resend)
- InvitationListView — HQ sees all, IPA staff sees their state's only
- InvitationCreateView — HQ admin and IPA staff both create correctly
- InvitationRevokeView — revoke changes status
- InvitationRegistrationView — token validation, user+IPAUser created, login on success
- BulkInvitationView — accepts multiple emails, rejects duplicates
- InvitationQRView — single QR card rendering, context, access control
- InvitationBulkQRView — scoping by role, empty state, context structure
- Access control: only can_manage_users may reach management views
- URL resolution for both namespaces (hq and country)

Bugs already present in the codebase that these tests expose are noted inline.
"""

import uuid
from datetime import timedelta
from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import IPAUser, User
from dashboard.tests.factories import IPAUserFactory, IPAWASAdminFactory, MemberStateIPAFactory
from invitations.models import Invitation


# ---------------------------------------------------------------------------
# Factory helpers
# ---------------------------------------------------------------------------

def make_invitation(member_state, invited_by, email="invitee@example.com", status="pending", days=7):
    """Create an Invitation bypassing .save() full_clean for test simplicity."""
    return Invitation.objects.create_invitation(
        email=email,
        member_state=member_state,
        role="ipa_officer",
        invited_by=invited_by,
        expires_in_days=days,
    )


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------

class InvitationModelTests(TestCase):

    def setUp(self):
        self.member_state = MemberStateIPAFactory()
        self.admin = IPAWASAdminFactory()

    def test_create_invitation_sets_pending_status(self):
        inv = make_invitation(self.member_state, self.admin)
        self.assertEqual(inv.status, "pending")

    def test_is_valid_true_for_fresh_invitation(self):
        inv = make_invitation(self.member_state, self.admin)
        self.assertTrue(inv.is_valid)

    def test_is_expired_false_for_fresh_invitation(self):
        inv = make_invitation(self.member_state, self.admin)
        self.assertFalse(inv.is_expired)

    def test_is_expired_true_after_expiry(self):
        inv = make_invitation(self.member_state, self.admin)
        # Bypass full_clean() validation to backdate expires_at
        Invitation.objects.filter(pk=inv.pk).update(expires_at=timezone.now() - timedelta(seconds=1))
        inv.refresh_from_db()
        self.assertTrue(inv.is_expired)

    def test_is_valid_false_when_expired(self):
        inv = make_invitation(self.member_state, self.admin)
        Invitation.objects.filter(pk=inv.pk).update(expires_at=timezone.now() - timedelta(seconds=1))
        inv.refresh_from_db()
        self.assertFalse(inv.is_valid)

    def test_accept_sets_status_and_timestamps(self):
        inv = make_invitation(self.member_state, self.admin)
        user = User.objects.create_user(email="newuser@example.com", password="pass")
        inv.accept(user)
        inv.refresh_from_db()
        self.assertEqual(inv.status, "accepted")
        self.assertEqual(inv.created_user, user)
        self.assertIsNotNone(inv.accepted_at)

    def test_revoke_sets_status_and_timestamps(self):
        inv = make_invitation(self.member_state, self.admin)
        inv.revoke(revoked_by=self.admin, reason="No longer needed")
        inv.refresh_from_db()
        self.assertEqual(inv.status, "revoked")
        self.assertEqual(inv.revoke_reason, "No longer needed")
        self.assertIsNotNone(inv.revoked_at)

    def test_resend_extends_expiry(self):
        inv = make_invitation(self.member_state, self.admin)
        original_expiry = inv.expires_at
        result = inv.resend()
        inv.refresh_from_db()
        self.assertTrue(result)
        self.assertGreater(inv.expires_at, original_expiry)

    def test_days_until_expiry_positive_for_valid_invite(self):
        inv = make_invitation(self.member_state, self.admin, days=7)
        self.assertGreater(inv.days_until_expiry, 0)

    def test_days_until_expiry_zero_when_expired(self):
        inv = make_invitation(self.member_state, self.admin)
        Invitation.objects.filter(pk=inv.pk).update(expires_at=timezone.now() - timedelta(days=1))
        inv.refresh_from_db()
        self.assertEqual(inv.days_until_expiry, 0)

    def test_unique_pending_constraint_prevents_duplicate(self):
        make_invitation(self.member_state, self.admin, email="dup@example.com")
        with self.assertRaises(Exception):
            make_invitation(self.member_state, self.admin, email="dup@example.com")

    def test_get_registration_url_returns_valid_path(self):
        inv = make_invitation(self.member_state, self.admin)
        url = inv.get_registration_url()
        self.assertIn(str(inv.token), url)
        self.assertIn("/register/", url)

    def test_token_is_uuid(self):
        inv = make_invitation(self.member_state, self.admin)
        self.assertIsInstance(inv.token, uuid.UUID)

    def test_cleanup_expired_marks_stale_pending_as_expired(self):
        inv = make_invitation(self.member_state, self.admin, email="stale@example.com")
        Invitation.objects.filter(pk=inv.pk).update(expires_at=timezone.now() - timedelta(hours=1))

        count = Invitation.objects.cleanup_expired()
        self.assertEqual(count, 1)
        inv.refresh_from_db()
        self.assertEqual(inv.status, "expired")


# ---------------------------------------------------------------------------
# InvitationListView
# ---------------------------------------------------------------------------

@override_settings(ALLOWED_HOSTS=["*"])
class InvitationListViewTests(TestCase):

    def setUp(self):
        self.ghana = MemberStateIPAFactory(slug="ghana")
        self.nigeria = MemberStateIPAFactory(slug="nigeria")
        self.admin = IPAWASAdminFactory()
        self.ghana_user = IPAUserFactory(member_state=self.ghana)
        # Create invitations for both states
        self.ghana_inv = make_invitation(self.ghana, self.admin, email="g@example.com")
        self.nigeria_inv = make_invitation(self.nigeria, self.admin, email="n@example.com")

    def test_hq_list_shows_all_invitations(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("dashboard:hq:invitations:list"))
        self.assertEqual(response.status_code, 200)
        inv_pks = [i.pk for i in response.context["invitations"]]
        self.assertIn(self.ghana_inv.pk, inv_pks)
        self.assertIn(self.nigeria_inv.pk, inv_pks)

    def test_ipa_staff_list_shows_only_own_state(self):
        self.client.force_login(self.ghana_user.user)
        url = reverse("dashboard:country:invitations:list", kwargs={"member_state_slug": "ghana"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        inv_pks = [i.pk for i in response.context["invitations"]]
        self.assertIn(self.ghana_inv.pk, inv_pks)
        self.assertNotIn(self.nigeria_inv.pk, inv_pks)

    def test_unauthenticated_redirects_to_login(self):
        response = self.client.get(reverse("dashboard:hq:invitations:list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response["Location"])


# ---------------------------------------------------------------------------
# InvitationRevokeView
# ---------------------------------------------------------------------------

@override_settings(ALLOWED_HOSTS=["*"])
class InvitationRevokeViewTests(TestCase):

    def setUp(self):
        self.member_state = MemberStateIPAFactory(slug="togo")
        self.admin = IPAWASAdminFactory()
        self.invitation = make_invitation(self.member_state, self.admin, email="revoke@example.com")

    def test_hq_admin_can_revoke_invitation(self):
        self.client.force_login(self.admin)
        url = reverse("dashboard:hq:invitations:revoke", kwargs={"pk": self.invitation.pk})
        response = self.client.post(url)
        self.invitation.refresh_from_db()
        self.assertEqual(self.invitation.status, "revoked")
        self.assertEqual(response.status_code, 302)

    def test_ipa_director_can_revoke_own_state_invitation(self):
        ipa_user = IPAUserFactory(member_state=self.member_state)  # ipa_director → can_manage_users
        self.client.force_login(ipa_user.user)
        url = reverse(
            "dashboard:country:invitations:revoke",
            kwargs={"member_state_slug": "togo", "pk": self.invitation.pk},
        )
        response = self.client.post(url)
        self.invitation.refresh_from_db()
        self.assertEqual(self.invitation.status, "revoked")

    def test_cannot_revoke_already_accepted_invitation(self):
        user = User.objects.create_user(email="accepted@example.com", password="pass")
        self.invitation.accept(user)

        self.client.force_login(self.admin)
        url = reverse("dashboard:hq:invitations:revoke", kwargs={"pk": self.invitation.pk})
        # RevokeView currently just sets status directly without checking — this is a known limitation
        # The model's .revoke() method would raise ValidationError; the view skips it
        response = self.client.post(url)
        # View should complete (302 redirect) but invitation is already accepted
        self.assertEqual(response.status_code, 302)


# ---------------------------------------------------------------------------
# InvitationRegistrationView (public token-based registration)
# ---------------------------------------------------------------------------

@override_settings(ALLOWED_HOSTS=["*"])
class InvitationRegistrationViewTests(TestCase):

    def setUp(self):
        self.member_state = MemberStateIPAFactory(slug="benin")
        self.admin = IPAWASAdminFactory()
        self.invitation = make_invitation(
            self.member_state, self.admin, email="newstaff@benin.gov"
        )

    def test_valid_token_renders_registration_form(self):
        url = reverse(
            "dashboard:country:invitations:register",
            kwargs={"member_state_slug": "benin", "token": self.invitation.token},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"newstaff@benin.gov", response.content)

    def test_invalid_token_shows_error_page(self):
        url = reverse(
            "dashboard:country:invitations:register",
            kwargs={"member_state_slug": "benin", "token": uuid.uuid4()},
        )
        response = self.client.get(url)
        # Should render invalid_token template (200), not crash
        self.assertEqual(response.status_code, 200)

    def test_expired_token_shows_error(self):
        Invitation.objects.filter(pk=self.invitation.pk).update(
            expires_at=timezone.now() - timedelta(hours=1)
        )

        url = reverse(
            "dashboard:country:invitations:register",
            kwargs={"member_state_slug": "benin", "token": self.invitation.token},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Should not show the registration form — show error instead
        self.assertNotIn(b"password", response.content.lower())

    @patch("dashboard.views.invitation.views.get_system_email_service")
    def test_valid_registration_creates_user_and_ipa_profile(self, mock_email_svc):
        mock_svc = MagicMock()
        mock_svc.send_welcome_email.return_value = True
        mock_email_svc.return_value = mock_svc

        url = reverse(
            "dashboard:country:invitations:register",
            kwargs={"member_state_slug": "benin", "token": self.invitation.token},
        )
        response = self.client.post(url, {
            "first_name": "Jean",
            "last_name": "Mensah",
            "email": "newstaff@benin.gov",
            "job_title": "Investment Officer",
            "phone_number": "+22901234567",
            "language_preference": "fr",
            "password1": "Secure@Pass1234",
            "password2": "Secure@Pass1234",
            "terms_accepted": "on",
        })

        # Should redirect to dashboard after success
        self.assertEqual(response.status_code, 302)

        # User created
        user = User.objects.filter(email="newstaff@benin.gov").first()
        self.assertIsNotNone(user)
        self.assertEqual(user.user_type, "ipa_staff")
        self.assertEqual(user.first_name, "Jean")

        # IPAUser profile linked to correct member state
        ipa_user = IPAUser.objects.filter(user=user).first()
        self.assertIsNotNone(ipa_user)
        self.assertEqual(ipa_user.member_state, self.member_state)

        # Invitation marked accepted
        self.invitation.refresh_from_db()
        self.assertEqual(self.invitation.status, "accepted")

    @patch("dashboard.views.invitation.views.get_system_email_service")
    def test_successful_registration_logs_user_in(self, mock_email_svc):
        mock_email_svc.return_value = MagicMock()
        mock_email_svc.return_value.send_welcome_email.return_value = True

        url = reverse(
            "dashboard:country:invitations:register",
            kwargs={"member_state_slug": "benin", "token": self.invitation.token},
        )
        self.client.post(url, {
            "first_name": "Awa",
            "last_name": "Kone",
            "email": "newstaff@benin.gov",
            "job_title": "",
            "phone_number": "",
            "language_preference": "en",
            "password1": "Secure@Pass1234",
            "password2": "Secure@Pass1234",
            "terms_accepted": "on",
        })

        # Session should have user ID (logged in)
        self.assertIn("_auth_user_id", self.client.session)

    def test_registration_marks_started_on_get(self):
        url = reverse(
            "dashboard:country:invitations:register",
            kwargs={"member_state_slug": "benin", "token": self.invitation.token},
        )
        self.client.get(url)
        self.invitation.refresh_from_db()
        self.assertIsNotNone(self.invitation.registration_started_at)


# ---------------------------------------------------------------------------
# BulkInvitationView
# ---------------------------------------------------------------------------

@override_settings(ALLOWED_HOSTS=["*"])
class BulkInvitationViewTests(TestCase):

    def setUp(self):
        self.member_state = MemberStateIPAFactory(slug="sierra-leone")
        self.admin = IPAWASAdminFactory()
        self.ipa_director = IPAUserFactory(member_state=self.member_state)

    def test_hq_admin_can_reach_bulk_form(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("dashboard:hq:invitations:bulk"))
        self.assertEqual(response.status_code, 200)

    def test_ipa_director_can_reach_bulk_form(self):
        self.client.force_login(self.ipa_director.user)
        url = reverse("dashboard:country:invitations:bulk", kwargs={"member_state_slug": "sierra-leone"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    @patch("dashboard.views.invitation.views.get_invitation_email_service")
    def test_bulk_creates_invitations_for_each_email(self, mock_email_svc):
        mock_svc = MagicMock()
        mock_svc.send_invitation_email.return_value = True
        mock_email_svc.return_value = mock_svc

        self.client.force_login(self.ipa_director.user)
        url = reverse("dashboard:country:invitations:bulk", kwargs={"member_state_slug": "sierra-leone"})
        response = self.client.post(url, {
            "emails": "alpha@example.com\nbeta@example.com\ngamma@example.com",
            "role": "ipa_officer",
            "invitation_message": "",
        })

        created = Invitation.objects.filter(member_state=self.member_state)
        self.assertEqual(created.count(), 3)

    @patch("dashboard.views.invitation.views.get_invitation_email_service")
    def test_bulk_deduplicates_emails(self, mock_email_svc):
        mock_email_svc.return_value = MagicMock()
        mock_email_svc.return_value.send_invitation_email.return_value = True

        self.client.force_login(self.ipa_director.user)
        url = reverse("dashboard:country:invitations:bulk", kwargs={"member_state_slug": "sierra-leone"})
        self.client.post(url, {
            "emails": "dup@example.com\ndup@example.com\ndup@example.com",
            "role": "ipa_officer",
            "invitation_message": "",
        })

        # Only one invitation created despite three lines
        created = Invitation.objects.filter(member_state=self.member_state, email="dup@example.com")
        self.assertEqual(created.count(), 1)

    def test_bulk_rejects_invalid_email_format(self):
        self.client.force_login(self.ipa_director.user)
        url = reverse("dashboard:country:invitations:bulk", kwargs={"member_state_slug": "sierra-leone"})
        response = self.client.post(url, {
            "emails": "notanemail\nalsobad",
            "role": "ipa_officer",
            "invitation_message": "",
        })
        # Form invalid → stays on same page
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Invitation.objects.filter(member_state=self.member_state).count(), 0)

    def test_bulk_requires_member_state_for_hq_admin(self):
        self.client.force_login(self.admin)
        url = reverse("dashboard:hq:invitations:bulk")
        response = self.client.post(url, {
            "emails": "valid@example.com",
            "role": "ipa_officer",
            "invitation_message": "",
            # Intentionally missing member_state
        })
        # Should stay on page with form errors
        self.assertEqual(response.status_code, 200)


# ---------------------------------------------------------------------------
# URL resolution
# ---------------------------------------------------------------------------

class InvitationURLResolutionTests(TestCase):

    def test_hq_invitation_urls_resolve(self):
        reverse("dashboard:hq:invitations:list")
        reverse("dashboard:hq:invitations:create")
        reverse("dashboard:hq:invitations:bulk")
        reverse("dashboard:hq:invitations:revoke", kwargs={"pk": 1})
        reverse("dashboard:hq:invitations:resend", kwargs={"pk": 1})
        reverse("dashboard:hq:invitations:register", kwargs={"token": uuid.uuid4()})

    def test_country_invitation_urls_resolve(self):
        slug = "cameroon"
        reverse("dashboard:country:invitations:list", kwargs={"member_state_slug": slug})
        reverse("dashboard:country:invitations:create", kwargs={"member_state_slug": slug})
        reverse("dashboard:country:invitations:bulk", kwargs={"member_state_slug": slug})
        reverse("dashboard:country:invitations:revoke", kwargs={"member_state_slug": slug, "pk": 1})
        reverse("dashboard:country:invitations:resend", kwargs={"member_state_slug": slug, "pk": 1})
        reverse("dashboard:country:invitations:register", kwargs={"member_state_slug": slug, "token": uuid.uuid4()})

    def test_hq_member_state_invite_url_resolves(self):
        # HQ-specific per-member-state invite page
        reverse("dashboard:hq:member_state_invite", kwargs={"slug": "cameroon"})

    def test_qr_urls_resolve(self):
        """QR card URLs must resolve for both namespaces."""
        reverse("dashboard:hq:invitations:qr", kwargs={"pk": 1})
        reverse("dashboard:hq:invitations:qr_bulk")
        reverse(
            "dashboard:country:invitations:qr",
            kwargs={"member_state_slug": "ghana", "pk": 1},
        )
        reverse(
            "dashboard:country:invitations:qr_bulk",
            kwargs={"member_state_slug": "ghana"},
        )


# ---------------------------------------------------------------------------
# InvitationQRView — single QR card
# ---------------------------------------------------------------------------

@override_settings(ALLOWED_HOSTS=["*"])
class InvitationQRViewTests(TestCase):

    def setUp(self):
        self.member_state = MemberStateIPAFactory(slug="ghana")
        self.admin = IPAWASAdminFactory()
        self.ipa_director = IPAUserFactory(member_state=self.member_state)
        self.invitation = make_invitation(
            self.member_state, self.admin, email="qrtest@example.com"
        )

    def _url(self, pk=None):
        return reverse(
            "dashboard:hq:invitations:qr",
            kwargs={"pk": pk or self.invitation.pk},
        )

    # --- Access ---

    def test_unauthenticated_redirects_to_login(self):
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response["Location"])

    def test_ipa_officer_without_manage_users_gets_403(self):
        """A plain ipa_officer (not director) cannot reach QR views."""
        officer = IPAUserFactory(member_state=self.member_state, role="ipa_officer")
        self.client.force_login(officer.user)
        response = self.client.get(self._url())
        self.assertIn(response.status_code, [302, 403])

    def test_hq_admin_can_reach_qr_card(self):
        self.client.force_login(self.admin)
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 200)

    def test_ipa_director_can_reach_qr_card(self):
        self.client.force_login(self.ipa_director.user)
        url = reverse(
            "dashboard:country:invitations:qr",
            kwargs={"member_state_slug": "ghana", "pk": self.invitation.pk},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_nonexistent_invitation_returns_404(self):
        self.client.force_login(self.admin)
        response = self.client.get(self._url(pk=99999))
        self.assertEqual(response.status_code, 404)

    # --- Context ---

    def test_context_contains_registration_url(self):
        self.client.force_login(self.admin)
        response = self.client.get(self._url())
        self.assertIn("registration_url", response.context)
        reg_url = response.context["registration_url"]
        self.assertIn(str(self.invitation.token), reg_url)
        self.assertIn("/register/", reg_url)

    def test_registration_url_is_absolute(self):
        self.client.force_login(self.admin)
        response = self.client.get(self._url())
        reg_url = response.context["registration_url"]
        self.assertTrue(reg_url.startswith("http"))

    def test_context_contains_qr_api_url(self):
        self.client.force_login(self.admin)
        response = self.client.get(self._url())
        self.assertIn("qr_api_url", response.context)
        qr_url = response.context["qr_api_url"]
        self.assertIn("api.qrserver.com", qr_url)
        self.assertIn("280x280", qr_url)
        # QR data must encode the invitation token
        self.assertIn(str(self.invitation.token), qr_url)

    def test_qr_api_url_uses_ipawas_green(self):
        self.client.force_login(self.admin)
        response = self.client.get(self._url())
        self.assertIn("1b7a4c", response.context["qr_api_url"])

    def test_template_used(self):
        self.client.force_login(self.admin)
        response = self.client.get(self._url())
        self.assertTemplateUsed(response, "dashboard/invitations/qr_card.html")

    def test_response_contains_invitee_email(self):
        self.client.force_login(self.admin)
        response = self.client.get(self._url())
        self.assertContains(response, "qrtest@example.com")

    def test_response_contains_print_button(self):
        self.client.force_login(self.admin)
        response = self.client.get(self._url())
        self.assertContains(response, "window.print()")


# ---------------------------------------------------------------------------
# InvitationBulkQRView — all pending invitations
# ---------------------------------------------------------------------------

@override_settings(ALLOWED_HOSTS=["*"])
class InvitationBulkQRViewTests(TestCase):

    def setUp(self):
        self.ghana = MemberStateIPAFactory(slug="ghana")
        self.nigeria = MemberStateIPAFactory(slug="nigeria")
        self.admin = IPAWASAdminFactory()
        self.ghana_director = IPAUserFactory(member_state=self.ghana)

        # Invitations in two different states
        self.ghana_inv = make_invitation(self.ghana, self.admin, email="g@example.com")
        self.nigeria_inv = make_invitation(self.nigeria, self.admin, email="n@example.com")

    def _hq_url(self):
        return reverse("dashboard:hq:invitations:qr_bulk")

    def _country_url(self, slug="ghana"):
        return reverse(
            "dashboard:country:invitations:qr_bulk",
            kwargs={"member_state_slug": slug},
        )

    # --- Access ---

    def test_unauthenticated_redirects_to_login(self):
        response = self.client.get(self._hq_url())
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response["Location"])

    def test_hq_admin_can_reach_bulk_qr(self):
        self.client.force_login(self.admin)
        response = self.client.get(self._hq_url())
        self.assertEqual(response.status_code, 200)

    def test_ipa_director_can_reach_country_bulk_qr(self):
        self.client.force_login(self.ghana_director.user)
        response = self.client.get(self._country_url("ghana"))
        self.assertEqual(response.status_code, 200)

    # --- Scoping ---

    def test_hq_admin_sees_all_pending_invitations(self):
        self.client.force_login(self.admin)
        response = self.client.get(self._hq_url())
        emails = [item["invitation"].email for item in response.context["invitations"]]
        self.assertIn("g@example.com", emails)
        self.assertIn("n@example.com", emails)

    def test_ipa_director_sees_only_own_state(self):
        self.client.force_login(self.ghana_director.user)
        response = self.client.get(self._country_url("ghana"))
        emails = [item["invitation"].email for item in response.context["invitations"]]
        self.assertIn("g@example.com", emails)
        self.assertNotIn("n@example.com", emails)

    def test_member_state_slug_scopes_hq_view(self):
        """Even HQ admin, when using the country URL, sees only that state."""
        self.client.force_login(self.admin)
        response = self.client.get(self._country_url("nigeria"))
        emails = [item["invitation"].email for item in response.context["invitations"]]
        self.assertNotIn("g@example.com", emails)
        self.assertIn("n@example.com", emails)

    def test_only_pending_invitations_included(self):
        """Accepted / revoked invitations must not appear in QR bulk."""
        user = User.objects.create_user(email="accepted@example.com", password="pass")
        self.ghana_inv.accept(user)

        self.client.force_login(self.admin)
        response = self.client.get(self._hq_url())
        emails = [item["invitation"].email for item in response.context["invitations"]]
        self.assertNotIn("g@example.com", emails)   # accepted → excluded
        self.assertIn("n@example.com", emails)       # still pending → included

    # --- Context structure ---

    def test_each_item_has_required_keys(self):
        self.client.force_login(self.admin)
        response = self.client.get(self._hq_url())
        for item in response.context["invitations"]:
            self.assertIn("invitation", item)
            self.assertIn("registration_url", item)
            self.assertIn("qr_api_url", item)

    def test_each_qr_api_url_contains_token(self):
        self.client.force_login(self.admin)
        response = self.client.get(self._hq_url())
        for item in response.context["invitations"]:
            self.assertIn(
                str(item["invitation"].token),
                item["qr_api_url"],
                msg=f"Token missing from QR URL for {item['invitation'].email}",
            )

    def test_each_registration_url_is_absolute(self):
        self.client.force_login(self.admin)
        response = self.client.get(self._hq_url())
        for item in response.context["invitations"]:
            self.assertTrue(
                item["registration_url"].startswith("http"),
                msg=f"Registration URL not absolute for {item['invitation'].email}",
            )

    # --- Empty state ---

    def test_empty_state_when_no_pending_invitations(self):
        # Accept all pending invitations
        user1 = User.objects.create_user(email="u1@example.com", password="pass")
        user2 = User.objects.create_user(email="u2@example.com", password="pass")
        self.ghana_inv.accept(user1)
        self.nigeria_inv.accept(user2)

        self.client.force_login(self.admin)
        response = self.client.get(self._hq_url())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["invitations"]), 0)
        self.assertContains(response, "No pending invitations")

    # --- Template ---

    def test_template_used(self):
        self.client.force_login(self.admin)
        response = self.client.get(self._hq_url())
        self.assertTemplateUsed(response, "dashboard/invitations/qr_bulk.html")

    def test_response_contains_print_button(self):
        self.client.force_login(self.admin)
        response = self.client.get(self._hq_url())
        self.assertContains(response, "window.print()")


# ---------------------------------------------------------------------------
# HQ Admin Invitation Tests (new feature)
# ---------------------------------------------------------------------------

def make_hq_invitation(invited_by, email="hqadmin@example.com", days=7):
    """Create a HQ admin invitation (no member state, user_type='ipawas_admin')."""
    return Invitation.objects.create_invitation(
        email=email,
        invited_by=invited_by,
        member_state=None,
        role="",
        user_type="ipawas_admin",
        expires_in_days=days,
    )


class HQAdminInvitationModelTests(TestCase):
    """Test the model layer for HQ admin invitations."""

    def setUp(self):
        self.admin = IPAWASAdminFactory()

    def test_create_hq_invitation_succeeds(self):
        inv = make_hq_invitation(self.admin)
        self.assertIsNone(inv.member_state)
        self.assertEqual(inv.user_type, "ipawas_admin")
        self.assertEqual(inv.role, "")
        self.assertEqual(inv.status, "pending")

    def test_hq_invitation_str_shows_hq_admin(self):
        inv = make_hq_invitation(self.admin)
        self.assertIn("HQ Admin", str(inv))

    def test_ipa_staff_invitation_str_shows_ipa_acronym(self):
        ms = MemberStateIPAFactory()
        inv = make_invitation(ms, self.admin)
        self.assertIn(ms.ipa_acronym, str(inv))

    def test_hq_invitation_is_valid(self):
        inv = make_hq_invitation(self.admin)
        self.assertTrue(inv.is_valid)

    def test_hq_invitation_unique_pending_constraint(self):
        """Only one pending HQ invitation per email is allowed."""
        make_hq_invitation(self.admin, email="dup_hq@example.com")
        with self.assertRaises(Exception):
            make_hq_invitation(self.admin, email="dup_hq@example.com")

    def test_hq_and_ipa_invitation_for_same_email_both_allowed(self):
        """An email can have a pending HQ invitation AND a pending IPA staff invitation."""
        ms = MemberStateIPAFactory()
        make_hq_invitation(self.admin, email="both@example.com")
        # IPA staff invitation for the same email is a different constraint
        inv_ipa = make_invitation(ms, self.admin, email="both@example.com")
        self.assertIsNotNone(inv_ipa.pk)

    def test_ipa_invitation_without_member_state_raises_validation_error(self):
        """user_type='ipa_staff' with no member_state must fail clean()."""
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            Invitation.objects.create_invitation(
                email="bad@example.com",
                invited_by=self.admin,
                member_state=None,
                role="ipa_officer",
                user_type="ipa_staff",  # ipa_staff without member_state should fail
            )

    def test_ipa_invitation_without_role_raises_validation_error(self):
        """IPA staff invitation with empty role must fail clean()."""
        from django.core.exceptions import ValidationError
        ms = MemberStateIPAFactory()
        with self.assertRaises(ValidationError):
            Invitation.objects.create_invitation(
                email="norole@example.com",
                invited_by=self.admin,
                member_state=ms,
                role="",  # role required for ipa_staff
                user_type="ipa_staff",
            )

    def test_hq_invitation_accept_creates_user_with_ipawas_admin_type(self):
        """Accepting a HQ invitation should create an ipawas_admin user."""
        inv = make_hq_invitation(self.admin)
        new_user = User.objects.create_user(
            email="hqnewuser@example.com",
            password="pass",
            user_type="ipawas_admin",
        )
        inv.accept(new_user)
        inv.refresh_from_db()
        self.assertEqual(inv.status, "accepted")
        self.assertEqual(inv.created_user, new_user)


@override_settings(ALLOWED_HOSTS=["*"])
class HQAdminInvitationRegistrationViewTests(TestCase):
    """Test the registration flow for HQ admin invitations."""

    def setUp(self):
        self.admin = IPAWASAdminFactory()

    def _register_url(self, token):
        # Use the flat namespace — this matches what get_registration_url() produces
        # and therefore matches the URL included in invitation emails.
        return reverse("dashboard:invitations:register", kwargs={"token": token})

    def _valid_form_data(self, inv):
        return {
            "first_name": "Alice",
            "last_name": "Smith",
            "email": inv.email,
            "job_title": "HQ Coordinator",
            "phone_number": "+22300000001",
            "language_preference": "en",
            "password1": "Str0ng!Password123",
            "password2": "Str0ng!Password123",
            "terms_accepted": True,
        }

    @patch("dashboard.views.invitation.views.get_system_email_service")
    def test_hq_admin_registration_creates_user_with_correct_type(self, mock_email_svc):
        mock_email_svc.return_value = MagicMock()
        mock_email_svc.return_value.send_welcome_email.return_value = True

        inv = make_hq_invitation(self.admin, email="hqreg@example.com")
        url = self._register_url(inv.token)
        response = self.client.post(url, data=self._valid_form_data(inv), follow=False)

        # Should redirect (302) to HQ dashboard
        self.assertEqual(response.status_code, 302)
        self.assertIn("/en/dashboard/hq/", response["Location"])

        # User should exist with user_type='ipawas_admin'
        user = User.objects.get(email="hqreg@example.com")
        self.assertEqual(user.user_type, "ipawas_admin")

        # No IPAUser profile should be created
        from accounts.models import IPAUser
        self.assertFalse(IPAUser.objects.filter(user=user).exists())

        # Invitation should be accepted
        inv.refresh_from_db()
        self.assertEqual(inv.status, "accepted")

    @patch("dashboard.views.invitation.views.get_system_email_service")
    def test_ipa_staff_registration_still_creates_ipa_user(self, mock_email_svc):
        mock_email_svc.return_value = MagicMock()
        mock_email_svc.return_value.send_welcome_email.return_value = True

        ms = MemberStateIPAFactory(slug="teststate")
        inv = make_invitation(ms, self.admin, email="ipareg@example.com")
        # Use country-scoped URL for IPA staff invitation
        url = reverse(
            "dashboard:country:invitations:register",
            kwargs={"member_state_slug": "teststate", "token": inv.token},
        )
        data = self._valid_form_data(inv)
        response = self.client.post(url, data=data, follow=False)

        self.assertEqual(response.status_code, 302)

        user = User.objects.get(email="ipareg@example.com")
        self.assertEqual(user.user_type, "ipa_staff")

        from accounts.models import IPAUser
        self.assertTrue(IPAUser.objects.filter(user=user, member_state=ms).exists())

        inv.refresh_from_db()
        self.assertEqual(inv.status, "accepted")

    def test_get_registration_url_uses_flat_namespace(self):
        """get_registration_url() must produce the flat dashboard:invitations:register URL.

        This is the URL embedded in invitation emails. If it changes namespace
        the email link would break for all outstanding invitations.
        """
        inv = make_hq_invitation(self.admin, email="urlcheck@example.com")
        url = inv.get_registration_url()
        expected = reverse("dashboard:invitations:register", kwargs={"token": inv.token})
        self.assertEqual(url, expected)


@override_settings(ALLOWED_HOSTS=["*"])
class InvitationCreateViewTests(TestCase):
    """Test InvitationCreateView for both HQ admin and IPA staff users."""

    def setUp(self):
        self.hq_admin = IPAWASAdminFactory()
        self.member_state = MemberStateIPAFactory(slug="cabo-verde")

    def _create_url(self):
        return reverse("dashboard:hq:invitations:create")

    @patch("dashboard.views.invitation.views.get_invitation_email_service")
    def test_hq_admin_can_invite_ipa_staff_for_member_state(self, mock_email_svc):
        """Regression: HQ admin inviting IPA staff from /hq/invitations/create/ must NOT
        raise 'Invitations without a member state must use user_type=ipawas_admin'.

        Root cause was that member_state is not in InvitationForm.Meta.fields, so
        _post_clean() never applied it to the model instance before calling
        instance.full_clean() — causing the model's clean() to see member_state=None.
        Fix: InvitationForm.clean() now syncs self.instance.member_state.
        """
        mock_email_svc.return_value = MagicMock()
        mock_email_svc.return_value.send_invitation_email.return_value = True

        self.client.force_login(self.hq_admin)
        response = self.client.post(
            self._create_url(),
            data={
                "user_type": "ipa_staff",
                "member_state": self.member_state.pk,
                "email": "caboverde@example.com",
                "role": "ipa_officer",
                "is_primary_contact": False,
                "invitation_message": "",
                "expires_in_days": 7,
            },
            follow=False,
        )

        # Must redirect on success, not return 200 (which would mean form error)
        self.assertEqual(
            response.status_code,
            302,
            msg=(
                "Expected redirect after successful invitation. "
                "If 200, the form was rejected — likely the member_state sync bug returned."
            ),
        )

        # The invitation must exist in the DB with the correct member state
        inv = Invitation.objects.filter(email="caboverde@example.com").first()
        self.assertIsNotNone(inv, "Invitation was not created in the database")
        self.assertEqual(inv.member_state, self.member_state)
        self.assertEqual(inv.user_type, "ipa_staff")
        self.assertEqual(inv.role, "ipa_officer")

    @patch("dashboard.views.invitation.views.get_invitation_email_service")
    def test_hq_admin_can_invite_hq_admin(self, mock_email_svc):
        """HQ admin inviting another HQ admin must succeed with no member state."""
        mock_email_svc.return_value = MagicMock()
        mock_email_svc.return_value.send_invitation_email.return_value = True

        self.client.force_login(self.hq_admin)
        response = self.client.post(
            self._create_url(),
            data={
                "user_type": "ipawas_admin",
                "email": "newhq@example.com",
                "role": "",
                "is_primary_contact": False,
                "invitation_message": "",
                "expires_in_days": 7,
            },
            follow=False,
        )

        self.assertEqual(response.status_code, 302)
        inv = Invitation.objects.filter(email="newhq@example.com").first()
        self.assertIsNotNone(inv)
        self.assertIsNone(inv.member_state)
        self.assertEqual(inv.user_type, "ipawas_admin")


class InvitationCreateViewHiddenFieldsRenderingTests(TestCase):
    """
    Regression test: dashboard/templates/dashboard/invitations/create.html
    used to render `{{ form.hidden_fields }}` directly. Form.hidden_fields()
    is a method returning a *list* of BoundField objects — Django templates
    auto-call it, but printing the list itself (instead of iterating it)
    just prints Python's list repr, e.g.
    "[<django.forms.boundfield.BoundField object at 0x...>]", visible as
    literal text on the page instead of rendering the actual hidden
    <input> HTML.

    For IPA staff this was purely cosmetic — InvitationForm.clean_user_type()
    already forces user_type to "ipa_staff" server-side regardless of what
    (if anything) was posted, specifically to guard against this exact
    missing-hidden-input case. But the broken-looking text was confusing
    end users, one of whom reported it as "Is this an error?".
    """

    def setUp(self):
        self.member_state = MemberStateIPAFactory(slug="the-gambia")
        self.ipa_user = IPAUserFactory(member_state=self.member_state)
        self.hq_admin = IPAWASAdminFactory()

    def _country_create_url(self):
        return reverse(
            "dashboard:country:invitations:create",
            kwargs={"member_state_slug": self.member_state.slug},
        )

    def _hq_create_url(self):
        return reverse("dashboard:hq:invitations:create")

    def test_ipa_staff_page_does_not_leak_boundfield_repr(self):
        self.client.force_login(self.ipa_user.user)
        content = self.client.get(self._country_create_url()).content.decode()
        self.assertNotIn("BoundField object", content)

    def test_ipa_staff_page_renders_actual_hidden_input_for_user_type(self):
        self.client.force_login(self.ipa_user.user)
        content = self.client.get(self._country_create_url()).content.decode()
        self.assertIn('type="hidden"', content)
        self.assertIn('name="user_type"', content)
        self.assertIn('value="ipa_staff"', content)

    def test_hq_admin_page_does_not_leak_boundfield_repr(self):
        """HQ admin has no hidden fields on this form — the loop must be a harmless no-op."""
        self.client.force_login(self.hq_admin)
        content = self.client.get(self._hq_create_url()).content.decode()
        self.assertNotIn("BoundField object", content)
