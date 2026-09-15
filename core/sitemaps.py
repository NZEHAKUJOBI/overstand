from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from members.models import MemberStateIPA
from opportunities.models import InvestmentOpportunity


class StaticViewSitemap(Sitemap):
    """High-value static pages — home, about, invest, services, media."""

    changefreq = "monthly"
    priority = 0.7
    i18n = True
    alternates = True
    x_default = True

    def items(self):
        return [
            # Home
            "home",
            # About
            "about:who_we_are",
            "about:mission_vision_values",
            "about:strategic_priorities",
            "about:governance",
            "about:ecowas_relationship",
            "about:contact",
            "about:afcfta",
            "about:privacy_policy",
            "about:terms_of_use",
            # Why West Africa
            "why_west_africa:hub",
            "why_west_africa:investment-case",
            "why_west_africa:incentives",
            "why_west_africa:success-stories",
            "why_west_africa:agriculture-sector",
            "why_west_africa:energy-sector",
            "why_west_africa:ict-sector",
            "why_west_africa:mining-sector",
            "why_west_africa:tourism-sector",
            # Opportunities listing
            "opportunities:listing",
            # Investor Services
            "investor_services:hub",
            "investor_services:advisory",
            "investor_services:ipa_connection",
            "investor_services:toolkit",
            "investor_services:resources",
            "investor_services:site_visits",
            # Knowledge Hub
            "knowledge_hub:hub",
            "knowledge_hub:publications",
            "knowledge_hub:news",
            "knowledge_hub:resources",
            # Media Centre
            "media_center:hub",
            "media_center:press_releases",
            "media_center:photo_gallery",
            "media_center:video_library",
            "media_center:media_kit",
            # Members hub
            "members:hub",
        ]

    def location(self, item):
        return reverse(item)


class OpportunitySitemap(Sitemap):
    """All published/active investment opportunities."""

    changefreq = "weekly"
    priority = 0.9
    i18n = True
    alternates = True
    x_default = True

    def items(self):
        return InvestmentOpportunity.objects.filter(
            published=True, status="active"
        ).order_by("-updated_at")

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse("opportunities:detail", kwargs={"slug": obj.slug})


class MemberStateSitemap(Sitemap):
    """All 12 active member state profile pages."""

    changefreq = "monthly"
    priority = 0.8
    i18n = True
    alternates = True
    x_default = True

    def items(self):
        return MemberStateIPA.objects.filter(is_active=True).order_by("country_name")

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse("members:detail", kwargs={"country_slug": obj.slug})


sitemaps = {
    "static": StaticViewSitemap,
    "opportunities": OpportunitySitemap,
    "members": MemberStateSitemap,
}
