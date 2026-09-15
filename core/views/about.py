import logging

from django import forms
from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from core.email.services import get_inquiry_email_service
from members.forms import InvestorInquiryForm
from members.models import InvestorInquiry, MemberStateIPA

logger = logging.getLogger(__name__)


class WhoWeAreView(TemplateView):
    """
    Display the 'Who We Are' page.

    Provides comprehensive information about IPAWAS including:
    - Organizational history and establishment
    - Core statistics and metrics
    - Service offerings
    - Member states overview
    """

    template_name = "core/about/who_we_are.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Who We Are"
        context["meta_description"] = (
            "Learn about IPAWAS - the premier regional platform uniting "
            "West Africa's Investment Promotion Agencies to drive sustainable "
            "economic growth across 15 nations."
        )

        # Add statistics data
        context["stats"] = {
            "member_states": 15,
            "population": "400M+",
            "establishment_year": 2012,
            "regional_gdp": "$800B+",
        }

        # Member states list
        context["member_states"] = [
            "Benin",
            "Burkina Faso",
            "Cabo Verde",
            "Côte d'Ivoire",
            "The Gambia",
            "Ghana",
            "Guinea",
            "Guinea-Bissau",
            "Liberia",
            "Mali",
            "Niger",
            "Nigeria",
            "Senegal",
            "Sierra Leone",
            "Togo",
        ]

        return context


class MissionVisionValuesView(TemplateView):
    """
    Display the 'Mission, Vision & Values' page.

    Showcases IPAWAS's:
    - Vision statement
    - Mission statement
    - Core values and principles
    - Commitment to stakeholders
    """

    template_name = "core/about/mission_vision_values.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Mission, Vision & Values"
        context["meta_description"] = (
            "Discover IPAWAS's guiding principles - our mission to promote "
            "West Africa as a reliable investment destination and the core "
            "values that drive our work."
        )

        # Vision and Mission
        context["vision"] = (
            "To be the leading regional platform for advancing West Africa "
            "as the preferred investment destination."
        )
        context["mission"] = (
            "To proactively promote and position West Africa as a reliable "
            "and competitive sub-region for sustainable investment that drives "
            "inclusive economic growth and development."
        )

        # Core values
        context["core_values"] = [
            {
                "name": "Collaboration",
                "description": "Fostering partnership among IPAs and stakeholders across the region.",
                "icon": "users",
            },
            {
                "name": "Integrity",
                "description": "Upholding transparency, accountability, and ethical standards.",
                "icon": "shield-alt",
            },
            {
                "name": "Innovation",
                "description": "Encouraging creative and data-driven investment solutions.",
                "icon": "lightbulb",
            },
            {
                "name": "Sustainability",
                "description": "Promoting responsible investment balancing profit with impact.",
                "icon": "leaf",
            },
            {
                "name": "Excellence",
                "description": "Striving for high standards in service delivery and results.",
                "icon": "trophy",
            },
            {
                "name": "Regional Unity",
                "description": "Championing West African solidarity and integration.",
                "icon": "globe-africa",
            },
        ]

        return context


class StrategicPrioritiesView(TemplateView):
    """
    Display the 'Strategic Priorities 2025-2027' page.

    Outlines IPAWAS's strategic framework including:
    - Five key strategic priorities
    - Implementation timeline
    - Expected impact metrics
    - Action plans
    """

    template_name = "core/about/strategic_priorities.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Strategic Priorities 2025-2027"
        context["meta_description"] = (
            "Explore IPAWAS's strategic roadmap for 2025-2027, outlining "
            "five key priorities to strengthen West Africa's investment "
            "ecosystem and drive regional transformation."
        )

        # Strategic priorities
        context["priorities"] = [
            {
                "number": "01",
                "title": "Strengthening Institutional Capacity of Member IPAs",
                "description": (
                    "Building robust, efficient, and professional Investment "
                    "Promotion Agencies across all 15 member states."
                ),
            },
            {
                "number": "02",
                "title": "Developing Regional Investment Promotion Strategies",
                "description": (
                    "Creating coordinated, multi-country approaches to promote "
                    "West Africa as a unified investment destination."
                ),
            },
            {
                "number": "03",
                "title": "Enhancing Cross-Border Investment Facilitation",
                "description": (
                    "Streamlining processes and reducing barriers to enable "
                    "seamless investment flows across borders."
                ),
            },
            {
                "number": "04",
                "title": "Building Robust Investment Intelligence Systems",
                "description": (
                    "Establishing comprehensive data-driven platforms through "
                    "the West Africa Investment Intelligence System (WAIIS)."
                ),
            },
            {
                "number": "05",
                "title": "Enhancing and Sustaining Strategic Partnerships",
                "description": (
                    "Strengthening relationships with ECOWAS, WAIPA, development "
                    "partners, and key stakeholders."
                ),
            },
        ]

        # Expected impact by 2027
        context["impact_metrics"] = {
            "ipa_capacity": "100%",
            "joint_missions": "15+",
            "investment_target": "$50B+",
            "staff_trained": "500+",
        }

        return context


