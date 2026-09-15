from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required(login_url="accounts:login")
def help_index(request):
    return render(request, "dashboard/help/index.html")


@login_required(login_url="accounts:login")
def getting_started(request):
    return render(request, "dashboard/help/getting_started.html")


@login_required(login_url="accounts:login")
def hq_dashboard_guide(request):
    return render(request, "dashboard/help/hq_dashboard.html")


@login_required(login_url="accounts:login")
def ipa_dashboard_guide(request):
    return render(request, "dashboard/help/ipa_dashboard.html")


@login_required(login_url="accounts:login")
def quick_reference(request):
    return render(request, "dashboard/help/quick_reference.html")


@login_required(login_url="accounts:login")
def roles_permissions(request):
    return render(request, "dashboard/help/roles.html")
