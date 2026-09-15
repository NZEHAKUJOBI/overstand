"""
Tests for investment-resource document upload wiring
(apps/dashboard/views/members/profile.py — ResourcesUpdateView,
ResourceUploadSignatureView, ResourceSaveDocumentUrlView).

Background: the public "Download Resources" widget links to 4 documents,
but only 2 (investment_guide_pdf, doing_business_pdf) had working dashboard
upload support — sector_profiles_pdf and incentives_brochure_pdf were fully
modeled but commented out of the upload views. This file covers enabling
those 2 fields end-to-end without touching the still-out-of-scope
legal_framework_pdf / infrastructure_report_pdf fields.

Covers:
- GET renders all 4 upload zones
- POST (classic multipart) upload handling for all 4 resource PDF fields
- File type / size validation still applies to the newly-enabled fields
- Direct-to-Cloudinary signature endpoint accepts the 2 newly-enabled fields
  and still rejects out-of-scope / unknown fields
- Save-document-url endpoint accepts the 2 newly-enabled fields, rejects
  unknown fields and non-Cloudinary URLs
- Access control: anonymous redirected, non-IPA-staff denied
"""

import json
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from dashboard.tests.factories import IPAUserFactory


def _login(client, ipa_user):
    client.force_login(ipa_user.user)


def _resources_url(member_state):
    return reverse(
        "dashboard:country:profile_resources",
        kwargs={"member_state_slug": member_state.slug},
    )


def _signature_url(member_state, field):
    url = reverse(
        "dashboard:country:profile_resources_signature",
        kwargs={"member_state_slug": member_state.slug},
    )
    return f"{url}?field={field}"


def _save_url_endpoint(member_state):
    return reverse(
        "dashboard:country:profile_resources_save_url",
        kwargs={"member_state_slug": member_state.slug},
    )


def _delete_endpoint(member_state):
    return reverse(
        "dashboard:country:profile_resources_delete",
        kwargs={"member_state_slug": member_state.slug},
    )


def _pdf_file(name="doc.pdf"):
    return SimpleUploadedFile(name, b"%PDF-1.4 fake pdf content", content_type="application/pdf")


class ResourcesUpdateViewGetTests(TestCase):
    """GET renders the resources tab with all 4 document cards."""

    def setUp(self):
        self.ipa_user = IPAUserFactory()
        self.member_state = self.ipa_user.member_state
        _login(self.client, self.ipa_user)

    def test_get_renders_all_four_upload_zones(self):
        response = self.client.get(_resources_url(self.member_state))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn('data-field="investment_guide_pdf"', content)
        self.assertIn('data-field="doing_business_pdf"', content)
        self.assertIn('data-field="incentives_brochure_pdf"', content)
        self.assertIn('data-field="sector_profiles_pdf"', content)

    def test_anonymous_redirected_to_login(self):
        self.client.logout()
        response = self.client.get(_resources_url(self.member_state))
        self.assertEqual(response.status_code, 302)

    def test_ipa_staff_without_edit_permission_gets_403(self):
        """ipa_analyst is read-only (can_edit_profile=False)."""
        self.client.logout()
        analyst = IPAUserFactory(member_state=self.member_state, role="ipa_analyst")
        self.client.force_login(analyst.user)
        response = self.client.get(_resources_url(self.member_state))
        self.assertEqual(response.status_code, 403)

    def test_remove_button_only_renders_for_uploaded_documents(self):
        self.member_state.incentives_brochure_pdf = "https://res.cloudinary.com/demo/raw/upload/incentives.pdf"
        self.member_state.save()

        content = self.client.get(_resources_url(self.member_state)).content.decode()
        self.assertIn("removeDocument('incentives_brochure_pdf', this)", content)
        self.assertNotIn("removeDocument('sector_profiles_pdf', this)", content)
        self.assertNotIn("removeDocument('investment_guide_pdf', this)", content)
        self.assertNotIn("removeDocument('doing_business_pdf', this)", content)


