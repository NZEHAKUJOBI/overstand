"""
Tests for the Member State Sectors feature.

Covers:
- SectorAddForm: validation, clean_sector_name strips whitespace
- SectorEditForm: only editable fields, sector name excluded
- SectorListView: scoped to member state, access control
- SectorAddView: GET renders form + datalist; POST creates GlobalSector +
  MemberStateSector; duplicate rejected; new sector name auto-creates global entry
- SectorEditView: GET pre-populates; POST updates description/potential/priority;
  cannot edit another state's sector (IDOR guard)
- SectorDeleteView: GET renders confirmation; POST deletes; cannot delete another
  state's sector (IDOR guard); template has correct sector name
- IncentiveForm applicable_sectors: scoped to requesting member state's sectors
"""

from django.test import TestCase, override_settings
from django.urls import reverse

from core.models import Sector as GlobalSector
from dashboard.forms import IncentiveForm, SectorAddForm, SectorEditForm
from dashboard.tests.factories import (
    IPAUserFactory,
    IPAWASAdminFactory,
    MemberStateIPAFactory,
    SectorFactory,
)
from members.models import InvestmentIncentive, MemberStateSector


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_member_state_sector(member_state, sector=None, **kwargs):
    if sector is None:
        sector = SectorFactory()
    return MemberStateSector.objects.create(
        member_state=member_state,
        sector=sector,
        **kwargs,
    )


def _login(client, ipa_user_obj):
    client.force_login(ipa_user_obj.user)


# ---------------------------------------------------------------------------
# Form tests
# ---------------------------------------------------------------------------

class SectorAddFormTests(TestCase):

    def test_valid_with_name_only(self):
        form = SectorAddForm(data={"sector_name": "Agriculture"})
        self.assertTrue(form.is_valid())

    def test_sector_name_stripped(self):
        form = SectorAddForm(data={"sector_name": "  Agriculture  "})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["sector_name"], "Agriculture")

    def test_sector_name_required(self):
        form = SectorAddForm(data={"sector_name": ""})
        self.assertFalse(form.is_valid())
        self.assertIn("sector_name", form.errors)

    def test_all_optional_fields(self):
        form = SectorAddForm(data={
            "sector_name": "Mining",
            "description": "Key sector",
            "investment_potential": "High",
            "is_priority": True,
        })
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["description"], "Key sector")
        self.assertTrue(form.cleaned_data["is_priority"])


class SectorEditFormTests(TestCase):

    def setUp(self):
        self.member_state = MemberStateIPAFactory()
        self.sector = SectorFactory(name="Tourism")
        self.mss = make_member_state_sector(self.member_state, self.sector)

    def test_edit_form_excludes_sector_name(self):
        form = SectorEditForm(instance=self.mss)
        self.assertNotIn("sector_name", form.fields)
        self.assertNotIn("sector", form.fields)

    def test_valid_update(self):
        form = SectorEditForm(
            instance=self.mss,
            data={
                "description": "Updated desc",
                "investment_potential": "Medium",
                "is_priority": True,
            },
        )
        self.assertTrue(form.is_valid())
        obj = form.save()
        self.assertEqual(obj.description, "Updated desc")
        self.assertTrue(obj.is_priority)


# ---------------------------------------------------------------------------
# SectorListView
# ---------------------------------------------------------------------------

