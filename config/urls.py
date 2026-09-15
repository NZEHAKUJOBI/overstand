from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from django.views.i18n import set_language

from core.sitemaps import sitemaps
from core.views.seo import robots_txt

# Custom error handlers — Django uses these when DEBUG=False
handler404 = "core.views.errors.handler404"
handler500 = "core.views.errors.handler500"
handler403 = "core.views.errors.handler403"

# Served at root (no language prefix) so crawlers always find them
urlpatterns = [
    path("i18n/setlang/", set_language, name="set_language"),
    path("robots.txt", robots_txt, name="robots_txt"),
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.sitemap",
    ),
]

urlpatterns += i18n_patterns(
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("accounts/", include("accounts.urls", namespace="accounts")),
    path("members/", include("members.urls")),
    path("dashboard/", include("dashboard.urls.urls")),
    path("training/", include("training.urls", namespace="training")),
    path("onboard/", include("onboarding.urls", namespace="onboarding")),
    path("join/", include("onboarding.join_urls")),
)
