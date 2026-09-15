"""
Tests for MemberStateIPA model (apps/members/models.py).

Covers:
- New PDF URL fields added in migration 0005
- get_profile_completion() returns expected structure
- InvestorInquiry.reference_number auto-generation
- InvestorInquiry status lifecycle
- Slug uniqueness enforcement
"""

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from dashboard.tests.factories import InvestorInquiryFactory, MemberStateIPAFactory
from members.models import InvestorInquiry, MemberStateIPA


class MemberStateIPAPDFFieldTests(TestCase):
    """Verify the 4 new resource PDF URL fields are present and writable."""

    def setUp(self):
        self.member_state = MemberStateIPAFactory()

    def test_sector_profiles_pdf_field_exists(self):
        self.member_state.sector_profiles_pdf = "https://res.cloudinary.com/test/raw/upload/sector.pdf"
        self.member_state.save()
        self.member_state.refresh_from_db()
        self.assertEqual(
            self.member_state.sector_profiles_pdf,
            "https://res.cloudinary.com/test/raw/upload/sector.pdf",
        )

    def test_incentives_brochure_pdf_field_exists(self):
        self.member_state.incentives_brochure_pdf = "https://res.cloudinary.com/test/raw/upload/incentives.pdf"
        self.member_state.save()
        self.member_state.refresh_from_db()
        self.assertEqual(
            self.member_state.incentives_brochure_pdf,
            "https://res.cloudinary.com/test/raw/upload/incentives.pdf",
        )

    def test_legal_framework_pdf_field_exists(self):
        self.member_state.legal_framework_pdf = "https://res.cloudinary.com/test/raw/upload/legal.pdf"
        self.member_state.save()
        self.member_state.refresh_from_db()
        self.assertEqual(
            self.member_state.legal_framework_pdf,
            "https://res.cloudinary.com/test/raw/upload/legal.pdf",
        )

    def test_infrastructure_report_pdf_field_exists(self):
        self.member_state.infrastructure_report_pdf = "https://res.cloudinary.com/test/raw/upload/infra.pdf"
        self.member_state.save()
        self.member_state.refresh_from_db()
        self.assertEqual(
            self.member_state.infrastructure_report_pdf,
            "https://res.cloudinary.com/test/raw/upload/infra.pdf",
        )

    def test_pdf_fields_are_optional(self):
        """All 4 PDF fields default to empty string (blank=True)."""
        fresh = MemberStateIPAFactory()
        self.assertEqual(fresh.sector_profiles_pdf, "")
        self.assertEqual(fresh.incentives_brochure_pdf, "")
        self.assertEqual(fresh.legal_framework_pdf, "")
        self.assertEqual(fresh.infrastructure_report_pdf, "")

    def test_all_four_pdf_fields_can_be_set_together(self):
        self.member_state.sector_profiles_pdf = "https://example.com/sectors.pdf"
        self.member_state.incentives_brochure_pdf = "https://example.com/incentives.pdf"
        self.member_state.legal_framework_pdf = "https://example.com/legal.pdf"
        self.member_state.infrastructure_report_pdf = "https://example.com/infra.pdf"
        self.member_state.save()
        self.member_state.refresh_from_db()

        self.assertEqual(self.member_state.sector_profiles_pdf, "https://example.com/sectors.pdf")
        self.assertEqual(self.member_state.incentives_brochure_pdf, "https://example.com/incentives.pdf")
        self.assertEqual(self.member_state.legal_framework_pdf, "https://example.com/legal.pdf")
        self.assertEqual(self.member_state.infrastructure_report_pdf, "https://example.com/infra.pdf")


class MemberStateIPAProfileCompletionTests(TestCase):
    """get_profile_completion() must return the right structure."""

    def test_returns_dict_with_percentage_completed_total_items(self):
        ms = MemberStateIPAFactory()
        result = ms.get_profile_completion()

        self.assertIn("percentage", result)
        self.assertIn("completed", result)
        self.assertIn("total", result)
        self.assertIn("items", result)

    def test_percentage_is_integer_between_0_and_100(self):
        ms = MemberStateIPAFactory()
        result = ms.get_profile_completion()
        self.assertIsInstance(result["percentage"], int)
        self.assertGreaterEqual(result["percentage"], 0)
        self.assertLessEqual(result["percentage"], 100)

    def test_completed_does_not_exceed_total(self):
        ms = MemberStateIPAFactory()
        result = ms.get_profile_completion()
        self.assertLessEqual(result["completed"], result["total"])

    def test_items_is_a_list(self):
        ms = MemberStateIPAFactory()
        result = ms.get_profile_completion()
        self.assertIsInstance(result["items"], list)


class MemberStateIPAUniquenessTests(TestCase):
    """slug and country_code must be unique."""

    def test_slug_must_be_unique(self):
        MemberStateIPAFactory(slug="unique-slug", country_code="US1")
        with self.assertRaises(IntegrityError):
            MemberStateIPAFactory(slug="unique-slug", country_code="US2")

    def test_country_code_must_be_unique(self):
        MemberStateIPAFactory(slug="country-a", country_code="XYZ")
        with self.assertRaises(IntegrityError):
            MemberStateIPAFactory(slug="country-b", country_code="XYZ")


class InvestorInquiryTests(TestCase):
    """InvestorInquiry model behaviour."""

    def test_factory_creates_valid_inquiry(self):
        inquiry = InvestorInquiryFactory()
        self.assertIsNotNone(inquiry.pk)
        self.assertEqual(inquiry.status, "new")

    def test_reference_number_set_on_factory(self):
        inquiry = InvestorInquiryFactory()
        self.assertNotEqual(inquiry.reference_number, "")

    def test_status_transitions(self):
        inquiry = InvestorInquiryFactory(status="new")

        inquiry.status = "in_progress"
        inquiry.save()
        inquiry.refresh_from_db()
        self.assertEqual(inquiry.status, "in_progress")

        inquiry.status = "responded"
        inquiry.save()
        inquiry.refresh_from_db()
        self.assertEqual(inquiry.status, "responded")

        inquiry.status = "closed"
        inquiry.save()
        inquiry.refresh_from_db()
        self.assertEqual(inquiry.status, "closed")

    def test_internal_notes_default_empty(self):
        inquiry = InvestorInquiryFactory()
        self.assertEqual(inquiry.internal_notes, "")

    def test_prepend_note_pattern(self):
        """Verify the note prepend pattern used by InquiryAddNoteView."""
        inquiry = InvestorInquiryFactory()
        note1 = "[2025-01-01 10:00] Admin:\nFirst note\n\n"
        inquiry.internal_notes = note1 + (inquiry.internal_notes or "")
        inquiry.save()

        note2 = "[2025-01-02 11:00] Staff:\nSecond note\n\n"
        inquiry.internal_notes = note2 + (inquiry.internal_notes or "")
        inquiry.save()
        inquiry.refresh_from_db()

        # Most recent note should be first
        self.assertTrue(inquiry.internal_notes.startswith("[2025-01-02"))
        self.assertIn("First note", inquiry.internal_notes)
        self.assertIn("Second note", inquiry.internal_notes)

    def test_get_absolute_url_returns_string(self):
        inquiry = InvestorInquiryFactory()
        url = inquiry.get_absolute_url()
        self.assertIsInstance(url, str)
        self.assertTrue(url.startswith("/"))
