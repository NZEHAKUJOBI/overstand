from django.urls import path

from onboarding.views import ShortLinkView

urlpatterns = [
    path("<str:short_code>/", ShortLinkView.as_view(), name="onboarding_join"),
]
