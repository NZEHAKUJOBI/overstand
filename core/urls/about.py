from django.urls import path

from core.views import about

app_name = "about"

urlpatterns = [
    path("who-we-are/", about.WhoWeAreView.as_view(), name="who_we_are"),
    path(
        "mission-vision-values/",
        about.MissionVisionValuesView.as_view(),
        name="mission_vision_values",
    ),
    path(
        "strategic-priorities/",
        about.StrategicPrioritiesView.as_view(),
        name="strategic_priorities",
    ),
    path("governance/", about.GovernanceLeadershipView.as_view(), name="governance"),
    path(
        "ecowas-relationship/", about.ECOWASRelationshipView.as_view(), name="ecowas_relationship"
    ),
    path("contact/", about.ContactUsView.as_view(), name="contact"),
    path("afcfta/", about.AfCFTAView.as_view(), name="afcfta"),
    # ECOWAS Commission President
    path(
        "leadership/commission-president/", about.commission_president, name="commission_president"
    ),
    # ECOWAS Authority Chairman (Head of State)
    path("leadership/authority-chairman/", about.authority_chairman, name="authority_chairman"),
    # Commissioner for Economic Affairs and Agriculture
    path(
        "leadership/commissioner-economic-affairs/",
        about.commissioner_economic,
        name="commissioner_economic",
    ),
    # IPAWAS Secretary General
    path(
        "leadership/secretary-general/",
        about.secretary_general,
        name="secretary_general",
    ),
    path("privacy-policy/", about.PrivacyPolicyView.as_view(), name="privacy_policy"),
    path("terms-of-use/", about.TermsOfUseView.as_view(), name="terms_of_use"),
]
