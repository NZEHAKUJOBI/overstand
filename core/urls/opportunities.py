from django.urls import path

from core.views import opportunities as views

app_name = "opportunities"

urlpatterns = [
    # Main listing page
    path("", views.OpportunityListView.as_view(), name="listing"),
    # Opportunity detail
    path("<slug:slug>/", views.OpportunityDetailView.as_view(), name="detail"),
    # AJAX endpoints
    path("ajax/express-interest/", views.express_interest_ajax, name="express_interest_ajax"),
]
