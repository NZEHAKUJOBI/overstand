"""Analytics views for the member-state dashboard."""

import csv
import json
from datetime import date, timedelta

from django.db.models import Count, Sum
from django.db.models.functions import TruncDate, TruncMonth, TruncWeek
from django.http import HttpResponse
from django.utils import timezone
from django.views.generic import TemplateView, View

from dashboard.mixins import IPAStaffRequiredMixin

VALID_RANGES = (7, 30, 90, 365)
RANGE_LABELS = {
    7: "Last 7 Days",
    30: "Last 30 Days",
    90: "Last 90 Days",
    365: "This Year",
}
INQUIRY_STATUSES = [
    ("new", "New"),
    ("in_progress", "In Progress"),
    ("responded", "Responded"),
    ("closed", "Closed"),
]
STATUS_COLORS = {
    "new": "#1B7A4C",
    "in_progress": "#3B82F6",
    "responded": "#10B981",
    "closed": "#8B5CF6",
}


def _parse_range(request):
    try:
        days = int(request.GET.get("range", 30))
        return days if days in VALID_RANGES else 30
    except (ValueError, TypeError):
        return 30


def _build_inquiry_trend(period_inquiries, now, days):
    """Return (labels, values) for the inquiry trend chart."""
    if days <= 30:
        raw = (
            period_inquiries.annotate(bucket=TruncDate("created_at"))
            .values("bucket")
            .annotate(n=Count("id"))
            .order_by("bucket")
        )
        bucket_map = {r["bucket"]: r["n"] for r in raw}
        labels, values = [], []
        fmt = "%a" if days <= 7 else "%b %d"
        for i in range(days - 1, -1, -1):
            d = (now - timedelta(days=i)).date()
            labels.append(d.strftime(fmt))
            values.append(bucket_map.get(d, 0))
    elif days == 90:
        raw = (
            period_inquiries.annotate(bucket=TruncWeek("created_at"))
            .values("bucket")
            .annotate(n=Count("id"))
            .order_by("bucket")
        )
        bucket_map = {r["bucket"].date(): r["n"] for r in raw}
        labels, values = [], []
        for i in range(12, -1, -1):
            d = (now - timedelta(weeks=i)).date()
            w_start = d - timedelta(days=d.weekday())
            labels.append(w_start.strftime("%b %d"))
            values.append(bucket_map.get(w_start, 0))
    else:  # 365
        raw = (
            period_inquiries.annotate(bucket=TruncMonth("created_at"))
            .values("bucket")
            .annotate(n=Count("id"))
            .order_by("bucket")
        )
        bucket_map = {}
        for r in raw:
            d = r["bucket"].date() if hasattr(r["bucket"], "date") else r["bucket"]
            bucket_map[date(d.year, d.month, 1)] = r["n"]
        labels, values = [], []
        for i in range(11, -1, -1):
            m_date = (now - timedelta(days=i * 30)).date()
            m_first = date(m_date.year, m_date.month, 1)
            labels.append(m_first.strftime("%b %Y"))
            values.append(bucket_map.get(m_first, 0))
    return labels, values


