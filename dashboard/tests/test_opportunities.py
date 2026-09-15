"""
Tests for the Member State Opportunity create/edit views.

Covers:
- _parse_coordinates helper
- OpportunityCreateView: GET renders form; POST creates with all fields;
  geo coordinates stored as JSON; video_url saved; secondary_sectors M2M saved;
  is_regional + participating_countries saved; featured flag; publish action;
  IDOR protection (staff can only create for their own member state)
- OpportunityEditView: GET pre-populates geo context; POST updates all fields;
  geo cleared when both empty; geo preserved when only one provided (keep sentinel);
  gallery appended not replaced; IDOR returns 404
- _handle_file_uploads: Cloudinary calls mocked; gallery append vs replace behaviour
"""

from unittest.mock import MagicMock, patch

from django import forms as django_forms
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.text import slugify

from core.models import Sector
from dashboard.tests.factories import (
    IPAUserFactory,
    IPAWASAdminFactory,
    MemberStateIPAFactory,
    SectorFactory,
    InvestmentOpportunityFactory,
)
from dashboard.views.members.opportunities import _parse_coordinates
from members.models import MemberStateIPA
from opportunities.models import InvestmentOpportunity


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _login(client, ipa_user):
    client.force_login(ipa_user.user)


def _create_url(member_state):
    return reverse(
        "dashboard:country:opportunities_create",
        kwargs={"member_state_slug": member_state.slug},
    )


def _edit_url(member_state, pk):
    return reverse(
        "dashboard:country:opportunities_edit",
        kwargs={"member_state_slug": member_state.slug, "pk": pk},
    )


def _minimal_post(primary_sector_id, **overrides):
    """Minimum valid POST data for the opportunity form."""
    data = {
        "title": "Test Opportunity",
        "summary": "A brief summary of the test opportunity.",
        "description": "A detailed description of the test opportunity.",
        "opportunity_type": "greenfield",
        "project_stage": "concept",
        "priority_level": "standard",
        "primary_sector": primary_sector_id,
        "investment_required_min": "1000000.00",
        "action": "draft",
    }
    data.update(overrides)
    return data


# ---------------------------------------------------------------------------
# _parse_coordinates unit tests
# ---------------------------------------------------------------------------

class FakeRequest:
    def __init__(self, post):
        self.POST = post


class ParseCoordinatesTests(TestCase):

    def test_both_valid_returns_dict(self):
        req = FakeRequest({"geo_lat": "5.6037", "geo_lng": "-0.1870"})
        result = _parse_coordinates(req)
        self.assertEqual(result, {"lat": 5.6037, "lng": -0.1870})

    def test_both_empty_returns_none(self):
        req = FakeRequest({"geo_lat": "", "geo_lng": ""})
        self.assertIsNone(_parse_coordinates(req))

    def test_both_missing_returns_none(self):
        req = FakeRequest({})
        self.assertIsNone(_parse_coordinates(req))

    def test_only_lat_returns_keep(self):
        req = FakeRequest({"geo_lat": "5.6037", "geo_lng": ""})
        self.assertEqual(_parse_coordinates(req), "keep")

    def test_only_lng_returns_keep(self):
        req = FakeRequest({"geo_lat": "", "geo_lng": "-0.1870"})
        self.assertEqual(_parse_coordinates(req), "keep")

    def test_invalid_float_returns_keep(self):
        req = FakeRequest({"geo_lat": "not-a-number", "geo_lng": "-0.1870"})
        self.assertEqual(_parse_coordinates(req), "keep")

    def test_whitespace_trimmed(self):
        req = FakeRequest({"geo_lat": "  5.6037  ", "geo_lng": "  -0.1870  "})
        result = _parse_coordinates(req)
        self.assertEqual(result["lat"], 5.6037)


# ---------------------------------------------------------------------------
# OpportunityCreateView
# ---------------------------------------------------------------------------

