from django.urls import include, path

from core.views import (
    MemberJoinView,
    MemberPortalView,
    index,
    membership_inquiry,
    newsletter_subscribe,
)

urlpatterns = [
    path("", index, name="home"),
    path("newsletter/subscribe/", newsletter_subscribe, name="newsletter_subscribe"),
    path("members/join/", MemberJoinView.as_view(), name="members_join"),
    path("members/portal/", MemberPortalView.as_view(), name="members_portal"),
    path("members/join/apply/", membership_inquiry, name="membership_inquiry"),
    path("about/", include(("core.urls.about", "about"), namespace="about")),
    path(
        "why-west-africa/",
        include(("core.urls.why_west_africa", "why_west_africa"), namespace="why_west_africa"),
    ),
    path(
        "opportunities/",
        include(("core.urls.opportunities", "opportunities"), namespace="opportunities"),
    ),
    path(
        "investor-services/",
        include(
            ("core.urls.investor_services", "investor_services"), namespace="investor_services"
        ),
    ),
    path(
        "knowledge-hub/",
        include(
            ("core.urls.knowledge_hub", "knowledge_hub"),
            namespace="knowledge_hub",
        ),
    ),
    path(
        "media-center/",
        include(("core.urls.media_center", "media_center"), namespace="media_center"),
    ),
    path(
        "programs/",
        include(("core.urls.programs", "programs"), namespace="programs"),
    ),
]
