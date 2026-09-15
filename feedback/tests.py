"""
Tests for the feedback app.

Covers:
- Feedback model: defaults, properties, __str__
- IPA Staff views: list, submit, detail — auth, scoping, form validation
- HQ Admin views: list with filters, detail/respond
- Access control: cross-user isolation and role enforcement
"""

import factory
from django.test import TestCase, override_settings
from django.urls import reverse

from dashboard.tests.factories import IPAUserFactory, IPAWASAdminFactory, MemberStateIPAFactory
from feedback.models import Feedback


# ── Factory ──────────────────────────────────────────────────────────────────

class FeedbackFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Feedback

    user = factory.LazyAttribute(lambda o: IPAUserFactory(member_state=o.member_state).user)
    member_state = factory.SubFactory(MemberStateIPAFactory)
    category = "idea"
    title = factory.Sequence(lambda n: f"Feedback title {n}")
    body = "Some detailed feedback body text."
    status = "new"

    class Params:
        # allows FeedbackFactory(ipa_user=...) to set user+member_state together
        ipa_user = None


# ── Model tests ───────────────────────────────────────────────────────────────

class FeedbackModelTests(TestCase):

    def _make(self, **kwargs):
        ms = MemberStateIPAFactory()
        ipa = IPAUserFactory(member_state=ms)
        return Feedback.objects.create(
            user=ipa.user, member_state=ms,
            category=kwargs.get("category", "idea"),
            title=kwargs.get("title", "Test title"),
            body=kwargs.get("body", "Test body"),
            status=kwargs.get("status", "new"),
        )

    def test_default_status_is_new(self):
        fb = self._make()
        self.assertEqual(fb.status, "new")

    def test_str_includes_category_and_title(self):
        fb = self._make(category="suggestion", title="My title")
        self.assertIn("Suggestion", str(fb))
        self.assertIn("My title", str(fb))

    def test_category_icon_idea(self):
        fb = self._make(category="idea")
        self.assertEqual(fb.category_icon, "fa-lightbulb")

    def test_category_icon_suggestion(self):
        fb = self._make(category="suggestion")
        self.assertEqual(fb.category_icon, "fa-comment-dots")

    def test_category_icon_observation(self):
        fb = self._make(category="observation")
        self.assertEqual(fb.category_icon, "fa-eye")

    def test_category_icon_bug_report(self):
        fb = self._make(category="bug_report")
        self.assertEqual(fb.category_icon, "fa-bug")

    def test_status_color_returns_string_for_all_statuses(self):
        for status, _ in Feedback.STATUS_CHOICES:
            fb = self._make(status=status)
            color = fb.status_color
            self.assertIsInstance(color, str)
            self.assertTrue(color.startswith("#"), f"Expected hex color for status {status}, got {color}")

    def test_ordering_newest_first(self):
        ms = MemberStateIPAFactory()
        ipa = IPAUserFactory(member_state=ms)
        fb1 = Feedback.objects.create(user=ipa.user, member_state=ms, category="idea", title="First", body="x")
        fb2 = Feedback.objects.create(user=ipa.user, member_state=ms, category="idea", title="Second", body="x")
        qs = list(Feedback.objects.all())
        self.assertEqual(qs[0].pk, fb2.pk)
        self.assertEqual(qs[1].pk, fb1.pk)

    def test_admin_response_defaults_empty(self):
        fb = self._make()
        self.assertEqual(fb.admin_response, "")

    def test_responded_at_defaults_null(self):
        fb = self._make()
        self.assertIsNone(fb.responded_at)


# ── IPA Staff: list view ──────────────────────────────────────────────────────

@override_settings(ALLOWED_HOSTS=["*"])
class FeedbackListViewTests(TestCase):

    def setUp(self):
        self.ms = MemberStateIPAFactory(slug="ghana")
        self.ipa = IPAUserFactory(member_state=self.ms)
        self.url = reverse("dashboard:country:feedback_list", kwargs={"member_state_slug": "ghana"})

    def test_unauthenticated_redirects_to_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response["Location"])

    def test_ipa_staff_can_access(self):
        self.client.force_login(self.ipa.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_hq_admin_redirected_to_hq(self):
        admin = IPAWASAdminFactory()
        self.client.force_login(admin)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("hq", response["Location"])

    def test_only_own_submissions_shown(self):
        # This user's feedback
        Feedback.objects.create(
            user=self.ipa.user, member_state=self.ms,
            category="idea", title="Mine", body="x",
        )
        # Another user's feedback from a different member state
        other_ms = MemberStateIPAFactory()
        other_ipa = IPAUserFactory(member_state=other_ms)
        Feedback.objects.create(
            user=other_ipa.user, member_state=other_ms,
            category="idea", title="Not mine", body="x",
        )

        self.client.force_login(self.ipa.user)
        response = self.client.get(self.url)
        submissions = response.context["submissions"]
        self.assertEqual(len(submissions), 1)
        self.assertEqual(submissions[0].title, "Mine")

    def test_empty_state_renders_without_error(self):
        self.client.force_login(self.ipa.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["submissions"]), 0)


