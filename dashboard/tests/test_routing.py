"""
Tests for DashboardRoutingView (apps/dashboard/views/routing.py).

Covers all routing scenarios:
- Unauthenticated → login redirect
- IPAWAS admin → HQ overview
- IPA staff with member state → country overview
- IPA staff without member state → profile page
- Public/investor user → home page
"""

from django.test import TestCase, override_settings
from django.urls import reverse

from dashboard.tests.factories import IPAUserFactory, IPAWASAdminFactory, MemberStateIPAFactory, UserFactory


@override_settings(ALLOWED_HOSTS=["*"])
class DashboardRoutingViewTests(TestCase):

    def setUp(self):
        self.url = reverse("dashboard:index")

    # --- Unauthenticated ---

    def test_unauthenticated_redirects_to_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response["Location"])

    # --- IPAWAS Admin ---

    def test_hq_admin_redirects_to_hq_overview(self):
        admin = IPAWASAdminFactory()
        self.client.force_login(admin)
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse("dashboard:hq:overview"), fetch_redirect_response=False)

    # --- IPA Staff ---

    def test_ipa_staff_redirects_to_country_overview(self):
        member_state = MemberStateIPAFactory(slug="ghana")
        ipa_user = IPAUserFactory(member_state=member_state)
        self.client.force_login(ipa_user.user)

        response = self.client.get(self.url)

        expected_url = reverse("dashboard:country:overview", kwargs={"member_state_slug": "ghana"})
        self.assertRedirects(response, expected_url, fetch_redirect_response=False)

    def test_ipa_staff_without_member_state_redirects_to_profile(self):
        """IPA staff whose ipa_profile has no member_state → accounts:profile fallback."""
        staff_user = IPAWASAdminFactory.__class__  # plain staff user, no IPAUser profile
        from accounts.models import User as AuthUser
        user = AuthUser.objects.create_user(
            email="broken@example.com",
            password="pass",
            user_type="ipa_staff",
        )
        self.client.force_login(user)

        response = self.client.get(self.url)

        self.assertRedirects(response, reverse("accounts:profile"), fetch_redirect_response=False)

    # --- Public/Investor ---

    def test_public_user_redirects_to_home(self):
        user = UserFactory(user_type="public")
        self.client.force_login(user)
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse("home"), fetch_redirect_response=False)

    # --- Follow-through (actual 200) ---

    def test_hq_admin_chain_resolves_to_200(self):
        admin = IPAWASAdminFactory()
        self.client.force_login(admin)
        response = self.client.get(self.url, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_ipa_staff_chain_resolves_to_200(self):
        member_state = MemberStateIPAFactory(slug="nigeria")
        ipa_user = IPAUserFactory(member_state=member_state)
        self.client.force_login(ipa_user.user)
        response = self.client.get(self.url, follow=True)
        self.assertEqual(response.status_code, 200)