@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
)
class OpportunityCreateViewTests(TestCase):

    def setUp(self):
        self.ipa_user = IPAUserFactory()
        self.member_state = self.ipa_user.member_state
        self.sector = SectorFactory(name="Agriculture")
        self.url = _create_url(self.member_state)
        _login(self.client, self.ipa_user)

    def test_login_required(self):
        self.client.logout()
        resp = self.client.get(self.url)
        self.assertRedirects(resp, f"/en/accounts/login/?next={self.url}", fetch_redirect_response=False)

    def test_get_renders_form(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("form", resp.context)

    def test_get_context_has_geo_keys(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.context["geo_lat"], "")
        self.assertEqual(resp.context["geo_lng"], "")

    def test_get_start_date_is_date_input(self):
        resp = self.client.get(self.url)
        form = resp.context["form"]
        widget = form.fields["start_date_target"].widget
        # DateInput stores the type as input_type, not in attrs
        self.assertIsInstance(widget, django_forms.DateInput)
        self.assertEqual(widget.input_type, "date")

    def test_post_creates_draft(self):
        self.client.post(self.url, _minimal_post(self.sector.pk, action="draft"))
        opp = InvestmentOpportunity.objects.filter(
            primary_country=self.member_state, title="Test Opportunity"
        ).first()
        self.assertIsNotNone(opp)
        self.assertFalse(opp.published)
        self.assertEqual(opp.status, "draft")

    def test_post_publish_sets_active(self):
        self.client.post(self.url, _minimal_post(self.sector.pk, action="publish"))
        opp = InvestmentOpportunity.objects.get(primary_country=self.member_state, title="Test Opportunity")
        self.assertTrue(opp.published)
        self.assertEqual(opp.status, "active")
        self.assertIsNotNone(opp.published_date)

    def test_post_redirects_to_list_on_success(self):
        resp = self.client.post(self.url, _minimal_post(self.sector.pk))
        list_url = reverse("dashboard:country:opportunities", kwargs={"member_state_slug": self.member_state.slug})
        self.assertRedirects(resp, list_url, fetch_redirect_response=False)

    def test_post_saves_new_fields(self):
        self.client.post(self.url, _minimal_post(
            self.sector.pk,
            priority_level="high",
            implementing_agency="GIPC",
            implementing_agency_contact="gipc@gov.gh",
            financial_incentives_available="Tax holiday for 5 years",
            regulatory_framework="Investment Act 2013",
            approval_process="Submit via GIPC portal",
            licenses_required="Business registration",
            land_availability="100 acres available",
            revenue_projections="$2M in year 3",
            local_content_requirements="30% local employees",
            video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        ))
        opp = InvestmentOpportunity.objects.get(primary_country=self.member_state)
        self.assertEqual(opp.priority_level, "high")
        self.assertEqual(opp.implementing_agency, "GIPC")
        self.assertEqual(opp.implementing_agency_contact, "gipc@gov.gh")
        self.assertEqual(opp.financial_incentives_available, "Tax holiday for 5 years")
        self.assertEqual(opp.regulatory_framework, "Investment Act 2013")
        self.assertEqual(opp.approval_process, "Submit via GIPC portal")
        self.assertEqual(opp.licenses_required, "Business registration")
        self.assertEqual(opp.land_availability, "100 acres available")
        self.assertEqual(opp.revenue_projections, "$2M in year 3")
        self.assertEqual(opp.local_content_requirements, "30% local employees")
        self.assertEqual(opp.video_url, "https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    def test_post_saves_geo_coordinates(self):
        self.client.post(self.url, _minimal_post(
            self.sector.pk, geo_lat="5.6037", geo_lng="-0.1870"
        ))
        opp = InvestmentOpportunity.objects.get(primary_country=self.member_state)
        self.assertEqual(opp.geographic_coordinates, {"lat": 5.6037, "lng": -0.1870})

    def test_post_no_geo_leaves_coordinates_null(self):
        self.client.post(self.url, _minimal_post(self.sector.pk))
        opp = InvestmentOpportunity.objects.get(primary_country=self.member_state)
        self.assertIsNone(opp.geographic_coordinates)

    def test_post_invalid_geo_leaves_coordinates_null(self):
        self.client.post(self.url, _minimal_post(
            self.sector.pk, geo_lat="not-a-number", geo_lng="-0.1870"
        ))
        opp = InvestmentOpportunity.objects.get(primary_country=self.member_state)
        self.assertIsNone(opp.geographic_coordinates)

    def test_post_featured_flag(self):
        self.client.post(self.url, _minimal_post(self.sector.pk, featured="on"))
        opp = InvestmentOpportunity.objects.get(primary_country=self.member_state)
        self.assertTrue(opp.featured)

    def test_post_no_featured_flag(self):
        self.client.post(self.url, _minimal_post(self.sector.pk))
        opp = InvestmentOpportunity.objects.get(primary_country=self.member_state)
        self.assertFalse(opp.featured)

    def test_post_secondary_sectors_m2m(self):
        sector_b = SectorFactory(name="Mining")
        sector_c = SectorFactory(name="Tourism")
        self.client.post(self.url, _minimal_post(
            self.sector.pk,
            secondary_sectors=[sector_b.pk, sector_c.pk],
        ))
        opp = InvestmentOpportunity.objects.get(primary_country=self.member_state)
        self.assertIn(sector_b, opp.secondary_sectors.all())
        self.assertIn(sector_c, opp.secondary_sectors.all())

    def test_post_is_regional_with_participating_countries(self):
        other_ms = MemberStateIPAFactory()
        self.client.post(self.url, _minimal_post(
            self.sector.pk,
            is_regional="on",
            participating_countries=[other_ms.pk],
        ))
        opp = InvestmentOpportunity.objects.get(primary_country=self.member_state)
        self.assertTrue(opp.is_regional)
        self.assertIn(other_ms, opp.participating_countries.all())

    def test_post_invalid_form_returns_200(self):
        resp = self.client.post(self.url, {"title": ""})
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(InvestmentOpportunity.objects.filter(primary_country=self.member_state).exists())

    def test_post_sets_primary_country_to_own_member_state(self):
        self.client.post(self.url, _minimal_post(self.sector.pk))
        opp = InvestmentOpportunity.objects.get(title="Test Opportunity")
        self.assertEqual(opp.primary_country, self.member_state)

    def test_ipa_staff_can_access_other_states_create_url_but_post_scoped_to_own_state(self):
        """The create URL slug is cosmetic; form_valid always uses the authenticated user's state."""
        other_ms = MemberStateIPAFactory()
        url = _create_url(other_ms)
        # GET is allowed — OpportunityCreateView doesn't use MemberStateAccessMixin
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        # POST still creates the opportunity under the authenticated user's member state
        self.client.post(url, _minimal_post(self.sector.pk))
        opp = InvestmentOpportunity.objects.filter(title="Test Opportunity").first()
        self.assertIsNotNone(opp)
        self.assertEqual(opp.primary_country, self.member_state)  # own state, not other_ms


# ---------------------------------------------------------------------------
# OpportunityEditView
# ---------------------------------------------------------------------------

@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
)
class OpportunityEditViewTests(TestCase):

    def setUp(self):
        self.ipa_user = IPAUserFactory()
        self.member_state = self.ipa_user.member_state
        self.sector = SectorFactory(name="Energy")
        self.opp = InvestmentOpportunityFactory(
            primary_country=self.member_state,
            primary_sector=self.sector,
        )
        self.url = _edit_url(self.member_state, self.opp.pk)
        _login(self.client, self.ipa_user)

    def test_get_200(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_get_populates_geo_context(self):
        self.opp.geographic_coordinates = {"lat": 5.6037, "lng": -0.1870}
        self.opp.save(update_fields=["geographic_coordinates"])
        resp = self.client.get(self.url)
        self.assertEqual(resp.context["geo_lat"], 5.6037)
        self.assertEqual(resp.context["geo_lng"], -0.1870)

    def test_get_geo_context_empty_when_no_coords(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.context["geo_lat"], "")
        self.assertEqual(resp.context["geo_lng"], "")

    def test_get_start_date_is_date_input(self):
        resp = self.client.get(self.url)
        form = resp.context["form"]
        widget = form.fields["start_date_target"].widget
        self.assertIsInstance(widget, django_forms.DateInput)
        self.assertEqual(widget.input_type, "date")

    def test_post_updates_title_and_description(self):
        data = _minimal_post(self.sector.pk, title="Updated Title", description="Updated desc.", action="save")
        self.client.post(self.url, data)
        self.opp.refresh_from_db()
        self.assertEqual(self.opp.title, "Updated Title")

    def test_post_updates_new_fields(self):
        data = _minimal_post(
            self.sector.pk,
            financial_incentives_available="5-year tax holiday",
            regulatory_framework="Investment Act",
            land_availability="200 acres",
            video_url="https://vimeo.com/123456789",
            action="save",
        )
        self.client.post(self.url, data)
        self.opp.refresh_from_db()
        self.assertEqual(self.opp.financial_incentives_available, "5-year tax holiday")
        self.assertEqual(self.opp.land_availability, "200 acres")
        self.assertEqual(self.opp.video_url, "https://vimeo.com/123456789")

    def test_post_saves_geo_coordinates(self):
        self.client.post(self.url, _minimal_post(
            self.sector.pk, geo_lat="5.6037", geo_lng="-0.1870", action="save"
        ))
        self.opp.refresh_from_db()
        self.assertEqual(self.opp.geographic_coordinates, {"lat": 5.6037, "lng": -0.1870})

    def test_post_clears_geo_when_both_empty(self):
        self.opp.geographic_coordinates = {"lat": 5.6037, "lng": -0.1870}
        self.opp.save(update_fields=["geographic_coordinates"])
        self.client.post(self.url, _minimal_post(
            self.sector.pk, geo_lat="", geo_lng="", action="save"
        ))
        self.opp.refresh_from_db()
        self.assertIsNone(self.opp.geographic_coordinates)

    def test_post_preserves_geo_when_one_field_provided(self):
        """Only one of lat/lng provided → 'keep' sentinel → coordinates unchanged."""
        self.opp.geographic_coordinates = {"lat": 5.6037, "lng": -0.1870}
        self.opp.save(update_fields=["geographic_coordinates"])
        self.client.post(self.url, _minimal_post(
            self.sector.pk, geo_lat="9.9999", geo_lng="", action="save"
        ))
        self.opp.refresh_from_db()
        self.assertEqual(self.opp.geographic_coordinates, {"lat": 5.6037, "lng": -0.1870})

    def test_post_publish_from_draft(self):
        self.assertEqual(self.opp.status, "draft")
        self.client.post(self.url, _minimal_post(self.sector.pk, action="publish"))
        self.opp.refresh_from_db()
        self.assertTrue(self.opp.published)
        self.assertEqual(self.opp.status, "active")

    def test_post_redirects_to_list(self):
        resp = self.client.post(self.url, _minimal_post(self.sector.pk, action="save"))
        list_url = reverse("dashboard:country:opportunities", kwargs={"member_state_slug": self.member_state.slug})
        self.assertRedirects(resp, list_url, fetch_redirect_response=False)

    def test_cannot_edit_another_states_opportunity(self):
        other_ms = MemberStateIPAFactory()
        other_opp = InvestmentOpportunityFactory(
            primary_country=other_ms,
            primary_sector=self.sector,
        )
        url = _edit_url(self.member_state, other_opp.pk)
        resp = self.client.get(url)
        # get_queryset scoped to own member state → 404
        self.assertEqual(resp.status_code, 404)

    def test_cannot_edit_via_post_idor(self):
        other_ms = MemberStateIPAFactory()
        other_opp = InvestmentOpportunityFactory(
            primary_country=other_ms,
            primary_sector=self.sector,
            title="Original Title",
        )
        url = _edit_url(self.member_state, other_opp.pk)
        resp = self.client.post(url, _minimal_post(self.sector.pk, title="Hacked"))
        self.assertEqual(resp.status_code, 404)
        other_opp.refresh_from_db()
        self.assertEqual(other_opp.title, "Original Title")

    def test_gallery_appended_on_edit(self):
        """Existing gallery URLs are preserved when new images are uploaded in edit mode."""
        self.opp.gallery_images = ["https://existing.com/img.jpg"]
        self.opp.save(update_fields=["gallery_images"])
        # We don't actually upload; the edit _handle_file_uploads only runs if FILES present.
        # Confirm existing gallery untouched when no new files are submitted.
        self.client.post(self.url, _minimal_post(self.sector.pk, action="save"))
        self.opp.refresh_from_db()
        self.assertEqual(self.opp.gallery_images, ["https://existing.com/img.jpg"])


# ---------------------------------------------------------------------------
# _handle_file_uploads — unit tests with mocked Cloudinary
# ---------------------------------------------------------------------------

@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
)
class HandleFileUploadsTests(TestCase):
    """
    Test _handle_file_uploads behaviour by hitting the create/edit views with
    mocked Cloudinary so no real HTTP calls are made.
    """

    def setUp(self):
        self.ipa_user = IPAUserFactory()
        self.member_state = self.ipa_user.member_state
        self.sector = SectorFactory(name="Tech")
        _login(self.client, self.ipa_user)

    def _mock_upload(self, url="https://res.cloudinary.com/test/image.jpg"):
        return {"success": True, "data": {"secure_url": url}}

    @patch("dashboard.views.members.opportunities.CloudinaryService.initialize")
    @patch("dashboard.views.members.opportunities.CloudinaryService.upload_file")
    def test_create_saves_thumbnail_url(self, mock_upload, mock_init):
        mock_upload.return_value = self._mock_upload("https://cdn.test/thumb.jpg")

        from io import BytesIO
        from django.core.files.uploadedfile import SimpleUploadedFile
        img = SimpleUploadedFile("thumb.jpg", b"fakeimage", content_type="image/jpeg")

        url = _create_url(self.member_state)
        self.client.post(url, {
            **_minimal_post(self.sector.pk),
            "thumbnail_image": img,
        })
        opp = InvestmentOpportunity.objects.get(primary_country=self.member_state)
        self.assertEqual(opp.thumbnail_image, "https://cdn.test/thumb.jpg")

    @patch("dashboard.views.members.opportunities.CloudinaryService.initialize")
    @patch("dashboard.views.members.opportunities.CloudinaryService.upload_file")
    def test_edit_appends_gallery_images(self, mock_upload, mock_init):
        opp = InvestmentOpportunityFactory(
            primary_country=self.member_state,
            primary_sector=self.sector,
            gallery_images=["https://existing.com/old.jpg"],
        )
        mock_upload.return_value = self._mock_upload("https://cdn.test/new.jpg")

        from io import BytesIO
        from django.core.files.uploadedfile import SimpleUploadedFile
        img = SimpleUploadedFile("new.jpg", b"fakeimage", content_type="image/jpeg")

        url = _edit_url(self.member_state, opp.pk)
        self.client.post(url, {
            **_minimal_post(self.sector.pk, action="save"),
            "gallery_images": img,
        })
        opp.refresh_from_db()
        self.assertIn("https://existing.com/old.jpg", opp.gallery_images)
        self.assertIn("https://cdn.test/new.jpg", opp.gallery_images)
        self.assertEqual(len(opp.gallery_images), 2)

    @patch("dashboard.views.members.opportunities.CloudinaryService.initialize")
    @patch("dashboard.views.members.opportunities.CloudinaryService.upload_file")
    def test_create_replaces_gallery_images(self, mock_upload, mock_init):
        """On create, gallery starts fresh (no prior images to preserve)."""
        mock_upload.return_value = self._mock_upload("https://cdn.test/first.jpg")

        from django.core.files.uploadedfile import SimpleUploadedFile
        img = SimpleUploadedFile("first.jpg", b"fakeimage", content_type="image/jpeg")

        url = _create_url(self.member_state)
        self.client.post(url, {
            **_minimal_post(self.sector.pk),
            "gallery_images": img,
        })
        opp = InvestmentOpportunity.objects.get(primary_country=self.member_state)
        self.assertEqual(opp.gallery_images, ["https://cdn.test/first.jpg"])
