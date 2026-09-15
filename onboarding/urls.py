"""
Onboarding public URLs.
These are accessible without authentication — anyone with the QR code can reach them.
"""

from django.urls import path

from onboarding import views

app_name = "onboarding"

urlpatterns = [
    path("<uuid:session_token>/", views.OnboardingFormView.as_view(), name="form"),
    path("<uuid:session_token>/success/", views.OnboardingSuccessView.as_view(), name="success"),
]
