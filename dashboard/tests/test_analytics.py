"""Tests for dashboard/views/members/analytics.py"""

import csv
import io
import json
from datetime import timedelta

from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from dashboard.tests.factories import (
    InvestmentOpportunityFactory,
    InvestorInquiryFactory,
    IPAUserFactory,
    MemberStateIPAFactory,
    SectorFactory,
)
from dashboard.views.members.analytics import VALID_RANGES, _parse_range
from members.models import InvestorInquiry


# ── Helpers ──────────────────────────────────────────────────────────────────


def _analytics_url(slug):
    return reverse("dashboard:country:analytics", kwargs={"member_state_slug": slug})


def _export_url(slug, **params):
    url = reverse("dashboard:country:analytics_export", kwargs={"member_state_slug": slug})
    if params:
        url += "?" + "&".join(f"{k}={v}" for k, v in params.items())
    return url


# ── _parse_range unit tests ───────────────────────────────────────────────────


class ParseRangeTests(TestCase):
    def _req(self, qs=""):
        return RequestFactory().get(f"/?{qs}")

    def test_valid_ranges_returned_as_is(self):
        for r in VALID_RANGES:
            self.assertEqual(_parse_range(self._req(f"range={r}")), r)

    def test_invalid_integer_defaults_to_30(self):
        self.assertEqual(_parse_range(self._req("range=999")), 30)

    def test_non_numeric_defaults_to_30(self):
        self.assertEqual(_parse_range(self._req("range=abc")), 30)

    def test_missing_param_defaults_to_30(self):
        self.assertEqual(_parse_range(self._req()), 30)

    def test_zero_defaults_to_30(self):
        self.assertEqual(_parse_range(self._req("range=0")), 30)

    def test_negative_defaults_to_30(self):
        self.assertEqual(_parse_range(self._req("range=-7")), 30)


# ── AnalyticsView tests ───────────────────────────────────────────────────────