class GovernanceLeadershipView(TemplateView):
    """
    Display the 'Governance & Leadership' page.

    Details IPAWAS's governance structure:
    - Legal framework
    - Organizational structure
    - Decision-making processes
    - Governance principles
    - Current leadership arrangement
    """

    template_name = "core/about/governance_leadership.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Governance & Leadership"
        context["meta_description"] = (
            "Learn about IPAWAS's governance framework, organizational "
            "structure, and commitment to transparent, accountable leadership "
            "serving all 15 member states."
        )

        # Governance structure
        context["governance_bodies"] = [
            {
                "name": "General Assembly",
                "description": "Highest decision-making body comprising all 15 member IPAs",
                "responsibilities": [
                    "Approves strategic direction",
                    "Elects Executive Committee",
                    "Reviews financial reports",
                    "Makes major policy decisions",
                ],
            },
            {
                "name": "Executive Committee",
                "description": "Elected representatives overseeing operations",
                "responsibilities": [
                    "Oversees daily operations",
                    "Implements Assembly decisions",
                    "Provides strategic guidance",
                    "Monitors performance",
                ],
            },
            {
                "name": "Secretariat",
                "description": "Administrative body coordinating activities",
                "responsibilities": [
                    "Coordinates programs",
                    "Manages operations",
                    "Facilitates communication",
                    "Provides technical support",
                ],
            },
        ]

        # Governance principles
        context["principles"] = [
            "Transparency",
            "Inclusivity",
            "Accountability",
            "Consensus Building",
            "Sustainability",
            "Ethical Standards",
        ]

        return context


class ECOWASRelationshipView(TemplateView):
    """
    Display the 'ECOWAS Relationship' page.

    Explains the partnership between IPAWAS and ECOWAS:
    - Complementary roles
    - Collaboration areas
    - Joint initiatives
    - Shared goals
    - ECOWAS support mechanisms
    """

    template_name = "core/about/ecowas_relationship.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "ECOWAS Relationship"
        context["meta_description"] = (
            "Discover how IPAWAS and ECOWAS work together to drive regional "
            "integration, investment facilitation, and economic development "
            "across West Africa."
        )

        # Collaboration areas
        context["collaboration_areas"] = [
            {
                "title": "Regional Integration",
                "icon": "network-wired",
                "description": (
                    "Supporting ECOWAS regional integration agenda through "
                    "investment promotion aligned with Vision 2050."
                ),
            },
            {
                "title": "Investment Promotion",
                "icon": "bullhorn",
                "description": (
                    "Joint promotion of West Africa through coordinated missions "
                    "and regional investment forums."
                ),
            },
            {
                "title": "Data & Intelligence",
                "icon": "chart-bar",
                "description": (
                    "WAIIS provides critical data supporting ECOWAS policy "
                    "decisions and regional planning."
                ),
            },
            {
                "title": "Capacity Building",
                "icon": "graduation-cap",
                "description": ("Training IPAs on ECOWAS protocols and regional opportunities."),
            },
        ]

        # Joint initiatives
        context["joint_initiatives"] = [
            {
                "name": "AfCFTA Investment Facilitation",
                "status": "Active",
                "timeline": "2024 - 2027",
            },
            {
                "name": "Regional Investment Data Platform",
                "status": "Active",
                "timeline": "2025 - 2026",
            },
            {"name": "IPA Capacity Building Program", "status": "Active", "timeline": "Ongoing"},
        ]

        return context


# class ContactUsView(TemplateView):
#     """
#     Display the 'Contact Us' page.

#     Provides comprehensive contact information:
#     - IPAWAS Secretariat details
#     - Contact form
#     - Interactive map
#     - Quick links
#     - FAQ section
#     - Newsletter subscription

#     Note: This is a simple TemplateView. For form handling,
#     consider extending with FormView or processing via AJAX.
#     """

#     template_name = "core/about/contact_us.html"

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context["page_title"] = "Contact Us"
#         context["meta_description"] = (
#             "Get in touch with IPAWAS Secretariat. Contact information, office "
#             "location, inquiry form, and quick links for investors, IPAs, and partners."
#         )

