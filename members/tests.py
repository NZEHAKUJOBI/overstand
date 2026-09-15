from django.test import TestCase
from django.urls import reverse

from dashboard.tests.factories import MemberStateIPAFactory
from media_app.models import MediaFile, MediaFolder
from members.models import InvestmentIncentive

# Create your tests here.


class MemberStateDetailDownloadResourcesTests(TestCase):
    """
    The public "Download Resources" widget (members/templates/members/detail.html)
    must link to the actual uploaded PDF URLs and never render a dead '#'
    placeholder link — that placeholder was the root cause of a reported bug
    where the 4 resource links were not clickable.
    """

    def _url(self, member_state):
        return reverse("members:detail", kwargs={"country_slug": member_state.slug})

    def _download_widget(self, content):
        """
        Isolate just the Download Resources widget's markup. The wider page
        (nav dropdowns, modals, etc. from the shared base template) legitimately
        uses href="#" elsewhere, so assertions must not scan the whole page.
        """
        start = content.index('<ul class="download-list">')
        end = content.index("</ul>", start)
        return content[start:end]

    def test_all_four_links_render_when_all_pdfs_uploaded(self):
        ms = MemberStateIPAFactory(
            investment_guide_pdf="https://res.cloudinary.com/test/investment.pdf",
            incentives_brochure_pdf="https://res.cloudinary.com/test/incentives.pdf",
            doing_business_pdf="https://res.cloudinary.com/test/business.pdf",
            sector_profiles_pdf="https://res.cloudinary.com/test/sectors.pdf",
        )
        response = self.client.get(self._url(ms))
        self.assertEqual(response.status_code, 200)
        widget = self._download_widget(response.content.decode())

        self.assertIn('href="https://res.cloudinary.com/test/investment.pdf"', widget)
        self.assertIn('href="https://res.cloudinary.com/test/incentives.pdf"', widget)
        self.assertIn('href="https://res.cloudinary.com/test/business.pdf"', widget)
        self.assertIn('href="https://res.cloudinary.com/test/sectors.pdf"', widget)
        self.assertNotIn('href="#"', widget)

    def test_disabled_state_when_no_pdfs_uploaded(self):
        ms = MemberStateIPAFactory()
        response = self.client.get(self._url(ms))
        self.assertEqual(response.status_code, 200)
        widget = self._download_widget(response.content.decode())

        self.assertNotIn('href="#"', widget)
        self.assertIn("download-link disabled", widget)
        # All 4 items should show the disabled "Not yet available" placeholder.
        self.assertEqual(widget.count("Not yet available"), 4)

    def test_partial_upload_mixes_live_and_disabled_links(self):
        ms = MemberStateIPAFactory(
            investment_guide_pdf="https://res.cloudinary.com/test/investment.pdf",
        )
        response = self.client.get(self._url(ms))
        self.assertEqual(response.status_code, 200)
        widget = self._download_widget(response.content.decode())

        self.assertIn('href="https://res.cloudinary.com/test/investment.pdf"', widget)
        self.assertNotIn('href="#"', widget)
        # The other 3 documents are still unset, so they stay disabled.
        self.assertEqual(widget.count("Not yet available"), 3)


class MemberStateDetailEconomicDownloadBannerTests(TestCase):
    """
    Regression test for the Economic Data tab's "Download Economic Reports"
    banner. It previously reused the `.download-card` class name also used
    (for an unrelated small link-card component) by the Overview and
    Leadership tabs. Because IPAWAS renders every tab into one page and only
    toggles visibility with CSS, that collision let an unrelated
    `.download-card:hover` rule make this banner's white text unreadable on
    hover, and an unrelated `.download-card i:first-child` rule paint its
    button icons red instead of the platform's own colors.
    """

    def _url(self, member_state):
        return reverse("members:detail", kwargs={"country_slug": member_state.slug})

    def _download_buttons(self, content):
        start = content.index('<div class="download-buttons">')
        end = content.index("</div>", start)
        return content[start:end]

    def test_banner_uses_its_own_unique_class_not_download_card(self):
        ms = MemberStateIPAFactory()
        content = self.client.get(self._url(ms)).content.decode()
        self.assertIn('class="economic-download-banner"', content)
        self.assertNotIn('<div class="download-card">', content)

    def test_buttons_use_branded_classes_not_bootstrap_defaults(self):
        ms = MemberStateIPAFactory(
            investment_guide_pdf="https://res.cloudinary.com/test/investment.pdf",
        )
        content = self.client.get(self._url(ms)).content.decode()
        buttons = self._download_buttons(content)

        self.assertIn("economic-download-btn-primary", buttons)
        self.assertIn("economic-download-btn-outline", buttons)
        self.assertNotIn('"btn btn-primary"', buttons)
        self.assertNotIn('"btn btn-outline-primary"', buttons)