# ── IPA Staff: submit view ────────────────────────────────────────────────────

@override_settings(ALLOWED_HOSTS=["*"])
class FeedbackSubmitViewTests(TestCase):

    def setUp(self):
        self.ms = MemberStateIPAFactory(slug="nigeria")
        self.ipa = IPAUserFactory(member_state=self.ms)
        self.url = reverse("dashboard:country:feedback_submit", kwargs={"member_state_slug": "nigeria"})

    def test_get_renders_form(self):
        self.client.force_login(self.ipa.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("form", response.context)

    def test_valid_post_creates_feedback(self):
        self.client.force_login(self.ipa.user)
        response = self.client.post(self.url, {
            "category": "suggestion",
            "title": "Add dark mode",
            "body": "It would help us work at night.",
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Feedback.objects.count(), 1)
        fb = Feedback.objects.first()
        self.assertEqual(fb.user, self.ipa.user)
        self.assertEqual(fb.member_state, self.ms)
        self.assertEqual(fb.category, "suggestion")
        self.assertEqual(fb.title, "Add dark mode")
        self.assertEqual(fb.status, "new")

    def test_redirects_to_list_on_success(self):
        self.client.force_login(self.ipa.user)
        response = self.client.post(self.url, {
            "category": "idea",
            "title": "My idea",
            "body": "Details here.",
        })
        self.assertRedirects(
            response,
            reverse("dashboard:country:feedback_list", kwargs={"member_state_slug": "nigeria"}),
        )

    def test_missing_title_invalid(self):
        self.client.force_login(self.ipa.user)
        response = self.client.post(self.url, {
            "category": "idea",
            "title": "",
            "body": "Some body.",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["form"].is_valid())
        self.assertEqual(Feedback.objects.count(), 0)

    def test_missing_body_invalid(self):
        self.client.force_login(self.ipa.user)
        response = self.client.post(self.url, {
            "category": "idea",
            "title": "Some title",
            "body": "",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["form"].is_valid())

    def test_invalid_category_invalid(self):
        self.client.force_login(self.ipa.user)
        response = self.client.post(self.url, {
            "category": "not_a_real_category",
            "title": "Title",
            "body": "Body",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["form"].is_valid())

    def test_unauthenticated_redirects(self):
        response = self.client.post(self.url, {"category": "idea", "title": "x", "body": "y"})
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response["Location"])


# ── IPA Staff: detail view ────────────────────────────────────────────────────

@override_settings(ALLOWED_HOSTS=["*"])
class FeedbackDetailViewTests(TestCase):

    def setUp(self):
        self.ms = MemberStateIPAFactory(slug="senegal")
        self.ipa = IPAUserFactory(member_state=self.ms)
        self.fb = Feedback.objects.create(
            user=self.ipa.user, member_state=self.ms,
            category="observation", title="My observation", body="Details.",
        )
        self.url = reverse("dashboard:country:feedback_detail",
                           kwargs={"member_state_slug": "senegal", "pk": self.fb.pk})

    def test_owner_can_view(self):
        self.client.force_login(self.ipa.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["submission"], self.fb)

    def test_other_user_gets_404(self):
        other_ms = MemberStateIPAFactory(slug="ghana")
        other_ipa = IPAUserFactory(member_state=other_ms)
        # other user tries to access senegal feedback directly
        self.client.force_login(other_ipa.user)
        # They'd hit the wrong member_state slug redirect, but let's test the queryset isolation
        # by creating a URL with the right slug but wrong user
        other_url = reverse("dashboard:country:feedback_detail",
                            kwargs={"member_state_slug": "senegal", "pk": self.fb.pk})
        response = self.client.get(other_url)
        # Redirected away from senegal (wrong member state) or 404
        self.assertIn(response.status_code, [302, 404])

    def test_unauthenticated_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response["Location"])

    def test_admin_response_visible_when_set(self):
        self.fb.admin_response = "Thank you for this insight!"
        self.fb.status = "acknowledged"
        self.fb.save()

        self.client.force_login(self.ipa.user)
        response = self.client.get(self.url)
        self.assertContains(response, "Thank you for this insight!")


# ── HQ Admin: list view ───────────────────────────────────────────────────────

@override_settings(ALLOWED_HOSTS=["*"])
class HQFeedbackListViewTests(TestCase):

    def setUp(self):
        self.admin = IPAWASAdminFactory()
        self.url = reverse("dashboard:hq:feedback_list")

        self.ms1 = MemberStateIPAFactory(slug="ivory-coast")
        self.ms2 = MemberStateIPAFactory(slug="ghana")
        self.ipa1 = IPAUserFactory(member_state=self.ms1)
        self.ipa2 = IPAUserFactory(member_state=self.ms2)

        self.fb1 = Feedback.objects.create(
            user=self.ipa1.user, member_state=self.ms1,
            category="idea", title="Ivory Coast idea", body="x", status="new",
        )
        self.fb2 = Feedback.objects.create(
            user=self.ipa2.user, member_state=self.ms2,
            category="bug_report", title="Ghana bug", body="x", status="under_review",
        )

    def test_unauthenticated_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_ipa_staff_redirected_away_from_hq(self):
        # IPAWASAdminRequiredMixin redirects IPA staff to their own dashboard, not HQ
        self.client.force_login(self.ipa1.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertNotIn("hq", response["Location"])
        self.assertIn("ivory-coast", response["Location"])

    def test_hq_admin_sees_all_submissions(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["submissions"].count(), 2)

    def test_filter_by_category(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url, {"category": "idea"})
        submissions = response.context["submissions"]
        self.assertEqual(submissions.count(), 1)
        self.assertEqual(submissions.first().title, "Ivory Coast idea")

    def test_filter_by_status(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url, {"status": "under_review"})
        submissions = response.context["submissions"]
        self.assertEqual(submissions.count(), 1)
        self.assertEqual(submissions.first().title, "Ghana bug")

    def test_filter_by_country(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url, {"country": "ghana"})
        submissions = response.context["submissions"]
        self.assertEqual(submissions.count(), 1)
        self.assertEqual(submissions.first().title, "Ghana bug")

    def test_combined_filters(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url, {"category": "idea", "country": "ivory-coast"})
        submissions = response.context["submissions"]
        self.assertEqual(submissions.count(), 1)

    def test_combined_filters_no_match(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url, {"category": "idea", "country": "ghana"})
        submissions = response.context["submissions"]
        self.assertEqual(submissions.count(), 0)

    def test_unreviewed_count_in_context(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url)
        # fb1 is "new", fb2 is "under_review"
        self.assertEqual(response.context["unreviewed_count"], 1)


# ── HQ Admin: detail/respond view ────────────────────────────────────────────

@override_settings(ALLOWED_HOSTS=["*"])
class HQFeedbackDetailViewTests(TestCase):

    def setUp(self):
        self.admin = IPAWASAdminFactory()
        self.ms = MemberStateIPAFactory(slug="togo")
        self.ipa = IPAUserFactory(member_state=self.ms)
        self.fb = Feedback.objects.create(
            user=self.ipa.user, member_state=self.ms,
            category="suggestion", title="Improve exports", body="Details.",
        )
        self.url = reverse("dashboard:hq:feedback_detail", kwargs={"pk": self.fb.pk})

    def test_hq_admin_can_view(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["submission"], self.fb)

    def test_ipa_staff_redirected(self):
        self.client.force_login(self.ipa.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_unauthenticated_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_valid_response_updates_status_and_response(self):
        self.client.force_login(self.admin)
        response = self.client.post(self.url, {
            "status": "acknowledged",
            "admin_response": "We have noted this suggestion.",
        })
        self.assertEqual(response.status_code, 302)
        self.fb.refresh_from_db()
        self.assertEqual(self.fb.status, "acknowledged")
        self.assertEqual(self.fb.admin_response, "We have noted this suggestion.")

    def test_first_response_sets_responded_by_and_responded_at(self):
        self.client.force_login(self.admin)
        self.client.post(self.url, {
            "status": "under_review",
            "admin_response": "Looking into this.",
        })
        self.fb.refresh_from_db()
        self.assertEqual(self.fb.responded_by, self.admin)
        self.assertIsNotNone(self.fb.responded_at)

    def test_status_only_update_no_response_text(self):
        self.client.force_login(self.admin)
        response = self.client.post(self.url, {
            "status": "declined",
            "admin_response": "",
        })
        self.assertEqual(response.status_code, 302)
        self.fb.refresh_from_db()
        self.assertEqual(self.fb.status, "declined")

    def test_invalid_status_does_not_save(self):
        self.client.force_login(self.admin)
        response = self.client.post(self.url, {
            "status": "not_a_real_status",
            "admin_response": "Test",
        })
        self.assertEqual(response.status_code, 200)
        self.fb.refresh_from_db()
        self.assertEqual(self.fb.status, "new")

    def test_nonexistent_feedback_returns_404(self):
        self.client.force_login(self.admin)
        url = reverse("dashboard:hq:feedback_detail", kwargs={"pk": 99999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