#         # Contact information
#         context["contact_info"] = {
#             "address": {
#                 "line1": "IPAWAS Secretariat",
#                 "line2": "c/o Nigerian Investment Promotion Commission (NIPC)",
#                 "line3": "Plot 1181, Aguiyi Ironsi Street",
#                 "line4": "Maitama District",
#                 "line5": "Abuja, Federal Capital Territory",
#                 "line6": "Nigeria",
#             },
#             "email": "infodesk@ipawas.org",
#             "phone": "+234 (0) 906 204 0061",
#             "office_hours": "Monday – Friday, 8:00 AM – 4:00 PM (GMT+1)",
#         }

#         # Social media links (update with actual URLs)
#         context["social_media"] = {
#             "linkedin": "#",
#             "twitter": "#",
#             "facebook": "#",
#             "youtube": "#",
#         }

#         # Inquiry types for form dropdown
#         context["inquiry_types"] = [
#             "General Inquiry",
#             "Investment Opportunity",
#             "Partnership Request",
#             "Media/Press Inquiry",
#             "IPA Support Request",
#             "Technical Support",
#             "Other",
#         ]

#         # Member states for country dropdown
#         context["countries"] = [
#             "Benin",
#             "Burkina Faso",
#             "Cabo Verde",
#             "Côte d'Ivoire",
#             "The Gambia",
#             "Ghana",
#             "Guinea",
#             "Guinea-Bissau",
#             "Liberia",
#             "Mali",
#             "Niger",
#             "Nigeria",
#             "Senegal",
#             "Sierra Leone",
#             "Togo",
#             "Other",
#         ]

#         # FAQ items
#         context["faqs"] = [
#             {
#                 "id": "faq1",
#                 "question": "What is IPAWAS?",
#                 "answer": (
#                     "IPAWAS (Investment Promotion Agencies of West African States) "
#                     "is a regional association of Investment Promotion Agencies from "
#                     "all 12 ECOWAS member states."
#                 ),
#             },
#             {
#                 "id": "faq2",
#                 "question": "How can I invest in West Africa through IPAWAS?",
#                 "answer": (
#                     "IPAWAS connects investors with investment opportunities across "
#                     "West Africa. Explore opportunities on our Investment Opportunities "
#                     "page, and we can connect you with relevant country IPAs."
#                 ),
#             },
#             # Add more FAQs as needed
#         ]

#         return context