class AnalyticsView(IPAStaffRequiredMixin, TemplateView):
    template_name = "dashboard/members/analytics.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        member_state = self.request.user.ipa_profile.member_state
        now = timezone.now()
        days = _parse_range(self.request)
        start_date = now - timedelta(days=days)
        prev_start = start_date - timedelta(days=days)

        context["selected_range"] = days
        context["range_label"] = RANGE_LABELS[days]

        # ── Opportunities ──────────────────────────────────────────────
        opps = member_state.opportunities.all()
        published_opps = opps.filter(published=True)

        context["published_opportunities"] = published_opps.count()
        context["total_opportunities"] = opps.count()
        context["total_views"] = published_opps.aggregate(t=Sum("views_count"))["t"] or 0
        context["total_downloads"] = published_opps.aggregate(t=Sum("downloads_count"))["t"] or 0
        context["new_opportunities"] = opps.filter(created_at__gte=start_date).count()

        # ── Inquiries ──────────────────────────────────────────────────
        inquiries = member_state.inquiries.all()
        period_inquiries = inquiries.filter(created_at__gte=start_date)
        prev_period_inquiries = inquiries.filter(
            created_at__gte=prev_start, created_at__lt=start_date
        ).count()

        context["total_inquiries"] = inquiries.count()
        context["period_inquiries"] = period_inquiries.count()
        context["new_inquiries"] = inquiries.filter(status="new").count()
        context["inquiries_this_month"] = inquiries.filter(
            created_at__gte=now - timedelta(days=30)
        ).count()

        # Trend vs previous period
        curr = period_inquiries.count()
        if prev_period_inquiries:
            pct = round((curr - prev_period_inquiries) / prev_period_inquiries * 100)
        else:
            pct = None
        context["inquiry_trend_pct"] = pct
        context["inquiry_trend_up"] = pct is not None and pct >= 0

        # ── Inquiry status breakdown ───────────────────────────────────
        status_raw = (
            inquiries.values("status").annotate(count=Count("id")).order_by("status")
        )
        status_map = {d["status"]: d["count"] for d in status_raw}
        status_keys = [s[0] for s in INQUIRY_STATUSES]
        status_labels = [s[1] for s in INQUIRY_STATUSES]
        status_counts = [status_map.get(k, 0) for k in status_keys]
        status_color_list = [STATUS_COLORS[k] for k in status_keys]
        context["status_labels_json"] = json.dumps(status_labels)
        context["status_counts_json"] = json.dumps(status_counts)
        context["status_colors_json"] = json.dumps(status_color_list)
        context["status_total"] = sum(status_counts)
        context["status_breakdown"] = list(zip(status_labels, status_counts, status_color_list))

        # ── Team ───────────────────────────────────────────────────────
        context["active_team_members"] = member_state.ipa_users.filter(is_active=True).count()

        # ── Top opportunities ──────────────────────────────────────────
        top_opps = list(published_opps.order_by("-inquiries_count", "-views_count")[:5])
        max_inq = max((o.inquiries_count for o in top_opps), default=1) or 1
        for opp in top_opps:
            opp.engagement_rate = round(opp.inquiries_count / max_inq * 100)
        context["top_opportunities"] = top_opps

        # ── Sector distribution ────────────────────────────────────────
        sector_data = (
            published_opps.values("primary_sector__name")
            .annotate(count=Count("id"))
            .order_by("-count")[:8]
        )
        sector_labels = [d["primary_sector__name"] or "Unspecified" for d in sector_data]
        sector_counts = [d["count"] for d in sector_data]
        context["sector_labels_json"] = json.dumps(sector_labels)
        context["sector_counts_json"] = json.dumps(sector_counts)

        # ── Inquiry trend chart ────────────────────────────────────────
        chart_labels, chart_values = _build_inquiry_trend(period_inquiries, now, days)
        context["chart_labels_json"] = json.dumps(chart_labels)
        context["chart_values_json"] = json.dumps(chart_values)

        # ── Top countries ──────────────────────────────────────────────
        top_countries = list(
            inquiries.exclude(company_country="")
            .values("company_country")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )
        total_cq = sum(c["count"] for c in top_countries) or 1
        for entry in top_countries:
            entry["pct"] = round(entry["count"] / total_cq * 100)
        context["top_countries"] = top_countries

        return context