class ResourcesUpdateViewPostTests(TestCase):
    """POST (classic multipart) upload handling for all 4 document fields."""

    def setUp(self):
        self.ipa_user = IPAUserFactory()
        self.member_state = self.ipa_user.member_state
        _login(self.client, self.ipa_user)

    def _mock_upload(self, url):
        return {"success": True, "data": {"secure_url": url}}

    @patch("dashboard.views.members.profile.CloudinaryService.upload_file")
    def test_uploading_incentives_brochure_saves_url(self, mock_upload):
        mock_upload.return_value = self._mock_upload("https://res.cloudinary.com/test/incentives.pdf")
        self.client.post(_resources_url(self.member_state), {
            "incentives_brochure_pdf": _pdf_file("incentives.pdf"),
        })
        self.member_state.refresh_from_db()
        self.assertEqual(
            self.member_state.incentives_brochure_pdf,
            "https://res.cloudinary.com/test/incentives.pdf",
        )

    @patch("dashboard.views.members.profile.CloudinaryService.upload_file")
    def test_uploading_sector_profiles_saves_url(self, mock_upload):
        mock_upload.return_value = self._mock_upload("https://res.cloudinary.com/test/sectors.pdf")
        self.client.post(_resources_url(self.member_state), {
            "sector_profiles_pdf": _pdf_file("sectors.pdf"),
        })
        self.member_state.refresh_from_db()
        self.assertEqual(
            self.member_state.sector_profiles_pdf,
            "https://res.cloudinary.com/test/sectors.pdf",
        )

    @patch("dashboard.views.members.profile.CloudinaryService.upload_file")
    def test_uploading_all_four_documents_together(self, mock_upload):
        mock_upload.side_effect = [
            self._mock_upload("https://res.cloudinary.com/test/investment.pdf"),
            self._mock_upload("https://res.cloudinary.com/test/business.pdf"),
            self._mock_upload("https://res.cloudinary.com/test/sectors.pdf"),
            self._mock_upload("https://res.cloudinary.com/test/incentives.pdf"),
        ]
        self.client.post(_resources_url(self.member_state), {
            "investment_guide_pdf": _pdf_file("investment.pdf"),
            "doing_business_pdf": _pdf_file("business.pdf"),
            "sector_profiles_pdf": _pdf_file("sectors.pdf"),
            "incentives_brochure_pdf": _pdf_file("incentives.pdf"),
        })
        self.member_state.refresh_from_db()
        self.assertTrue(self.member_state.investment_guide_pdf)
        self.assertTrue(self.member_state.doing_business_pdf)
        self.assertTrue(self.member_state.sector_profiles_pdf)
        self.assertTrue(self.member_state.incentives_brochure_pdf)

    @patch("dashboard.views.members.profile.CloudinaryService.upload_file")
    def test_rejects_non_pdf_file_for_incentives(self, mock_upload):
        non_pdf = SimpleUploadedFile("doc.txt", b"not a pdf", content_type="text/plain")
        self.client.post(_resources_url(self.member_state), {
            "incentives_brochure_pdf": non_pdf,
        })
        self.member_state.refresh_from_db()
        self.assertEqual(self.member_state.incentives_brochure_pdf, "")
        mock_upload.assert_not_called()

    @patch("dashboard.views.members.profile.CloudinaryService.upload_file")
    def test_rejects_oversized_file_for_sector_profiles(self, mock_upload):
        big_file = SimpleUploadedFile(
            "big.pdf", b"x" * (51 * 1024 * 1024), content_type="application/pdf"
        )
        self.client.post(_resources_url(self.member_state), {
            "sector_profiles_pdf": big_file,
        })
        self.member_state.refresh_from_db()
        self.assertEqual(self.member_state.sector_profiles_pdf, "")
        mock_upload.assert_not_called()

    def test_legal_framework_pdf_still_not_wired(self):
        """
        Out of scope for this fix: legal_framework_pdf / infrastructure_report_pdf
        remain unwired (no public widget references them). Posting them should be
        a harmless no-op, not an error.
        """
        response = self.client.post(_resources_url(self.member_state), {
            "legal_framework_pdf": _pdf_file("legal.pdf"),
        })
        self.assertEqual(response.status_code, 302)  # redirects back, no crash
        self.member_state.refresh_from_db()
        self.assertEqual(self.member_state.legal_framework_pdf, "")


