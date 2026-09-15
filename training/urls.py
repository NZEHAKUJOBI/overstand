from django.urls import path

from . import views

app_name = "training"

urlpatterns = [
    path("<uuid:token>/", views.AssessmentView.as_view(), name="assess"),
    path("<uuid:token>/done/", views.AssessmentSuccessView.as_view(), name="success"),
]