class AnalyticsExportView(IPAStaffRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        member_state = request.user.ipa_profile.member_state
        now = timezone.now()
        days = _parse_range(request)
        start_date = now - timedelta(days=days)
        export_type = request.GET.get("type", "summary")

        response = HttpResponse(content_type="text/csv")
        filename = f"analytics_{member_state.slug}_{now.strftime('%Y%m%d')}_{export_type}.csv"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        writer = csv.writer(response)

        if export_type == "inquiries":
            self._write_inquiries(writer, member_state, start_date, days)
        elif export_type == "opportunities":
            self._write_opportunities(writer, member_state)
        else:
            self._write_summary(writer, member_state, days, start_date, now)

        return response

    def _write_summary(self, writer, member_state, days, start_date, now):
        writer.writerow(["IPAWAS Analytics Report — Summary"])
        writer.writerow([f"Member State: {member_state.ipa_full_name}"])
        writer.writerow([f"Period: {RANGE_LABELS[days]} (from {start_date.date()} to {now.date()})"])
        writer.writerow([f"Exported: {now.strftime('%Y-%m-%d %H:%M UTC')}"])
        writer.writerow([])

        opps = member_state.opportunities.all()
        published = opps.filter(published=True)
        inquiries = member_state.inquiries.all()

        writer.writerow(["OPPORTUNITIES"])
        writer.writerow(["Metric", "Value"])
        writer.writerow(["Total Opportunities", opps.count()])
        writer.writerow(["Published Opportunities", published.count()])
        writer.writerow(["Total Views", published.aggregate(t=Sum("views_count"))["t"] or 0])
        writer.writerow(["Total Downloads", published.aggregate(t=Sum("downloads_count"))["t"] or 0])
        writer.writerow(["New in Period", opps.filter(created_at__gte=start_date).count()])
        writer.writerow([])

        writer.writerow(["INQUIRIES"])
        writer.writerow(["Metric", "Value"])
        writer.writerow(["Total Inquiries", inquiries.count()])
        writer.writerow(["In Period", inquiries.filter(created_at__gte=start_date).count()])
        for key, label in INQUIRY_STATUSES:
            writer.writerow([label, inquiries.filter(status=key).count()])
        writer.writerow([])

        writer.writerow(["TOP OPPORTUNITIES BY INQUIRIES"])
        writer.writerow(["Rank", "Title", "Reference", "Views", "Inquiries", "Downloads"])
        for i, opp in enumerate(published.order_by("-inquiries_count", "-views_count")[:10], 1):
            writer.writerow([
                i, opp.title, opp.reference_number,
                opp.views_count, opp.inquiries_count, opp.downloads_count,
            ])
        writer.writerow([])

        writer.writerow(["TOP INVESTOR COUNTRIES"])
        writer.writerow(["Country", "Inquiries", "% of Total"])
        total_cq = inquiries.exclude(company_country="").count() or 1
        for entry in (
            inquiries.exclude(company_country="")
            .values("company_country")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        ):
            writer.writerow([
                entry["company_country"],
                entry["count"],
                f"{round(entry['count'] / total_cq * 100)}%",
            ])

    def _write_inquiries(self, writer, member_state, start_date, days):
        writer.writerow(["IPAWAS — Inquiries Export"])
        writer.writerow([f"Member State: {member_state.ipa_full_name}"])
        writer.writerow([f"Period: {RANGE_LABELS[days]} (since {start_date.date()})"])
        writer.writerow([])
        writer.writerow([
            "Reference", "Date", "Type", "Subject", "Investor Name",
            "Company", "Country", "Email", "Phone", "Status",
        ])
        qs = (
            member_state.inquiries.filter(created_at__gte=start_date)
            .select_related("sector_of_interest")
            .order_by("-created_at")
        )
        for inq in qs:
            writer.writerow([
                inq.reference_number,
                inq.created_at.strftime("%Y-%m-%d"),
                inq.get_inquiry_type_display(),
                inq.subject,
                inq.full_name,
                inq.company_name,
                inq.company_country,
                inq.email,
                inq.phone,
                inq.get_status_display(),
            ])

    def _write_opportunities(self, writer, member_state):
        writer.writerow(["IPAWAS — Opportunities Export"])
        writer.writerow([f"Member State: {member_state.ipa_full_name}"])
        writer.writerow([])
        writer.writerow([
            "Reference", "Title", "Sector", "Type",
            "Published", "Views", "Inquiries", "Downloads", "Published Date", "Created",
        ])
        qs = (
            member_state.opportunities.all()
            .select_related("primary_sector")
            .order_by("-created_at")
        )
        for opp in qs:
            writer.writerow([
                opp.reference_number,
                opp.title,
                opp.primary_sector.name if opp.primary_sector else "",
                opp.get_opportunity_type_display(),
                "Yes" if opp.published else "No",
                opp.views_count,
                opp.inquiries_count,
                opp.downloads_count,
                opp.published_date.strftime("%Y-%m-%d") if opp.published_date else "",
                opp.created_at.strftime("%Y-%m-%d"),
            ])