class ResourceUploadSignatureViewTests(TestCase):
    """Direct-to-Cloudinary signature endpoint."""

    def setUp(self):
        self.ipa_user = IPAUserFactory()
        self.member_state = self.ipa_user.member_state
        _login(self.client, self.ipa_user)

    def test_signature_for_incentives_brochure_pdf(self):
        response = self.client.get(_signature_url(self.member_state, "incentives_brochure_pdf"))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("signature", data)
        self.assertIn("cloud_name", data)
        self.assertIn("timestamp", data)
        self.assertEqual(data["resource_type"], "raw")

    def test_signature_for_sector_profiles_pdf(self):
        response = self.client.get(_signature_url(self.member_state, "sector_profiles_pdf"))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("signature", data)

    def test_signature_rejects_unknown_field(self):
        response = self.client.get(_signature_url(self.member_state, "not_a_real_field"))
        self.assertEqual(response.status_code, 400)

    def test_signature_still_rejects_legal_framework_pdf(self):
        """legal_framework_pdf is intentionally out of scope for this fix."""
        response = self.client.get(_signature_url(self.member_state, "legal_framework_pdf"))
        self.assertEqual(response.status_code, 400)

    def test_anonymous_cannot_get_signature(self):
        self.client.logout()
        response = self.client.get(_signature_url(self.member_state, "incentives_brochure_pdf"))
        self.assertEqual(response.status_code, 302)


class ResourceSaveDocumentUrlViewTests(TestCase):
    """Save-document-url endpoint (called after a direct browser->Cloudinary upload)."""

    def setUp(self):
        self.ipa_user = IPAUserFactory()
        self.member_state = self.ipa_user.member_state
        _login(self.client, self.ipa_user)

    def _post_json(self, payload):
        return self.client.post(
            _save_url_endpoint(self.member_state),
            data=json.dumps(payload),
            content_type="application/json",
        )

    def test_saves_incentives_brochure_url(self):
        response = self._post_json({
            "field": "incentives_brochure_pdf",
            "url": "https://res.cloudinary.com/demo/raw/upload/incentives.pdf",
        })
        self.assertEqual(response.status_code, 200)
        self.member_state.refresh_from_db()
        self.assertEqual(
            self.member_state.incentives_brochure_pdf,
            "https://res.cloudinary.com/demo/raw/upload/incentives.pdf",
        )

    def test_saves_sector_profiles_url(self):
        response = self._post_json({
            "field": "sector_profiles_pdf",
            "url": "https://res.cloudinary.com/demo/raw/upload/sectors.pdf",
        })
        self.assertEqual(response.status_code, 200)
        self.member_state.refresh_from_db()
        self.assertEqual(
            self.member_state.sector_profiles_pdf,
            "https://res.cloudinary.com/demo/raw/upload/sectors.pdf",
        )

    def test_rejects_unknown_field(self):
        response = self._post_json({
            "field": "not_a_real_field",
            "url": "https://res.cloudinary.com/demo/raw/upload/x.pdf",
        })
        self.assertEqual(response.status_code, 400)

    def test_rejects_non_cloudinary_url(self):
        response = self._post_json({
            "field": "incentives_brochure_pdf",
            "url": "https://evil.example.com/malware.pdf",
        })
        self.assertEqual(response.status_code, 400)
        self.member_state.refresh_from_db()
        self.assertEqual(self.member_state.incentives_brochure_pdf, "")

    def test_still_rejects_legal_framework_pdf(self):
        """legal_framework_pdf is intentionally out of scope for this fix."""
        response = self._post_json({
            "field": "legal_framework_pdf",
            "url": "https://res.cloudinary.com/demo/raw/upload/legal.pdf",
        })
        self.assertEqual(response.status_code, 400)