@override_settings(ALLOWED_HOSTS=["*"])
class AnalyticsViewTests(TestCase):
    def setUp(self):
        self.member_state = MemberStateIPAFactory()
        self.ipa_user = IPAUserFactory(member_state=self.member_state)
        self.url = _analytics_url(self.member_state.slug)

    # ── Auth ─────────────────────────────────────────────────────────────

    def test_unauthenticated_redirects_to_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response["Location"])

    def test_authenticated_ipa_staff_gets_200(self):
        self.client.force_login(self.ipa_user.user)
        self.assertEqual(self.client.get(self.url).status_code, 200)

    # ── Date range ───────────────────────────────────────────────────────

    def test_default_range_is_30(self):
        self.client.force_login(self.ipa_user.user)
        ctx = self.client.get(self.url).context
        self.assertEqual(ctx["selected_range"], 30)

    def test_all_valid_range_params_are_honoured(self):
        self.client.force_login(self.ipa_user.user)
        for days in VALID_RANGES:
            ctx = self.client.get(self.url + f"?range={days}").context
            self.assertEqual(ctx["selected_range"], days, f"range={days} not honoured")

    def test_invalid_range_param_falls_back_to_30(self):
        self.client.force_login(self.ipa_user.user)
        ctx = self.client.get(self.url + "?range=999").context
        self.assertEqual(ctx["selected_range"], 30)

    def test_range_label_matches_selected_range(self):
        self.client.force_login(self.ipa_user.user)
        ctx = self.client.get(self.url + "?range=7").context
        self.assertEqual(ctx["range_label"], "Last 7 Days")

    # ── Required context keys ────────────────────────────────────────────

    def test_all_required_context_keys_present(self):
        self.client.force_login(self.ipa_user.user)
        ctx = self.client.get(self.url).context
        for key in (
            "selected_range", "range_label",
            "published_opportunities", "total_opportunities",
            "total_views", "total_downloads",
            "total_inquiries", "period_inquiries", "new_inquiries",
            "active_team_members",
            "status_labels_json", "status_counts_json", "status_colors_json",
            "status_total", "status_breakdown",
            "top_opportunities", "top_countries",
            "chart_labels_json", "chart_values_json",
            "inquiry_trend_pct", "inquiry_trend_up",
        ):
            self.assertIn(key, ctx, f"Context key '{key}' missing")

    # ── Zero-data state ──────────────────────────────────────────────────

    def test_all_counts_zero_when_no_data(self):
        self.client.force_login(self.ipa_user.user)
        ctx = self.client.get(self.url).context
        self.assertEqual(ctx["published_opportunities"], 0)
        self.assertEqual(ctx["total_opportunities"], 0)
        self.assertEqual(ctx["total_inquiries"], 0)
        self.assertEqual(ctx["status_total"], 0)
        self.assertIsNone(ctx["inquiry_trend_pct"])

    # ── Opportunity counts ───────────────────────────────────────────────

    def test_published_opportunity_counted_in_both_totals(self):
        InvestmentOpportunityFactory(primary_country=self.member_state, published=True)
        self.client.force_login(self.ipa_user.user)
        ctx = self.client.get(self.url).context
        self.assertEqual(ctx["published_opportunities"], 1)
        self.assertEqual(ctx["total_opportunities"], 1)

    def test_draft_opportunity_only_in_total_not_published(self):
        InvestmentOpportunityFactory(primary_country=self.member_state, published=False)
        self.client.force_login(self.ipa_user.user)
        ctx = self.client.get(self.url).context
        self.assertEqual(ctx["published_opportunities"], 0)
        self.assertEqual(ctx["total_opportunities"], 1)

    def test_other_state_opportunities_not_counted(self):
        other = MemberStateIPAFactory()
        InvestmentOpportunityFactory(primary_country=other, published=True)
        self.client.force_login(self.ipa_user.user)
        ctx = self.client.get(self.url).context
        self.assertEqual(ctx["total_opportunities"], 0)

    # ── Inquiry counts ───────────────────────────────────────────────────

    def test_inquiries_counted_correctly(self):
        InvestorInquiryFactory(member_state=self.member_state, status="new")
        InvestorInquiryFactory(member_state=self.member_state, status="responded")
        self.client.force_login(self.ipa_user.user)
        ctx = self.client.get(self.url).context
        self.assertEqual(ctx["total_inquiries"], 2)
        self.assertEqual(ctx["new_inquiries"], 1)
        self.assertEqual(ctx["status_total"], 2)

    def test_other_state_inquiries_not_visible(self):
        other = MemberStateIPAFactory()
        InvestorInquiryFactory(member_state=other)
        self.client.force_login(self.ipa_user.user)
        ctx = self.client.get(self.url).context
        self.assertEqual(ctx["total_inquiries"], 0)

    def test_inquiry_trend_none_when_no_previous_period_data(self):
        # Current period has inquiries but previous period has none → pct is None
        InvestorInquiryFactory.create_batch(2, member_state=self.member_state)
        self.client.force_login(self.ipa_user.user)
        ctx = self.client.get(self.url + "?range=7").context
        self.assertIsNone(ctx["inquiry_trend_pct"])

    def test_inquiry_trend_positive_when_current_exceeds_previous(self):
        now = timezone.now()
        # 1 inquiry in the previous period (15 days ago, range=7)
        old = InvestorInquiryFactory(member_state=self.member_state)
        InvestorInquiry.objects.filter(pk=old.pk).update(
            created_at=now - timedelta(days=10)
        )
        # 3 inquiries in the current 7-day period
        InvestorInquiryFactory.create_batch(3, member_state=self.member_state)
        self.client.force_login(self.ipa_user.user)
        ctx = self.client.get(self.url + "?range=7").context
        self.assertIsNotNone(ctx["inquiry_trend_pct"])
        self.assertTrue(ctx["inquiry_trend_up"])
        self.assertEqual(ctx["inquiry_trend_pct"], 200)  # (3-1)/1 * 100

    def test_inquiry_trend_negative_when_current_below_previous(self):
        now = timezone.now()
        # 4 inquiries in previous period
        for _ in range(4):
            inq = InvestorInquiryFactory(member_state=self.member_state)
            InvestorInquiry.objects.filter(pk=inq.pk).update(
                created_at=now - timedelta(days=10)
            )
        # 2 inquiries in current 7-day period
        InvestorInquiryFactory.create_batch(2, member_state=self.member_state)
        self.client.force_login(self.ipa_user.user)
        ctx = self.client.get(self.url + "?range=7").context
        self.assertIsNotNone(ctx["inquiry_trend_pct"])
        self.assertFalse(ctx["inquiry_trend_up"])
        self.assertEqual(ctx["inquiry_trend_pct"], -50)  # (2-4)/4 * 100

    # ── Status breakdown ─────────────────────────────────────────────────

    def test_status_breakdown_uses_correct_status_keys(self):
        InvestorInquiryFactory(member_state=self.member_state, status="new")
        InvestorInquiryFactory(member_state=self.member_state, status="in_progress")
        InvestorInquiryFactory(member_state=self.member_state, status="responded")
        InvestorInquiryFactory(member_state=self.member_state, status="closed")
        self.client.force_login(self.ipa_user.user)
        ctx = self.client.get(self.url).context
        counts = json.loads(ctx["status_counts_json"])
        labels = json.loads(ctx["status_labels_json"])
        # All four statuses should be represented
        self.assertIn("New", labels)
        self.assertIn("In Progress", labels)
        self.assertIn("Responded", labels)
        self.assertIn("Closed", labels)
        # Each should have count 1
        for count in counts:
            self.assertEqual(count, 1)

    # ── Country breakdown ────────────────────────────────────────────────

    def test_country_breakdown_shows_correct_countries(self):
        InvestorInquiryFactory(member_state=self.member_state, company_country="France")
        InvestorInquiryFactory(member_state=self.member_state, company_country="France")
        InvestorInquiryFactory(member_state=self.member_state, company_country="Germany")
        self.client.force_login(self.ipa_user.user)
        ctx = self.client.get(self.url).context
        countries = [c["company_country"] for c in ctx["top_countries"]]
        self.assertIn("France", countries)
        self.assertIn("Germany", countries)

    def test_country_pct_values_sum_to_approximately_100(self):
        InvestorInquiryFactory.create_batch(3, member_state=self.member_state, company_country="UK")
        InvestorInquiryFactory.create_batch(1, member_state=self.member_state, company_country="USA")
        self.client.force_login(self.ipa_user.user)
        ctx = self.client.get(self.url).context
        total_pct = sum(c["pct"] for c in ctx["top_countries"])
        self.assertAlmostEqual(total_pct, 100, delta=5)

    def test_blank_company_country_excluded_from_table(self):
        InvestorInquiryFactory(member_state=self.member_state, company_country="")
        self.client.force_login(self.ipa_user.user)
        ctx = self.client.get(self.url).context
        self.assertEqual(len(ctx["top_countries"]), 0)

    # ── Top opportunities ────────────────────────────────────────────────

    def test_top_opportunities_sorted_by_inquiry_count(self):
        sector = SectorFactory()
        opp_low = InvestmentOpportunityFactory(
            primary_country=self.member_state, published=True,
            primary_sector=sector,
        )
        opp_high = InvestmentOpportunityFactory(
            primary_country=self.member_state, published=True,
            primary_sector=sector,
        )
        from opportunities.models import InvestmentOpportunity
        InvestmentOpportunity.objects.filter(pk=opp_high.pk).update(inquiries_count=5)
        InvestmentOpportunity.objects.filter(pk=opp_low.pk).update(inquiries_count=1)
        self.client.force_login(self.ipa_user.user)
        ctx = self.client.get(self.url).context
        top = ctx["top_opportunities"]
        self.assertEqual(top[0].pk, opp_high.pk)

    def test_top_opportunity_engagement_rate_is_100_for_leader(self):
        sector = SectorFactory()
        opp = InvestmentOpportunityFactory(
            primary_country=self.member_state, published=True, primary_sector=sector,
        )
        from opportunities.models import InvestmentOpportunity
        InvestmentOpportunity.objects.filter(pk=opp.pk).update(inquiries_count=10)
        self.client.force_login(self.ipa_user.user)
        ctx = self.client.get(self.url).context
        self.assertEqual(ctx["top_opportunities"][0].engagement_rate, 100)

    def test_unpublished_opps_excluded_from_top_opportunities(self):
        sector = SectorFactory()
        InvestmentOpportunityFactory(
            primary_country=self.member_state, published=False, primary_sector=sector,
        )
        self.client.force_login(self.ipa_user.user)
        ctx = self.client.get(self.url).context
        self.assertEqual(len(ctx["top_opportunities"]), 0)

    # ── Trend chart label counts ─────────────────────────────────────────

    def test_chart_has_7_labels_for_range_7(self):
        self.client.force_login(self.ipa_user.user)
        labels = json.loads(self.client.get(self.url + "?range=7").context["chart_labels_json"])
        self.assertEqual(len(labels), 7)

    def test_chart_has_30_labels_for_range_30(self):
        self.client.force_login(self.ipa_user.user)
        labels = json.loads(self.client.get(self.url + "?range=30").context["chart_labels_json"])
        self.assertEqual(len(labels), 30)

    def test_chart_has_13_labels_for_range_90(self):
        self.client.force_login(self.ipa_user.user)
        labels = json.loads(self.client.get(self.url + "?range=90").context["chart_labels_json"])
        self.assertEqual(len(labels), 13)

    def test_chart_has_12_labels_for_range_365(self):
        self.client.force_login(self.ipa_user.user)
        labels = json.loads(self.client.get(self.url + "?range=365").context["chart_labels_json"])
        self.assertEqual(len(labels), 12)

    def test_chart_values_count_matches_labels_count(self):
        self.client.force_login(self.ipa_user.user)
        for days in VALID_RANGES:
            ctx = self.client.get(self.url + f"?range={days}").context
            labels = json.loads(ctx["chart_labels_json"])
            values = json.loads(ctx["chart_values_json"])
            self.assertEqual(len(labels), len(values), f"Mismatch for range={days}")