@override_settings(STORAGES={"default": {"BACKEND": "django.core.files.storage.InMemoryStorage"}, "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}})
class SectorListViewTests(TestCase):

    def setUp(self):
        self.ipa_user = IPAUserFactory()
        self.member_state = self.ipa_user.member_state
        self.url = reverse(
            "dashboard:country:sectors",
            kwargs={"member_state_slug": self.member_state.slug},
        )

    def test_login_required(self):
        resp = self.client.get(self.url)
        self.assertRedirects(resp, f"/en/accounts/login/?next={self.url}", fetch_redirect_response=False)

    def test_shows_own_sectors_only(self):
        own = make_member_state_sector(self.member_state, SectorFactory(name="Agriculture"))
        other_ms = MemberStateIPAFactory()
        make_member_state_sector(other_ms, SectorFactory(name="Mining"))

        _login(self.client, self.ipa_user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        qs = resp.context["object_list"]
        self.assertIn(own, qs)
        self.assertEqual(qs.count(), 1)

    def test_context_object_name_is_sectors(self):
        """
        Regression test: the template iterates `{% for sector in sectors %}`
        and checks `{% if sectors %}`, but the view previously only exposed
        the queryset as Django's default `object_list` — `sectors` was always
        undefined, so the template silently fell through to its `{% empty %}`
        branch and showed "No Priority Sectors Yet" regardless of how many
        sectors actually existed.
        """
        make_member_state_sector(self.member_state, SectorFactory(name="Agriculture"))

        _login(self.client, self.ipa_user)
        resp = self.client.get(self.url)
        self.assertIn("sectors", resp.context)
        self.assertEqual(list(resp.context["sectors"]), list(resp.context["object_list"]))

    def test_existing_sectors_render_in_the_page_not_empty_state(self):
        make_member_state_sector(self.member_state, SectorFactory(name="Agriculture"))

        _login(self.client, self.ipa_user)
        content = self.client.get(self.url).content.decode()
        self.assertIn("Agriculture", content)
        self.assertNotIn("No Priority Sectors Yet", content)

    def test_empty_state_shown_only_when_there_are_no_sectors(self):
        _login(self.client, self.ipa_user)
        content = self.client.get(self.url).content.decode()
        self.assertIn("No Priority Sectors Yet", content)


# ---------------------------------------------------------------------------
# SectorAddView
# ---------------------------------------------------------------------------

@override_settings(STORAGES={"default": {"BACKEND": "django.core.files.storage.InMemoryStorage"}, "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}})
class SectorAddViewTests(TestCase):

    def setUp(self):
        self.ipa_user = IPAUserFactory()
        self.member_state = self.ipa_user.member_state
        self.url = reverse(
            "dashboard:country:sectors_add",
            kwargs={"member_state_slug": self.member_state.slug},
        )
        _login(self.client, self.ipa_user)

    def test_get_renders_form(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("form", resp.context)
        self.assertIn("existing_sector_names", resp.context)

    def test_datalist_contains_existing_sector_names(self):
        SectorFactory(name="Tourism")
        resp = self.client.get(self.url)
        self.assertIn("Tourism", resp.context["existing_sector_names"])

    def test_post_creates_global_sector_and_member_state_sector(self):
        self.assertEqual(GlobalSector.objects.filter(name="New Tech").count(), 0)
        resp = self.client.post(self.url, {"sector_name": "New Tech"})
        self.assertRedirects(
            resp,
            reverse("dashboard:country:sectors", kwargs={"member_state_slug": self.member_state.slug}),
            fetch_redirect_response=False,
        )
        self.assertTrue(GlobalSector.objects.filter(name="New Tech").exists())
        self.assertTrue(
            MemberStateSector.objects.filter(
                member_state=self.member_state,
                sector__name="New Tech",
            ).exists()
        )

    def test_post_reuses_existing_global_sector(self):
        existing = SectorFactory(name="Agriculture")
        self.client.post(self.url, {"sector_name": "Agriculture"})
        self.assertEqual(GlobalSector.objects.filter(name="Agriculture").count(), 1)
        linked = MemberStateSector.objects.get(member_state=self.member_state, sector=existing)
        self.assertIsNotNone(linked)

    def test_post_sets_optional_fields(self):
        self.client.post(self.url, {
            "sector_name": "Mining",
            "description": "Rich mineral reserves",
            "investment_potential": "Very High",
            "is_priority": "on",
        })
        mss = MemberStateSector.objects.get(member_state=self.member_state, sector__name="Mining")
        self.assertEqual(mss.description, "Rich mineral reserves")
        self.assertEqual(mss.investment_potential, "Very High")
        self.assertTrue(mss.is_priority)

    def test_duplicate_sector_rejected(self):
        sector = SectorFactory(name="Tourism")
        make_member_state_sector(self.member_state, sector)
        resp = self.client.post(self.url, {"sector_name": "Tourism"})
        self.assertEqual(resp.status_code, 200)
        form = resp.context["form"]
        self.assertIn("sector_name", form.errors)
        self.assertIn("already been added", form.errors["sector_name"][0])

    def test_slug_collision_gets_suffix(self):
        # Two sectors "Tech" and "Tech " (whitespace stripped) should share a global entry
        # but if a different sector already has slug "tech", a suffix is appended
        GlobalSector.objects.create(name="Other Tech", slug="tech")
        self.client.post(self.url, {"sector_name": "Tech"})
        new_sector = GlobalSector.objects.get(name="Tech")
        self.assertNotEqual(new_sector.slug, "tech")
        self.assertTrue(new_sector.slug.startswith("tech-"))


# ---------------------------------------------------------------------------
# SectorEditView
# ---------------------------------------------------------------------------

@override_settings(STORAGES={"default": {"BACKEND": "django.core.files.storage.InMemoryStorage"}, "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}})
class SectorEditViewTests(TestCase):

    def setUp(self):
        self.ipa_user = IPAUserFactory()
        self.member_state = self.ipa_user.member_state
        self.sector = SectorFactory(name="Energy")
        self.mss = make_member_state_sector(
            self.member_state, self.sector,
            description="Old desc", investment_potential="Low"
        )
        self.url = reverse(
            "dashboard:country:sectors_edit",
            kwargs={"member_state_slug": self.member_state.slug, "pk": self.mss.pk},
        )
        _login(self.client, self.ipa_user)

    def test_get_renders_edit_form(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context["object"], self.mss)

    def test_get_shows_sector_name_readonly(self):
        resp = self.client.get(self.url)
        self.assertContains(resp, "Energy")

    def test_post_updates_description_and_potential(self):
        resp = self.client.post(self.url, {
            "description": "Updated description",
            "investment_potential": "High",
            "is_priority": "",
        })
        self.assertRedirects(
            resp,
            reverse("dashboard:country:sectors", kwargs={"member_state_slug": self.member_state.slug}),
            fetch_redirect_response=False,
        )
        self.mss.refresh_from_db()
        self.assertEqual(self.mss.description, "Updated description")
        self.assertEqual(self.mss.investment_potential, "High")
        self.assertFalse(self.mss.is_priority)

    def test_post_marks_priority(self):
        self.client.post(self.url, {
            "description": "x",
            "investment_potential": "x",
            "is_priority": "on",
        })
        self.mss.refresh_from_db()
        self.assertTrue(self.mss.is_priority)

    def test_cannot_edit_another_states_sector(self):
        other_ms = MemberStateIPAFactory()
        other_mss = make_member_state_sector(other_ms, SectorFactory(name="Finance"))
        url = reverse(
            "dashboard:country:sectors_edit",
            kwargs={"member_state_slug": self.member_state.slug, "pk": other_mss.pk},
        )
        resp = self.client.post(url, {"description": "hacked", "investment_potential": "", "is_priority": ""})
        self.assertEqual(resp.status_code, 404)
        other_mss.refresh_from_db()
        self.assertNotEqual(other_mss.description, "hacked")


# ---------------------------------------------------------------------------
# SectorDeleteView
# ---------------------------------------------------------------------------

@override_settings(STORAGES={"default": {"BACKEND": "django.core.files.storage.InMemoryStorage"}, "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}})
class SectorDeleteViewTests(TestCase):

    def setUp(self):
        self.ipa_user = IPAUserFactory()
        self.member_state = self.ipa_user.member_state
        self.sector = SectorFactory(name="Retail")
        self.mss = make_member_state_sector(self.member_state, self.sector)
        self.url = reverse(
            "dashboard:country:sectors_delete",
            kwargs={"member_state_slug": self.member_state.slug, "pk": self.mss.pk},
        )
        _login(self.client, self.ipa_user)

    def test_get_renders_confirmation(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Retail")

    def test_post_removes_member_state_sector(self):
        resp = self.client.post(self.url)
        self.assertRedirects(
            resp,
            reverse("dashboard:country:sectors", kwargs={"member_state_slug": self.member_state.slug}),
            fetch_redirect_response=False,
        )
        self.assertFalse(MemberStateSector.objects.filter(pk=self.mss.pk).exists())

    def test_delete_does_not_remove_global_sector(self):
        self.client.post(self.url)
        self.assertTrue(GlobalSector.objects.filter(pk=self.sector.pk).exists())

    def test_cannot_delete_another_states_sector(self):
        other_ms = MemberStateIPAFactory()
        other_mss = make_member_state_sector(other_ms, SectorFactory(name="Pharma"))
        url = reverse(
            "dashboard:country:sectors_delete",
            kwargs={"member_state_slug": self.member_state.slug, "pk": other_mss.pk},
        )
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 404)
        self.assertTrue(MemberStateSector.objects.filter(pk=other_mss.pk).exists())


# ---------------------------------------------------------------------------
# IncentiveForm — applicable_sectors scoping
# ---------------------------------------------------------------------------

class IncentiveFormApplicableSectorsTests(TestCase):

    def setUp(self):
        self.ms_a = MemberStateIPAFactory()
        self.ms_b = MemberStateIPAFactory()

        self.sector_a = SectorFactory(name="Agriculture")
        self.sector_b = SectorFactory(name="Mining")
        self.sector_shared = SectorFactory(name="Technology")

        make_member_state_sector(self.ms_a, self.sector_a)
        make_member_state_sector(self.ms_a, self.sector_shared)
        make_member_state_sector(self.ms_b, self.sector_b)
        make_member_state_sector(self.ms_b, self.sector_shared)

    def test_form_scoped_to_member_state_a(self):
        form = IncentiveForm(member_state=self.ms_a)
        qs = form.fields["applicable_sectors"].queryset
        self.assertIn(self.sector_a, qs)
        self.assertIn(self.sector_shared, qs)
        self.assertNotIn(self.sector_b, qs)

    def test_form_scoped_to_member_state_b(self):
        form = IncentiveForm(member_state=self.ms_b)
        qs = form.fields["applicable_sectors"].queryset
        self.assertIn(self.sector_b, qs)
        self.assertIn(self.sector_shared, qs)
        self.assertNotIn(self.sector_a, qs)

    def test_form_without_member_state_shows_all(self):
        form = IncentiveForm()
        qs = form.fields["applicable_sectors"].queryset
        self.assertIn(self.sector_a, qs)
        self.assertIn(self.sector_b, qs)
        self.assertIn(self.sector_shared, qs)

    def test_form_falls_back_to_all_sectors_when_none_configured(self):
        """
        Regression test: a member state that hasn't added any Priority Sectors
        yet must still see every global sector as a selectable option — the
        field must never render empty. Previously this queryset went empty for
        any country with zero MemberStateSector rows.
        """
        empty_state = MemberStateIPAFactory()  # no MemberStateSector rows created
        form = IncentiveForm(member_state=empty_state)
        qs = form.fields["applicable_sectors"].queryset
        self.assertTrue(qs.exists())
        self.assertIn(self.sector_a, qs)
        self.assertIn(self.sector_b, qs)
        self.assertIn(self.sector_shared, qs)

    def test_applicable_sectors_widget_is_checkbox(self):
        from django import forms as django_forms
        form = IncentiveForm(member_state=self.ms_a)
        self.assertIsInstance(
            form.fields["applicable_sectors"].widget,
            django_forms.CheckboxSelectMultiple,
        )

    def test_applicable_sectors_not_required(self):
        form = IncentiveForm(member_state=self.ms_a)
        self.assertFalse(form.fields["applicable_sectors"].required)


# ---------------------------------------------------------------------------
# IncentiveCreateView — end-to-end reproduction of the reported bug:
# "Applicable Sectors cannot be selected" on /dashboard/<slug>/incentives/add/
# for a country that hasn't added any Priority Sectors yet.
# ---------------------------------------------------------------------------

class IncentiveCreateViewApplicableSectorsTests(TestCase):

    def setUp(self):
        self.ipa_user = IPAUserFactory()
        self.member_state = self.ipa_user.member_state
        self.url = reverse(
            "dashboard:country:incentives_add",
            kwargs={"member_state_slug": self.member_state.slug},
        )
        _login(self.client, self.ipa_user)

    def test_no_priority_sectors_still_renders_selectable_checkboxes(self):
        """
        The exact reported scenario: a country with zero configured
        Priority Sectors must still see a usable checkbox list, not the
        'No sectors are available' empty state.
        """
        SectorFactory(name="Agriculture")
        SectorFactory(name="Renewable Energy")

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()

        self.assertIn("sector-checkbox-grid", content)
        self.assertNotIn("No sectors are available in the system yet.", content)
        self.assertIn("Agriculture", content)
        self.assertIn("Renewable Energy", content)

    def test_configured_sectors_are_still_scoped(self):
        """Once the country has its own sectors, only those are offered."""
        own_sector = SectorFactory(name="Tourism")
        other_sector = SectorFactory(name="Mining")
        make_member_state_sector(self.member_state, own_sector)

        resp = self.client.get(self.url)
        content = resp.content.decode()

        self.assertIn("sector-checkbox-grid", content)
        self.assertIn("Tourism", content)
        self.assertNotIn("Mining", content)

    def test_post_saves_selected_applicable_sectors(self):
        """The whole point of the field: a selected sector must persist on save."""
        sector = SectorFactory(name="Fintech")
        resp = self.client.post(self.url, {
            "title": "5-Year Tax Holiday",
            "incentive_type": "tax_holiday",
            "description": "Full corporate tax exemption for qualifying investors.",
            "applicable_sectors": [str(sector.pk)],
            "is_active": "on",
            "display_order": "0",
        })
        self.assertEqual(resp.status_code, 302)
        incentive = InvestmentIncentive.objects.get(member_state=self.member_state)
        self.assertIn(sector, incentive.applicable_sectors.all())
