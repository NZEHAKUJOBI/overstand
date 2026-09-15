from django.urls import path

from . import views

urlpatterns = [
    # IPAWAS Home
    path("", views.ipawas_home, name="ipawas_home"),
    # IPAWAS about section
    path("about/mission/", views.about_mission, name="about_mission"),
    path("about/our-story", views.about_our_story, name="about_our_story"),
    path("about/leadership", views.about_leadership, name="about_leadership"),
    path(
        "about/partnerships",
        views.about_strategy_patnerships,
        name="about_strategy_patnerships",
    ),
    # about section
    path(
        "invest/regional-overview/",
        views.invest_regional_overview,
        name="invest_regional_overview",
    ),
    path("invest/sectors", views.invest_sectors, name="invest_sectors"),
    path("invest/countries", views.invest_countries, name="invest_countries"),
    path("invest/process", views.invest_process, name="invest_process"),
    path(
        "invest/success-stories",
        views.invest_success_stories,
        name="invest_success_stories",
    ),
    # members section
    path(
        "members/directory/",
        views.members_directory,
        name="members_directory",
    ),
    path("members/benefits/", views.members_benefits, name="members_benefits"),
    path("members/join", views.members_join, name="members_join"),
    path("members/portal", views.members_portal, name="members_portal"),
]
