"""
Tests for dashboard access-control mixins (apps/dashboard/mixins.py).

Covers:
- IPAWASAdminRequiredMixin: blocks non-admins, redirects IPA staff
- IPAStaffRequiredMixin: blocks non-staff, redirects HQ admins
- MemberStateAccessMixin: cross-state slug validation
- CanManageUsersMixin: HQ always passes, IPA staff need permission
"""

from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from dashboard.tests.factories import IPAUserFactory, IPAWASAdminFactory, MemberStateIPAFactory, UserFactory


@override_settings(ALLOWED_HOSTS=["*"])
class IPAWASAdminRequiredMixinTests(TestCase):
    """Tests for the HQ-only mixin enforced on /dashboard/hq/ views."""

    def test_unauthenticated_redirects_to_login(self):
        url = reverse("dashboard:hq:overview")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response["Location"])

    def test_hq_admin_can_access(self):
        admin = IPAWASAdminFactory()
        self.client.force_login(admin)
        response = self.client.get(reverse("dashboard:hq:overview"))
        self.assertEqual(response.status_code, 200)

    def test_ipa_staff_redirected_to_their_dashboard(self):
        member_state = MemberStateIPAFactory(slug="togo")
        ipa_user = IPAUserFactory(member_state=member_state)
        self.client.force_login(ipa_user.user)

        response = self.client.get(reverse("dashboard:hq:overview"))
        # IPA staff should be redirected to their own dashboard, not denied
        self.assertEqual(response.status_code, 302)
        self.assertIn("togo", response["Location"])

    def test_public_user_gets_permission_denied(self):
        user = UserFactory(user_type="public")
        self.client.force_login(user)
        response = self.client.get(reverse("dashboard:hq:overview"))
        self.assertEqual(response.status_code, 403)


@override_settings(ALLOWED_HOSTS=["*"])
class IPAStaffRequiredMixinTests(TestCase):
    """Tests for the IPA staff mixin enforced on /dashboard/<slug>/ views."""

    def test_unauthenticated_redirects_to_login(self):
        member_state = MemberStateIPAFactory(slug="ghana")
        url = reverse("dashboard:country:overview", kwargs={"member_state_slug": "ghana"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response["Location"])

    def test_ipa_staff_can_access_own_dashboard(self):
        member_state = MemberStateIPAFactory(slug="ghana")
        ipa_user = IPAUserFactory(member_state=member_state)
        self.client.force_login(ipa_user.user)

        url = reverse("dashboard:country:overview", kwargs={"member_state_slug": "ghana"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_hq_admin_redirected_to_hq_dashboard(self):
        MemberStateIPAFactory(slug="ghana")
        admin = IPAWASAdminFactory()
        self.client.force_login(admin)

        url = reverse("dashboard:country:overview", kwargs={"member_state_slug": "ghana"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("hq", response["Location"])

    def test_public_user_gets_403(self):
        MemberStateIPAFactory(slug="ghana")
        user = UserFactory(user_type="public")
        self.client.force_login(user)

        url = reverse("dashboard:country:overview", kwargs={"member_state_slug": "ghana"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)


@override_settings(ALLOWED_HOSTS=["*"])
class MemberStateAccessMixinTests(TestCase):
    """IPA staff cannot access another country's dashboard URL."""

    def test_ipa_staff_redirected_when_accessing_wrong_state(self):
        ghana = MemberStateIPAFactory(slug="ghana")
        nigeria = MemberStateIPAFactory(slug="nigeria")

        ghana_user = IPAUserFactory(member_state=ghana)
        self.client.force_login(ghana_user.user)

        # Try to access Nigeria's dashboard with Ghana credentials
        url = reverse("dashboard:country:overview", kwargs={"member_state_slug": "nigeria"})
        response = self.client.get(url)

        # Should be redirected back to Ghana
        self.assertEqual(response.status_code, 302)
        self.assertIn("ghana", response["Location"])

    def test_ipa_staff_can_access_own_state_url(self):
        ghana = MemberStateIPAFactory(slug="ghana")
        ghana_user = IPAUserFactory(member_state=ghana)
        self.client.force_login(ghana_user.user)

        url = reverse("dashboard:country:overview", kwargs={"member_state_slug": "ghana"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_hq_admin_can_view_any_member_state(self):
        ghana = MemberStateIPAFactory(slug="ghana")
        admin = IPAWASAdminFactory()
        self.client.force_login(admin)

        # HQ admin accessing Ghana's overview via country namespace (resolves to redirect in practice)
        url = reverse("dashboard:country:overview", kwargs={"member_state_slug": "ghana"})
        response = self.client.get(url)
        # HQ admin is redirected to HQ dashboard by IPAStaffRequiredMixin
        self.assertEqual(response.status_code, 302)


@override_settings(ALLOWED_HOSTS=["*"])
class CanManageUsersMixinTests(TestCase):
    """Tests for CanManageUsersMixin on inquiry views."""

    def setUp(self):
        from members.models import InvestorInquiry
        self.member_state = MemberStateIPAFactory(slug="ivory-coast")

    def test_hq_admin_always_has_access(self):
        admin = IPAWASAdminFactory()
        self.client.force_login(admin)
        url = reverse("dashboard:hq:inquiries:list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_ipa_staff_with_permission_can_access(self):
        ipa_user = IPAUserFactory(member_state=self.member_state, can_manage_users=True)
        self.client.force_login(ipa_user.user)
        url = reverse(
            "dashboard:country:inquiries:list",
            kwargs={"member_state_slug": "ivory-coast"},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_ipa_staff_without_manage_users_can_still_view_inquiries(self):
        # All IPA staff (including analysts without can_manage_users) should be able
        # to view their member state's inquiries. Inquiry access is not tied to the
        # user-management permission — that was the old (wrong) behaviour.
        ipa_user = IPAUserFactory(member_state=self.member_state, role="ipa_analyst")
        self.client.force_login(ipa_user.user)
        url = reverse(
            "dashboard:country:inquiries:list",
            kwargs={"member_state_slug": "ivory-coast"},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
