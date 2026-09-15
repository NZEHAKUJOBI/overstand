"""
Investment Opportunities Views - CORRECTED for existing schema

This works with YOUR existing InvestmentOpportunity and InvestorInquiry models.
Place this in: opportunities/views.py
"""

import json
import logging

from django.core.paginator import Paginator
from django.db import models
from django.db.models import Prefetch, Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.generic import DetailView, ListView

from django_ratelimit.decorators import ratelimit

from core.forms import InvestorInquiryForm
from core.models import Sector
from members.models import InvestorInquiry, MemberStateIPA
from opportunities.models import InvestmentOpportunity

logger = logging.getLogger(__name__)


class OpportunityListView(ListView):
    """
    Investment opportunities listing with filters, search, and pagination.
    Works with existing InvestmentOpportunity model.
    """

    model = InvestmentOpportunity
    template_name = "core/opportunities/listing.html"
    context_object_name = "opportunities"
    paginate_by = 12

    def get_queryset(self):
        queryset = (
            InvestmentOpportunity.objects.filter(published=True, status="active")
            .select_related("primary_country", "primary_sector")
            .prefetch_related("secondary_sectors")
        )

        # Search
        search = self.request.GET.get("search", "").strip()
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search)
                | Q(description__icontains=search)
                | Q(summary__icontains=search)
                | Q(reference_number__icontains=search)
            )

        # Country filter
        country = self.request.GET.get("country")
        if country:
            queryset = queryset.filter(primary_country__slug=country)

        # Sector filter
        sector = self.request.GET.get("sector")
        if sector:
            queryset = queryset.filter(
                Q(primary_sector__slug=sector) | Q(secondary_sectors__slug=sector)
            ).distinct()

        # Investment size filter (based on investment_required_min)
        size = self.request.GET.get("size")
        if size:
            if size == "micro":
                queryset = queryset.filter(investment_required_min__lt=100000)
            elif size == "small":
                queryset = queryset.filter(
                    investment_required_min__gte=100000, investment_required_min__lt=1000000
                )
            elif size == "medium":
                queryset = queryset.filter(
                    investment_required_min__gte=1000000, investment_required_min__lt=5000000
                )
            elif size == "large":
                queryset = queryset.filter(
                    investment_required_min__gte=5000000, investment_required_min__lt=25000000
                )
            elif size == "very_large":
                queryset = queryset.filter(investment_required_min__gte=25000000)

        # Project stage filter
        stage = self.request.GET.get("stage")
        if stage:
            queryset = queryset.filter(project_stage=stage)

        # Opportunity type filter
        opp_type = self.request.GET.get("type")
        if opp_type:
            queryset = queryset.filter(opportunity_type=opp_type)

        # Priority filter
        priority = self.request.GET.get("priority")
        if priority:
            queryset = queryset.filter(priority_level=priority)

        # Sorting
        sort = self.request.GET.get("sort", "-published_date")
        valid_sorts = [
            "-published_date",
            "published_date",
            "-investment_required_min",
            "investment_required_min",
            "title",
            "-title",
            "-views_count",
            "-inquiries_count",
        ]
        if sort in valid_sorts:
            queryset = queryset.order_by(sort)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Featured opportunities
        context["featured_opportunities"] = InvestmentOpportunity.objects.filter(
            published=True, status="active", featured=True
        ).select_related("primary_country", "primary_sector")[:6]

        # Filter options
        context["countries"] = MemberStateIPA.objects.filter(is_active=True).order_by(
            "country_name"
        )
        context["sectors"] = Sector.objects.filter(is_active=True).order_by("name")

        # Current filters for display
        context["current_search"] = self.request.GET.get("search", "")
        context["current_country"] = self.request.GET.get("country", "")
        context["current_sector"] = self.request.GET.get("sector", "")
        context["current_size"] = self.request.GET.get("size", "")
        context["current_stage"] = self.request.GET.get("stage", "")
        context["current_type"] = self.request.GET.get("type", "")
        context["current_priority"] = self.request.GET.get("priority", "")
        context["current_sort"] = self.request.GET.get("sort", "-published_date")

        # Choices for filters
        context["project_stages"] = InvestmentOpportunity.PROJECT_STAGES
        context["opportunity_types"] = InvestmentOpportunity.OPPORTUNITY_TYPES
        context["priority_levels"] = InvestmentOpportunity.PRIORITY_LEVELS

        # Stats for stats bar — single base queryset reused for all aggregates
        active_opportunities = InvestmentOpportunity.objects.filter(
            published=True, status="active"
        )
        agg = active_opportunities.aggregate(
            total_count=models.Count("id"),
            total_value=Sum("investment_required_min"),
        )
        total_value_sum = agg["total_value"] or 0
        context["total_opportunities"] = agg["total_count"]
        context["total_count"] = agg["total_count"]
        context["total_value"] = total_value_sum / 1_000_000_000  # to billions, keep decimal

        context["countries_count"] = (
            active_opportunities.exclude(primary_country__isnull=True)
            .values("primary_country")
            .distinct()
            .count()
        )
        context["sectors_count"] = (
            active_opportunities.exclude(primary_sector__isnull=True)
            .values("primary_sector")
            .distinct()
            .count()
        )

        # Pagination-safe filter querystring (strips current page number so
        # pagination links can append their own ?page=N without duplicates)
        get_copy = self.request.GET.copy()
        get_copy.pop("page", None)
        context["filter_querystring"] = get_copy.urlencode()

        return context