# ── AnalyticsExportView tests ─────────────────────────────────────────────────


@override_settings(ALLOWED_HOSTS=["*"])
class AnalyticsExportViewTests(TestCase):
    def setUp(self):
        self.member_state = MemberStateIPAFactory()
        self.ipa_user = IPAUserFactory(member_state=self.member_state)

    def _csv_rows(self, url):
        self.client.force_login(self.ipa_user.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        return list(csv.reader(io.StringIO(response.content.decode("utf-8"))))

    def _flat(self, rows):
        return " ".join(" ".join(r) for r in rows if r)

    # ── Auth ──────────────────────────────────────────────────────────────

    def test_unauthenticated_redirects_to_login(self):
        response = self.client.get(_export_url(self.member_state.slug, type="summary"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response["Location"])

    # ── Response headers ─────────────────────────────────────────────────

    def test_response_content_type_is_csv(self):
        self.client.force_login(self.ipa_user.user)
        response = self.client.get(_export_url(self.member_state.slug, type="summary"))
        self.assertIn("text/csv", response["Content-Type"])

    def test_response_is_attachment_with_csv_extension(self):
        self.client.force_login(self.ipa_user.user)
        response = self.client.get(_export_url(self.member_state.slug, type="summary"))
        disp = response["Content-Disposition"]
        self.assertIn("attachment", disp)
        self.assertIn(".csv", disp)

    def test_filename_contains_member_state_slug(self):
        self.client.force_login(self.ipa_user.user)
        response = self.client.get(_export_url(self.member_state.slug, type="summary"))
        self.assertIn(self.member_state.slug, response["Content-Disposition"])

    # ── Summary CSV ───────────────────────────────────────────────────────

    def test_summary_csv_contains_section_headers(self):
        rows = self._csv_rows(_export_url(self.member_state.slug, type="summary"))
        flat = self._flat(rows)
        self.assertIn("OPPORTUNITIES", flat)
        self.assertIn("INQUIRIES", flat)
        self.assertIn("TOP OPPORTUNITIES", flat)

    def test_summary_csv_contains_member_state_name(self):
        rows = self._csv_rows(_export_url(self.member_state.slug, type="summary"))
        self.assertIn(self.member_state.ipa_full_name, self._flat(rows))

    def test_unknown_type_defaults_to_summary(self):
        rows = self._csv_rows(_export_url(self.member_state.slug, type="nonsense"))
        self.assertIn("OPPORTUNITIES", self._flat(rows))

    def test_summary_reflects_correct_opportunity_counts(self):
        InvestmentOpportunityFactory(primary_country=self.member_state, published=True)
        InvestmentOpportunityFactory(primary_country=self.member_state, published=False)
        rows = self._csv_rows(_export_url(self.member_state.slug, type="summary"))
        flat = self._flat(rows)
        self.assertIn("Total Opportunities", flat)
        self.assertIn("Published Opportunities", flat)

    def test_summary_reflects_correct_inquiry_counts(self):
        InvestorInquiryFactory(member_state=self.member_state, status="new")
        InvestorInquiryFactory(member_state=self.member_state, status="responded")
        rows = self._csv_rows(_export_url(self.member_state.slug, type="summary"))
        flat = self._flat(rows)
        self.assertIn("Total Inquiries", flat)

    # ── Inquiries CSV ──────────────────────────────────────────────────────

    def test_inquiries_csv_has_expected_column_headers(self):
        rows = self._csv_rows(_export_url(self.member_state.slug, type="inquiries", range=365))
        header = next((r for r in rows if r and r[0] == "Reference"), None)
        self.assertIsNotNone(header, "Header row not found")
        self.assertIn("Status", header)
        self.assertIn("Country", header)
        self.assertIn("Email", header)

    def test_inquiries_csv_includes_inquiries_in_period(self):
        InvestorInquiryFactory(
            member_state=self.member_state,
            full_name="Alice Investor",
            company_country="Canada",
        )
        rows = self._csv_rows(_export_url(self.member_state.slug, type="inquiries", range=365))
        flat = self._flat(rows)
        self.assertIn("Alice Investor", flat)
        self.assertIn("Canada", flat)

    def test_inquiries_csv_excludes_other_member_state(self):
        other = MemberStateIPAFactory()
        InvestorInquiryFactory(member_state=other, full_name="Eve Attacker")
        rows = self._csv_rows(_export_url(self.member_state.slug, type="inquiries", range=365))
        self.assertNotIn("Eve Attacker", self._flat(rows))

    def test_inquiries_csv_respects_date_range(self):
        old = InvestorInquiryFactory(member_state=self.member_state, full_name="OldInvestor")
        InvestorInquiry.objects.filter(pk=old.pk).update(
            created_at=timezone.now() - timedelta(days=30)
        )
        rows = self._csv_rows(_export_url(self.member_state.slug, type="inquiries", range=7))
        self.assertNotIn("OldInvestor", self._flat(rows))

    def test_inquiries_csv_status_uses_display_value(self):
        InvestorInquiryFactory(member_state=self.member_state, status="in_progress")
        rows = self._csv_rows(_export_url(self.member_state.slug, type="inquiries", range=365))
        self.assertIn("In Progress", self._flat(rows))

    # ── Opportunities CSV ──────────────────────────────────────────────────

    def test_opportunities_csv_has_expected_column_headers(self):
        rows = self._csv_rows(_export_url(self.member_state.slug, type="opportunities"))
        header = next((r for r in rows if r and r[0] == "Reference"), None)
        self.assertIsNotNone(header, "Header row not found")
        self.assertIn("Title", header)
        self.assertIn("Published", header)
        self.assertIn("Views", header)

    def test_opportunities_csv_includes_own_opportunities(self):
        sector = SectorFactory()
        InvestmentOpportunityFactory(
            primary_country=self.member_state,
            primary_sector=sector,
            title="Special Mining Project",
            published=True,
        )
        rows = self._csv_rows(_export_url(self.member_state.slug, type="opportunities"))
        flat = self._flat(rows)
        self.assertIn("Special Mining Project", flat)
        self.assertIn("Yes", flat)

    def test_opportunities_csv_excludes_other_member_state(self):
        other = MemberStateIPAFactory()
        sector = SectorFactory()
        InvestmentOpportunityFactory(
            primary_country=other,
            primary_sector=sector,
            title="Secret Opportunity",
        )
        rows = self._csv_rows(_export_url(self.member_state.slug, type="opportunities"))
        self.assertNotIn("Secret Opportunity", self._flat(rows))

    def test_opportunities_csv_shows_no_for_unpublished(self):
        sector = SectorFactory()
        InvestmentOpportunityFactory(
            primary_country=self.member_state,
            primary_sector=sector,
            published=False,
        )
        rows = self._csv_rows(_export_url(self.member_state.slug, type="opportunities"))
        self.assertIn("No", self._flat(rows))