class MemberStateDetailIncentiveSupportingDocumentTests(TestCase):
    """
    Regression test: an incentive's uploaded supporting document never
    rendered anywhere on the public country page. The model already tracked
    it (via document_url/document_name for a direct upload, or document_file
    for a media-library pick, unified by resolved_document_url/
    resolved_document_name) — members/templates/members/tabs/incentives.html
    just never referenced it.
    """

    def _url(self, member_state):
        return reverse("members:detail", kwargs={"country_slug": member_state.slug})

    def test_direct_upload_document_link_renders(self):
        ms = MemberStateIPAFactory()
        InvestmentIncentive.objects.create(
            member_state=ms,
            title="5-Year Tax Holiday",
            incentive_type="tax_holiday",
            description="Full corporate tax exemption for qualifying investors.",
            document_url="https://res.cloudinary.com/demo/raw/upload/guidelines.pdf",
            document_name="application-guidelines-for-economic-development-tax-incentive.pdf",
            is_active=True,
        )
        content = self.client.get(self._url(ms)).content.decode()
        self.assertIn('href="https://res.cloudinary.com/demo/raw/upload/guidelines.pdf"', content)
        self.assertIn("application-guidelines-for-economic-development-tax-incentive.pdf", content)

    def test_media_library_document_link_resolves_via_file(self):
        ms = MemberStateIPAFactory()
        folder = MediaFolder.objects.create(member_state=ms, name="Documents", slug="documents")
        media_file = MediaFile.objects.create(
            member_state=ms,
            folder=folder,
            name="Incentives Guide.pdf",
            original_filename="incentives-guide.pdf",
            file_type="document",
            mime_type="application/pdf",
            size_bytes=12345,
            cloudinary_public_id="ipawas/test/incentives-guide",
            cloudinary_resource_type="raw",
            cloudinary_url="http://res.cloudinary.com/demo/raw/upload/incentives-guide.pdf",
            cloudinary_secure_url="https://res.cloudinary.com/demo/raw/upload/incentives-guide.pdf",
        )
        InvestmentIncentive.objects.create(
            member_state=ms,
            title="VAT Exemption",
            incentive_type="vat_exemption",
            description="Full VAT exemption on qualifying capital equipment.",
            document_file=media_file,
            is_active=True,
        )
        content = self.client.get(self._url(ms)).content.decode()
        self.assertIn('href="https://res.cloudinary.com/demo/raw/upload/incentives-guide.pdf"', content)
        self.assertIn("Incentives Guide.pdf", content)

    def test_no_document_renders_no_supporting_document_section(self):
        ms = MemberStateIPAFactory()
        InvestmentIncentive.objects.create(
            member_state=ms,
            title="Capital Allowance",
            incentive_type="capital_allowance",
            description="Accelerated depreciation on qualifying capital expenditure.",
            is_active=True,
        )
        content = self.client.get(self._url(ms)).content.decode()
        self.assertNotIn("Supporting Document:", content)

    def test_inactive_incentive_not_shown_at_all(self):
        """Sanity check: inactive incentives (and their documents) stay hidden."""
        ms = MemberStateIPAFactory()
        InvestmentIncentive.objects.create(
            member_state=ms,
            title="Draft Incentive",
            incentive_type="other",
            description="Not ready for publication yet.",
            document_url="https://res.cloudinary.com/demo/raw/upload/draft.pdf",
            document_name="draft.pdf",
            is_active=False,
        )
        content = self.client.get(self._url(ms)).content.decode()
        self.assertNotIn("Draft Incentive", content)
        self.assertNotIn("draft.pdf", content)