class ResourceDeleteDocumentViewTests(TestCase):
    """
    Delete-document endpoint. Lets IPA staff clear an already-uploaded
    resource document instead of only being able to view/copy its link.
    """

    def setUp(self):
        self.ipa_user = IPAUserFactory()
        self.member_state = self.ipa_user.member_state
        _login(self.client, self.ipa_user)

    def _post_json(self, payload):
        return self.client.post(
            _delete_endpoint(self.member_state),
            data=json.dumps(payload),
            content_type="application/json",
        )

    def test_deletes_incentives_brochure(self):
        self.member_state.incentives_brochure_pdf = "https://res.cloudinary.com/demo/raw/upload/incentives.pdf"
        self.member_state.save()

        response = self._post_json({"field": "incentives_brochure_pdf"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        self.member_state.refresh_from_db()
        self.assertEqual(self.member_state.incentives_brochure_pdf, "")

    def test_deletes_sector_profiles(self):
        self.member_state.sector_profiles_pdf = "https://res.cloudinary.com/demo/raw/upload/sectors.pdf"
        self.member_state.save()

        response = self._post_json({"field": "sector_profiles_pdf"})
        self.assertEqual(response.status_code, 200)
        self.member_state.refresh_from_db()
        self.assertEqual(self.member_state.sector_profiles_pdf, "")

    def test_deletes_investment_guide_and_doing_business(self):
        self.member_state.investment_guide_pdf = "https://res.cloudinary.com/demo/raw/upload/investment.pdf"
        self.member_state.doing_business_pdf = "https://res.cloudinary.com/demo/raw/upload/business.pdf"
        self.member_state.save()

        self._post_json({"field": "investment_guide_pdf"})
        self._post_json({"field": "doing_business_pdf"})
        self.member_state.refresh_from_db()
        self.assertEqual(self.member_state.investment_guide_pdf, "")
        self.assertEqual(self.member_state.doing_business_pdf, "")

    def test_deleting_already_empty_field_is_a_harmless_no_op(self):
        response = self._post_json({"field": "incentives_brochure_pdf"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])

    def test_rejects_unknown_field(self):
        response = self._post_json({"field": "not_a_real_field"})
        self.assertEqual(response.status_code, 400)

    def test_still_rejects_legal_framework_pdf(self):
        """legal_framework_pdf is intentionally out of scope for this fix."""
        response = self._post_json({"field": "legal_framework_pdf"})
        self.assertEqual(response.status_code, 400)

    def test_rejects_invalid_json_body(self):
        response = self.client.post(
            _delete_endpoint(self.member_state),
            data="not json",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_anonymous_cannot_delete(self):
        self.client.logout()
        response = self._post_json({"field": "incentives_brochure_pdf"})
        self.assertEqual(response.status_code, 302)

    def test_ipa_staff_without_edit_permission_gets_403(self):
        self.client.logout()
        analyst = IPAUserFactory(member_state=self.member_state, role="ipa_analyst")
        self.client.force_login(analyst.user)
        response = self._post_json({"field": "incentives_brochure_pdf"})
        self.assertEqual(response.status_code, 403)

    def test_cannot_delete_another_member_states_document(self):
        """A staff user can only clear their own member state's document."""
        other_state_user = IPAUserFactory()
        other_state_user.member_state.incentives_brochure_pdf = (
            "https://res.cloudinary.com/demo/raw/upload/other.pdf"
        )
        other_state_user.member_state.save()

        # self.ipa_user (logged in) deletes their OWN field only.
        self._post_json({"field": "incentives_brochure_pdf"})

        other_state_user.member_state.refresh_from_db()
        self.assertEqual(
            other_state_user.member_state.incentives_brochure_pdf,
            "https://res.cloudinary.com/demo/raw/upload/other.pdf",
        )