class OpportunityDetailView(DetailView):
    """
    Investment opportunity detail page with all information.
    Works with existing InvestmentOpportunity model.
    """

    model = InvestmentOpportunity
    template_name = "core/opportunities/detail.html"
    context_object_name = "opportunity"

    def get_queryset(self):
        return (
            InvestmentOpportunity.objects.filter(published=True)
            .select_related("primary_country", "primary_sector", "created_by", "approved_by")
            .prefetch_related("secondary_sectors", "participating_countries", "documents")
        )

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        # Increment view count
        obj.increment_views()
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Related opportunities (same sector or country)
        opportunity = self.object
        context["related_opportunities"] = (
            InvestmentOpportunity.objects.filter(published=True, status="active")
            .filter(
                Q(primary_sector=opportunity.primary_sector)
                | Q(primary_country=opportunity.primary_country)
            )
            .exclude(id=opportunity.id)
            .select_related("primary_country", "primary_sector")[:3]
        )

        # All countries for the inquiry form
        context["countries"] = MemberStateIPA.objects.filter(is_active=True).order_by(
            "country_name"
        )

        context["form"] = InvestorInquiryForm(
            initial={
                "member_state": opportunity.primary_country,
                "inquiry_type": "investment_opportunity",
                "sector_of_interest": opportunity.primary_sector,
                "subject": f"Interest in {opportunity.title}",
            }
        )

        # All sectors for the inquiry form
        context["sectors"] = Sector.objects.filter(is_active=True).order_by("name")

        # Public documents — still available for potential future use
        context["public_documents"] = opportunity.documents.filter(is_public=True).order_by(
            "display_order", "document_type"
        )
        # factsheet_url on the model takes priority; fall back to legacy OpportunityDocument
        if opportunity.factsheet_url:
            context["factsheet_url"] = opportunity.factsheet_url
        else:
            legacy_doc = context["public_documents"].filter(
                document_type__in=["brochure", "presentation", "business_plan", "feasibility", "financial", "other"]
            ).first()
            context["factsheet_url"] = legacy_doc.file if legacy_doc else ""

        return context


@require_http_methods(["POST"])
@ratelimit(key="ip", rate="10/m", method="POST", block=True)
def express_interest_ajax(request):
    """
    Handle express interest form submission via AJAX.
    Creates InvestorInquiry using existing model structure.
    """
    try:
        logger.debug("Received AJAX express interest request")
        # Get opportunity
        opportunity_slug = request.POST.get("opportunity_slug")
        opportunity = get_object_or_404(
            InvestmentOpportunity, slug=opportunity_slug, published=True
        )

        # Create inquiry using EXISTING InvestorInquiry model structure
        # Accept inquiry_type from POST so Schedule Visit / Advisory use correct type
        valid_inquiry_types = {t for t, _ in InvestorInquiry.INQUIRY_TYPES}
        raw_inquiry_type = request.POST.get("inquiry_type", "investment_opportunity")
        inquiry_type_value = raw_inquiry_type if raw_inquiry_type in valid_inquiry_types else "investment_opportunity"

        inquiry = InvestorInquiry.objects.create(
            member_state=opportunity.primary_country,
            inquiry_type=inquiry_type_value,
            # Investor info
            full_name=f"{request.POST.get('first_name', '')} {request.POST.get('last_name', '')}".strip(),
            email=request.POST.get("email", ""),
            phone=request.POST.get("phone", ""),
            company_name=request.POST.get("company_name", ""),
            company_country=request.POST.get("country", ""),
            # Investment details
            sector_of_interest=opportunity.primary_sector,
            estimated_investment=request.POST.get("investment_capacity", ""),
            # Message
            subject=f"Interest in {opportunity.title}",
            message=request.POST.get("message", ""),
            # Metadata
            ip_address=request.META.get("HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR")),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
        )

        # Increment opportunity inquiries count
        opportunity.increment_inquiries()

        # Send email notification to IPA contact for the member state
        try:
            from django.conf import settings
            from django.core.mail import send_mail

            recipient = getattr(
                opportunity.primary_country, "contact_email", None
            ) or getattr(settings, "CONTACT_EMAIL", "infodesk@ipawas.org")
            inquiry_type_label = dict(InvestorInquiry.INQUIRY_TYPES).get(inquiry_type_value, inquiry_type_value)
            send_mail(
                subject=f"New {inquiry_type_label} [{inquiry.reference_number}]: {opportunity.title}",
                message=(
                    f"A new investor inquiry has been submitted.\n\n"
                    f"Reference: {inquiry.reference_number}\n"
                    f"Investor: {inquiry.full_name} <{inquiry.email}>\n"
                    f"Organisation: {inquiry.company_name or 'N/A'}\n"
                    f"Opportunity: {opportunity.title}\n"
                    f"Message:\n{inquiry.message or '(none)'}\n\n"
                    f"Please log in to the IPAWAS dashboard to respond."
                ),
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@ipawas.org"),
                recipient_list=[recipient],
                fail_silently=True,
            )
        except Exception:
            logger.exception(
                "Failed to send inquiry notification for %s", inquiry.reference_number
            )

        return JsonResponse(
            {
                "success": True,
                "reference": inquiry.reference_number,
                "message": "Your inquiry has been submitted successfully!",
            }
        )

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)
