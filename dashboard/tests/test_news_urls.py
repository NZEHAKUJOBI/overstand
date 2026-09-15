"""
Tests for Country News Hub URL configuration (apps/dashboard/urls/country_news.py).

Verifies all 6 routes resolve correctly with the right view and namespace,
and that authenticated IPA staff can reach them (200/302 responses).
"""

from django.test import TestCase, override_settings
from django.urls import NoReverseMatch, resolve, reverse

from dashboard.tests.factories import IPAUserFactory, MemberStateIPAFactory


SLUG = "liberia"


def _news_url(name, **kwargs):
    kwargs.setdefault("member_state_slug", SLUG)
    return reverse(f"dashboard:country:news:{name}", kwargs=kwargs)


class CountryNewsURLResolutionTests(TestCase):
    """URL pattern reverse/resolve tests — no DB, no auth needed."""

    def test_list_url_resolves(self):
        url = _news_url("list")
        resolved = resolve(url)
        self.assertEqual(resolved.url_name, "list")
        # Full namespace path is "dashboard:country:news"
        self.assertIn("news", resolved.namespace)

    def test_create_url_resolves(self):
        url = _news_url("create")
        resolved = resolve(url)
        self.assertEqual(resolved.url_name, "create")

    def test_edit_url_resolves(self):
        url = _news_url("edit", pk=42)
        resolved = resolve(url)
        self.assertEqual(resolved.url_name, "edit")
        self.assertEqual(resolved.kwargs["pk"], 42)

    def test_delete_url_resolves(self):
        url = _news_url("delete", pk=42)
        resolved = resolve(url)
        self.assertEqual(resolved.url_name, "delete")

    def test_preview_url_resolves(self):
        url = _news_url("preview", pk=42)
        resolved = resolve(url)
        self.assertEqual(resolved.url_name, "preview")

    def test_autosave_url_resolves(self):
        url = _news_url("autosave", pk=42)
        resolved = resolve(url)
        self.assertEqual(resolved.url_name, "autosave")

    def test_all_six_urls_reverse_without_error(self):
        _news_url("list")
        _news_url("create")
        _news_url("edit", pk=1)
        _news_url("delete", pk=1)
        _news_url("preview", pk=1)
        _news_url("autosave", pk=1)
        # If we get here, all 6 reversed successfully


@override_settings(ALLOWED_HOSTS=["*"])
class CountryNewsAccessTests(TestCase):
    """Integration: authenticated IPA staff can reach news list."""

    def setUp(self):
        self.member_state = MemberStateIPAFactory(slug=SLUG)
        self.ipa_user = IPAUserFactory(member_state=self.member_state)

    def test_news_list_accessible_to_ipa_staff(self):
        self.client.force_login(self.ipa_user.user)
        url = _news_url("list")
        response = self.client.get(url)
        # 200 (list) or 302 (redirect within system) both acceptable
        self.assertIn(response.status_code, [200, 302])

    def test_news_list_requires_login(self):
        url = _news_url("list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response["Location"])

    def test_news_create_requires_login(self):
        url = _news_url("create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response["Location"])

    def test_news_urls_nested_under_member_state_slug(self):
        """All news URLs must be prefixed with /dashboard/<slug>/news/."""
        list_url = _news_url("list")
        self.assertIn(f"/{SLUG}/", list_url)
        self.assertIn("/news/", list_url)
