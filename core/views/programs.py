"""
IPAWAS Programs Section - Django Views
All views for programs and initiatives pages.

NOTE: The Program/ProgramCategory/Applicant/Faculty models have not been created yet.
      Views currently render with static context so the site stays functional.
      Once the models are added, replace the static dicts with ORM queries.
"""

from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods


def programs_hub(request):
    """
    Programs Hub - Main gateway to all IPAWAS programs
    URL: /programs/
    """
    context = {
        "programs": [],
        "categories": [],
        "featured_programs": [],
        "upcoming_programs": [],
        "page_title": "Programs & Initiatives",
    }
    return render(request, "core/programs/programs_hub.html", context)


def program_detail(request, slug):
    """
    Generic Program Detail
    URL: /programs/<slug>/
    """
    context = {"program": None, "slug": slug}
    return render(request, "programs/program_detail.html", context)


def ipa_leadership_academy(request):
    """
    IPA Leadership Academy
    URL: /programs/ipa-leadership-academy/
    """
    context = {
        "program": None,
        "modules": [
            {
                "number": 1,
                "title": "Strategic Leadership & Vision",
                "duration": "2 Weeks",
                "location": "Abuja, Nigeria",
                "topics": [
                    "Leadership in the 21st Century",
                    "Strategic Thinking & Planning",
                    "Change Management",
                    "Stakeholder Engagement",
                ],
                "activities": ["Case Studies", "Group Discussions", "Leadership Simulations"],
                "deliverables": "Strategic Vision Document",
            },
            {
                "number": 2,
                "title": "Investment Promotion Excellence",
                "duration": "3 Weeks",
                "location": "Accra, Ghana",
                "topics": [
                    "Modern Investment Promotion Techniques",
                    "Investor Targeting & Outreach",
                    "Project Packaging",
                    "FDI Trends Analysis",
                ],
                "activities": ["Workshops", "Site Visits", "Peer Learning"],
                "deliverables": "Investment Promotion Strategy",
            },
        ],
        "faculty": [],
        "key_stats": {
            "completion_rate": "96%",
            "satisfaction_score": "4.8/5.0",
            "career_advancement": "78%",
        },
    }
    return render(request, "programs/ipa_leadership_academy.html", context)


def investment_promotion_training(request):
    """
    Investment Promotion Training Workshops
    URL: /programs/investment-promotion-training/
    """
    context = {
        "program": None,
        "workshop_dates": [
            {"quarter": "Q1 2025", "location": "Abuja", "date": "March 15-19"},
            {"quarter": "Q2 2025", "location": "Dakar", "date": "June 10-14"},
            {"quarter": "Q3 2025", "location": "Accra", "date": "September 5-9"},
            {"quarter": "Q4 2025", "location": "Abidjan", "date": "November 18-22"},
        ],
    }
    return render(request, "programs/investment_promotion_training.html", context)


def regional_investment_missions(request):
    """
    Regional Investment Missions
    URL: /programs/regional-investment-missions/
    """
    context = {
        "program": None,
        "upcoming_missions": [
            {
                "title": "UAE - West Africa Investment Mission",
                "date": "June 2025",
                "countries": ["Nigeria", "Ghana", "Senegal"],
                "sectors": ["Renewable Energy", "Agriculture", "Infrastructure"],
                "expected_investors": 25,
            },
            {
                "title": "China - West Africa Manufacturing Mission",
                "date": "September 2025",
                "countries": ["Côte d'Ivoire", "Ghana", "Nigeria"],
                "sectors": ["Manufacturing", "Textiles", "Industrial Parks"],
                "expected_investors": 30,
            },
        ],
        "past_missions": [
            {
                "title": "US - West Africa Tech Investment Mission",
                "date": "March 2024",
                "investment_secured": "$1.2B",
                "projects": 15,
                "testimonial": {
                    "text": "The mission provided unprecedented access...",
                    "author": "John Smith",
                    "company": "TechVentures Inc.",
                },
            }
        ],
    }
    return render(request, "programs/regional_investment_missions.html", context)


def ipa_performance_benchmarking(request):
    """
    IPA Performance Benchmarking Program
    URL: /programs/ipa-performance-benchmarking/
    """
    context = {
        "program": None,
        "benchmark_categories": [
            {
                "name": "Institutional Capacity",
                "indicators": ["Staff Capacity", "Budget Allocation", "Technology Adoption"],
            },
            {
                "name": "Investment Promotion",
                "indicators": ["Investor Inquiries", "Projects Facilitated", "FDI Secured"],
            },
            {
                "name": "Aftercare Services",
                "indicators": ["Investor Retention", "Expansion Projects", "Satisfaction Rate"],
            },
        ],
        "participating_ipas": 15,
        "reports_published": "Annually",
    }
    return render(request, "programs/ipa_performance_benchmarking.html", context)


def research_publications_program(request):
    """
    Research & Publications Program
    URL: /programs/research-publications/
    """
    context = {
        "program": None,
        "research_areas": [
            "FDI Trends & Analysis",
            "Sector-Specific Investment Studies",
            "Policy & Regulatory Research",
            "Investment Climate Assessment",
            "Regional Integration Studies",
        ],
        "recent_publications": [
            {
                "title": "West Africa Investment Report 2024",
                "type": "Annual Report",
                "date": "December 2024",
                "pages": 150,
            },
            {
                "title": "Renewable Energy Investment in ECOWAS",
                "type": "Policy Brief",
                "date": "November 2024",
                "pages": 25,
            },
        ],
    }
    return render(request, "programs/research_publications.html", context)


@require_http_methods(["POST"])
def submit_application(request, program_slug):
    """
    Handle program application submissions.
    URL: /programs/<slug>/apply/

    TODO: implement once Program model and ProgramApplicationForm are created.
    Returns 503 honestly rather than silently failing or pretending to succeed.
    """
    return JsonResponse(
        {
            "status": "error",
            "message": (
                "Program applications are not yet open. "
                "Please contact the IPAWAS Secretariat directly at infodesk@ipawas.org."
            ),
        },
        status=503,
    )


@require_http_methods(["POST"])
def submit_program_proposal(request):
    """
    Handle program proposal submissions.
    URL: /programs/submit-proposal/

    TODO: implement once ProgramProposal model is created.
    Returns 503 honestly rather than silently pretending to save.
    """
    return JsonResponse(
        {
            "status": "error",
            "message": (
                "Online proposal submissions are not yet available. "
                "Please send your proposal directly to infodesk@ipawas.org."
            ),
        },
        status=503,
    )


def download_program_brochure(request, program_slug):
    """
    Download program brochure PDF.
    URL: /programs/<slug>/brochure/

    TODO: generate PDF once Program model and Cloudinary storage are wired up.
    Returns 404 rather than an empty file that silently corrupts in PDF readers.
    """
    from django.http import Http404
    raise Http404(
        f"No brochure is available for '{program_slug}' yet. "
        "Please contact infodesk@ipawas.org to request programme materials."
    )