class ContactUsView(FormView):
    """Handle contact form submissions using InvestorInquiry model."""

    template_name = "core/about/contact_us.html"
    form_class = InvestorInquiryForm

    def get_success_url(self):
        return self.request.path

    def form_valid(self, form):
        # Get the inquiry instance but don't save yet
        inquiry = form.save(commit=False)

        # If no member_state selected, assign to a default (e.g., Nigeria/IPAWAS HQ)
        if not inquiry.member_state_id:
            inquiry.member_state = (
                MemberStateIPA.objects.filter(country_code="NG").first()
                or MemberStateIPA.objects.first()
            )
            is_general_inquiry = True
        else:
            is_general_inquiry = False

        # Capture metadata
        inquiry.ip_address = self.get_client_ip(self.request)
        inquiry.user_agent = self.request.META.get("HTTP_USER_AGENT", "")[:500]

        # Save the inquiry (reference_number auto-generated)
        inquiry.save()

        # Initialize email service
        email_service = get_inquiry_email_service()

        # 1. Send confirmation email to the investor
        try:
            email_sent = email_service.send_inquiry_confirmation(inquiry)

            if not email_sent:
                logger.warning(
                    f"Failed to send confirmation email for inquiry {inquiry.reference_number}"
                )
        except Exception as e:
            logger.exception(
                f"Error sending confirmation email for inquiry {inquiry.reference_number}: {str(e)}"
            )

        # 2. Notify admins (HQ or country-specific)
        try:
            recipients = self.get_notification_recipients(inquiry, is_general_inquiry)

            if recipients:
                admin_notified = email_service.send_new_inquiry_notification(inquiry, recipients)

                if admin_notified:
                    logger.info(
                        f"Notified {len(recipients)} admin(s) about inquiry {inquiry.reference_number}"
                    )
                else:
                    logger.warning(
                        f"Failed to notify admins about inquiry {inquiry.reference_number}"
                    )
        except Exception as e:
            logger.exception(
                f"Error notifying admins about inquiry {inquiry.reference_number}: {str(e)}"
            )

        # Return JSON for AJAX or redirect for regular form
        if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse(
                {
                    "success": True,
                    "message": f"Thank you! Your inquiry ({inquiry.reference_number}) has been received. We'll respond within 2 business days.",
                    "reference": inquiry.reference_number,
                }
            )

        messages.success(
            self.request,
            f"Thank you! Your inquiry ({inquiry.reference_number}) has been received. We'll respond within 2 business days.",
        )
        return super().form_valid(form)

    def get_notification_recipients(self, inquiry, is_general_inquiry):
        """
        Determine who should be notified about this inquiry.

        Args:
            inquiry: InvestorInquiry instance
            is_general_inquiry: Whether this is a general IPAWAS inquiry (no specific country)

        Returns:
            QuerySet of IPAUser instances to notify
        """
        from accounts.models import IPAUser

        if is_general_inquiry:
            # Notify IPAWAS HQ admins (Nigeria HQ staff with admin permissions)
            recipients = IPAUser.objects.filter(
                member_state__country_code="NG",  # IPAWAS HQ is in Nigeria
                notify_on_inquiry=True,
                is_active=True,
                user__is_active=True,
                user__email_notifications=True,
            ).select_related("user")

            # If no HQ staff found, notify superusers
            if not recipients.exists():
                from accounts.models import User

                admin_users = User.objects.filter(
                    is_superuser=True, is_active=True, email_notifications=True
                )
                # Convert to IPAUser queryset if possible, or handle separately
                logger.warning(
                    f"No HQ staff found for general inquiry {inquiry.reference_number}, would notify superusers"
                )
        else:
            # Notify country-specific IPA staff
            recipients = IPAUser.objects.filter(
                member_state=inquiry.member_state,
                notify_on_inquiry=True,
                is_active=True,
                user__is_active=True,
                user__email_notifications=True,
            ).select_related("user", "member_state")

            # If no country staff found, also notify HQ
            if not recipients.exists():
                logger.warning(
                    f"No staff found for {inquiry.member_state.country_name}, notifying HQ"
                )
                recipients = IPAUser.objects.filter(
                    member_state__country_code="NGA",
                    notify_on_inquiry=True,
                    is_active=True,
                    user__is_active=True,
                    user__email_notifications=True,
                ).select_related("user")

        return recipients

    def form_invalid(self, form):
        if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": False, "errors": form.errors}, status=400)
        return super().form_invalid(form)

    def get_client_ip(self, request):
        """Extract client IP address."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Contact Us"
        context["meta_description"] = (
            "Get in touch with IPAWAS Secretariat. Contact information, office "
            "location, inquiry form, and quick links for investors, IPAs, and partners."
        )

        # Contact information
        context["contact_info"] = {
            "address": {
                "line1": "IPAWAS Secretariat",
                "line2": "c/o Nigerian Investment Promotion Commission (NIPC)",
                "line3": "Plot 1181, Aguiyi Ironsi Street",
                "line4": "Maitama District",
                "line5": "Abuja, Federal Capital Territory",
                "line6": "Nigeria",
            },
            "email": "infodesk@ipawas.org",
            "phone": "+234 (0) 906 204 0061",
            "office_hours": "Monday – Friday, 8:00 AM – 4:00 PM (GMT+1)",
        }

        context["social_media"] = {
            "linkedin": getattr(settings, "SOCIAL_LINKEDIN", ""),
            "twitter": getattr(settings, "SOCIAL_TWITTER", ""),
            "facebook": getattr(settings, "SOCIAL_FACEBOOK", ""),
            "youtube": getattr(settings, "SOCIAL_YOUTUBE", ""),
            "instagram": getattr(settings, "SOCIAL_INSTAGRAM", ""),
        }

        # IPA office directory for "Find Us" section
        from members.models import MemberStateIPA
        context["ipa_offices"] = (
            MemberStateIPA.objects
            .filter(is_active=True)
            .order_by("country_name")
            .values("country_name", "ipa_full_name", "ipa_acronym", "capital_city", "contact_email", "flag_emoji")
        )

        return context


class ContactForm(forms.Form):
    """Contact form for IPAWAS inquiries."""

    inquiry_type = forms.ChoiceField(
        choices=[
            ("general", "General Inquiry"),
            ("investment", "Investment Opportunity"),
            ("partnership", "Partnership Request"),
            ("media", "Media/Press Inquiry"),
            ("ipa-support", "IPA Support Request"),
            ("technical", "Technical Support"),
            ("other", "Other"),
        ],
        required=True,
    )
    full_name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=20, required=False)
    organization = forms.CharField(max_length=200, required=False)
    country = forms.CharField(max_length=100, required=True)
    subject = forms.CharField(max_length=100, required=True)
    message = forms.CharField(widget=forms.Textarea, min_length=50, max_length=1000, required=True)
    consent = forms.BooleanField(required=True)


class ContactFormView(FormView):
    """
    Handle contact form submissions.

    Processes form data and sends email notifications.
    """

    template_name = "core/about/contact_us.html"
    form_class = ContactForm
    success_url = reverse_lazy("about:contact")

    def form_valid(self, form):
        # Process the form data
        data = form.cleaned_data

        # Send email notification
        subject = f"IPAWAS Contact Form: {data['subject']}"
        message = f"""
        New contact form submission from IPAWAS website:

        Inquiry Type: {data['inquiry_type']}
        Name: {data['full_name']}
        Email: {data['email']}
        Phone: {data.get('phone', 'Not provided')}
        Organization: {data.get('organization', 'Not provided')}
        Country: {data['country']}

        Subject: {data['subject']}

        Message:
        {data['message']}
        """

        contact_email = getattr(settings, "CONTACT_EMAIL", settings.DEFAULT_FROM_EMAIL)
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [contact_email],
                fail_silently=False,
            )
            messages.success(
                self.request,
                "Thank you! Your message has been received. "
                "We'll respond within 2 business days.",
            )
        except Exception as e:
            messages.error(
                self.request,
                "Sorry, there was an error sending your message. "
                "Please try again or email us directly.",
            )

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add same context data as ContactUsView
        contact_view = ContactUsView()
        context.update(contact_view.get_context_data(**kwargs))
        return context


class AfCFTAView(TemplateView):

    template_name = "core/about/afcfta.html"


def commission_president(request):
    """
    Display ECOWAS Commission President profile.

    Future enhancement: Fetch from ECOWASLeadershipPosition model
    position_type='commission_president'
    """
    context = {
        "page_title": "President of ECOWAS Commission",
        "meta_description": "Profile of the President of the ECOWAS Commission, leading regional integration efforts across West Africa.",
    }

    # Future: Add database query
    # from ecowas.models import ECOWASLeadershipPosition
    # context['leader'] = ECOWASLeadershipPosition.objects.get(
    #     position_type='commission_president',
    #     is_active=True
    # )

    return render(request, "core/leadership/commission_president.html", context)


def authority_chairman(request):
    """
    Display ECOWAS Authority Chairman profile.

    This is a rotating position held by a member state Head of Government.

    Future enhancement: Fetch from ECOWASLeadershipPosition model
    position_type='authority_chairman'
    """
    context = {
        "page_title": "Chairman of ECOWAS Authority",
        "meta_description": "Profile of the current Chairman of the ECOWAS Authority of Heads of State and Government.",
    }

    # Future: Add database query
    # from ecowas.models import ECOWASLeadershipPosition
    # context['leader'] = ECOWASLeadershipPosition.objects.get(
    #     position_type='authority_chairman',
    #     is_active=True
    # )

    return render(request, "core/leadership/authority_chairman.html", context)


def commissioner_economic(request):
    """
    Display Commissioner for Economic Affairs and Agriculture profile.

    This position has direct oversight of IPAWAS and investment promotion.

    Future enhancement: Fetch from ECOWASLeadershipPosition model
    position_type='commissioner_economic'
    """
    context = {
        "page_title": "Commissioner for Economic Affairs and Agriculture",
        "meta_description": "Profile of the ECOWAS Commissioner for Economic Affairs and Agriculture, overseeing regional investment promotion through IPAWAS.",
    }

    # Future: Add database query
    # from ecowas.models import ECOWASLeadershipPosition
    # context['leader'] = ECOWASLeadershipPosition.objects.get(
    #     position_type='commissioner_economic',
    #     is_active=True
    # )

    return render(request, "core/leadership/commissioner_economic.html", context)


def secretary_general(request):
    """
    Display IPAWAS Secretary General profile — Bakary Séga Bathily.
    """
    context = {
        "page_title": "Secretary General of IPAWAS",
        "meta_description": "Profile of Bakary Séga Bathily, founding Secretary General of IPAWAS, leading operational activities and investment promotion coordination across West Africa.",
    }
    return render(request, "core/leadership/secretary_general.html", context)


class PrivacyPolicyView(TemplateView):
    template_name = "core/about/privacy_policy.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Privacy Policy"
        context["meta_description"] = (
            "IPAWAS Privacy Policy — how we collect, use, and protect your personal "
            "information when you use our platform and services."
        )
        return context


class TermsOfUseView(TemplateView):
    template_name = "core/about/terms_of_use.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Terms of Use"
        context["meta_description"] = (
            "IPAWAS Terms of Use — the rules and conditions governing access to "
            "and use of the IPAWAS platform, data, and services."
        )
        return context
