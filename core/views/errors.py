"""
Custom error handlers for IPAWAS.

Django calls these view functions when DEBUG=False and an HTTP error occurs.
They render branded, user-friendly error pages instead of plain Django defaults.
"""

from django.shortcuts import render


def handler404(request, exception=None):
    """Render the custom 404 — Page Not Found page."""
    return render(request, "404.html", status=404)


def handler500(request):
    """
    Render the custom 500 — Internal Server Error page.

    NOTE: This handler must NOT rely on anything that could itself raise
    an exception (e.g. complex context processors).  Keep it simple.
    """
    return render(request, "500.html", status=500)


def handler403(request, exception=None):
    """Render the custom 403 — Permission Denied page."""
    return render(request, "403.html", status=403)
