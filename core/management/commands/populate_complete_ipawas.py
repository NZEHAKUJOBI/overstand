"""
Django Management Command: Comprehensive IPAWAS Database Population
Location: apps/core/management/commands/populate_complete_ipawas.py

Creates COMPLETE test data including:
- Member States & HQ Admins
- Sectors & Sub-sectors
- Investment Opportunities
- Investment Incentives
- Events (Forums, Workshops, Webinars)
- Publications & Documents
- News & Blog Posts
- FDI Data Points (WAIIS)
- Success Stories
- Partners & Development Organizations
"""

import random
from datetime import datetime, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import IPAUser
from core.models import Event, Publication, Sector
from dashboard.models import IPADashboardActivity, IPANotification
from invitations.models import Invitation
from members.models import FDIDataPoint, InvestmentIncentive, MemberStateIPA, SuccessStory
from opportunities.models import InvestmentOpportunity

User = get_user_model()


class Command(BaseCommand):
    help = "Populate complete IPAWAS database with realistic data across all tables"

    def __init__(self):
        super().__init__()
        self.credentials = []
        self.member_states = []
        self.sectors = []
        self.hq_admins = []

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing data before populating",
        )
        parser.add_argument(
            "--basic-only",
            action="store_true",
            help="Create only users and member states (skip opportunities, events, etc.)",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("\n🚀 Starting Complete IPAWAS Data Population...\n"))

        if options["clear"]:
            self.clear_data()

        with transaction.atomic():
            # Phase 1: Core entities
            self.stdout.write(self.style.HTTP_INFO("\n📊 PHASE 1: Core Entities"))
            self.member_states = self.create_member_states()
            self.hq_admins = self.create_hq_admins()

            # Phase 2: IPA Staff
            self.stdout.write(self.style.HTTP_INFO("\n👥 PHASE 2: IPA Staff"))
            self.all_ipa_staff = {}
            for state in self.member_states:
                staff = self.create_ipa_staff(state)
                self.all_ipa_staff[state.slug] = staff

            if not options["basic_only"]:
                # Phase 3: Content entities
                self.stdout.write(self.style.HTTP_INFO("\n📁 PHASE 3: Content & Sectors"))
                self.sectors = self.create_sectors()
                self.create_investment_incentives()

                # Phase 4: Investment opportunities
                self.stdout.write(self.style.HTTP_INFO("\n💼 PHASE 4: Investment Opportunities"))
                self.create_investment_opportunities()

                # Phase 5: Events & Programs
                self.stdout.write(self.style.HTTP_INFO("\n📅 PHASE 5: Events & Programs"))
                self.create_events()

                # Phase 6: Knowledge Hub
                self.stdout.write(self.style.HTTP_INFO("\n📚 PHASE 6: Knowledge Hub"))
                self.create_publications()
                self.create_success_stories()

                # Phase 7: WAIIS Data
                self.stdout.write(self.style.HTTP_INFO("\n📈 PHASE 7: FDI Data (WAIIS)"))
                self.create_fdi_data()

                # Phase 8: Dashboard data
                self.stdout.write(self.style.HTTP_INFO("\n🔔 PHASE 8: Dashboard Data"))
                self.create_activities(self.member_states, self.hq_admins, self.all_ipa_staff)
                self.create_notifications(self.member_states, self.all_ipa_staff)
                self.create_invitations(self.member_states, self.hq_admins)

        # Save credentials
        self.save_credentials()

        self.print_summary()
        self.stdout.write(self.style.SUCCESS("\n✅ Complete database population finished!"))
        self.stdout.write(self.style.SUCCESS("📄 Credentials saved to credentials.txt\n"))

    def clear_data(self):
        """Clear all existing data"""
        self.stdout.write("🗑️  Clearing existing data...")

        # Clear dashboard data
        IPADashboardActivity.objects.all().delete()
        IPANotification.objects.all().delete()
        Invitation.objects.all().delete()

        # Clear content (check if models exist)
        try:

            InvestmentOpportunity.objects.all().delete()
            InvestmentIncentive.objects.all().delete()
            Event.objects.all().delete()
            Publication.objects.all().delete()
            # NewsArticle.objects.all().delete()
            SuccessStory.objects.all().delete()
            Sector.objects.all().delete()
        except ImportError:
            self.stdout.write(self.style.WARNING("  ⚠ Content models not found, skipping"))

        # Clear FDI data
        try:

            FDIDataPoint.objects.all().delete()
        except ImportError:
            self.stdout.write(self.style.WARNING("  ⚠ WAIIS models not found, skipping"))

        # Clear users
        IPAUser.objects.all().delete()
        User.objects.filter(user_type__in=["ipawas_admin", "ipa_staff"]).delete()
        MemberStateIPA.objects.all().delete()

        self.stdout.write(self.style.SUCCESS("✓ Data cleared"))

    def create_member_states(self):
        """Create all 12 ECOWAS member state IPAs"""
        self.stdout.write("Creating Member State IPAs...")

        states_data = [
            {
                "country_name": "Nigeria",
                "slug": "nigeria",
                "country_code": "NGA",
                "flag_emoji": "🇳🇬",
                "ipa_full_name": "Nigerian Investment Promotion Commission",
                "ipa_acronym": "NIPC",
                "ipa_website": "https://www.nipc.gov.ng",
                "overview": "The Nigerian Investment Promotion Commission (NIPC) encourages, promotes and co-ordinates investments in the Nigerian economy.",
                "contact_email": "info@nipc.gov.ng",
                "contact_phone": "+234 9 461 3000",
                "population": 227000000,
                "gdp": 252.00,
                "official_language": "english",
                "capital_city": "Abuja",
                "currency_name": "Nigerian Naira",
                "currency_code": "NGN",
                "currency_symbol": "₦",
                "is_active": True,
            },
            {
                "country_name": "Ghana",
                "slug": "ghana",
                "country_code": "GHA",
                "flag_emoji": "🇬🇭",
                "ipa_full_name": "Ghana Investment Promotion Centre",
                "ipa_acronym": "GIPC",
                "ipa_website": "https://www.gipc.gov.gh",
                "overview": "GIPC is Ghana's primary institution for investment promotion, providing a one-stop shop for investors.",
                "contact_email": "info@gipcghana.com",
                "contact_phone": "+233 30 266 5125",
                "population": 33800000,
                "gdp": 87.50,
                "official_language": "english",
                "capital_city": "Accra",
                "currency_name": "Ghanaian Cedi",
                "currency_code": "GHS",
                "currency_symbol": "₵",
                "is_active": True,
            },
            {
                "country_name": "Benin",
                "slug": "benin",
                "country_code": "BEN",
                "flag_emoji": "🇧🇯",
                "ipa_full_name": "Agence de Promotion des Investissements et des Exportations",
                "ipa_acronym": "APIEX",
                "ipa_website": "https://www.apiex.bj",
                "overview": "APIEX promotes and facilitates investment and exports in Benin.",
                "contact_email": "contact@apiex.bj",
                "contact_phone": "+229 21 31 55 70",
                "population": 13400000,
                "gdp": 20.50,
                "official_language": "french",
                "capital_city": "Porto-Novo",
                "currency_name": "West African CFA Franc",
                "currency_code": "XOF",
                "currency_symbol": "CFA",
                "is_active": True,
            },
            {
                "country_name": "Cabo Verde",
                "slug": "cabo-verde",
                "country_code": "CPV",
                "flag_emoji": "🇨🇻",
                "ipa_full_name": "Cabo Verde TradeInvest",
                "ipa_acronym": "CVTI",
                "ipa_website": "https://www.cvtradeinvest.com",
                "overview": "CVTI facilitates and promotes investment across the Cabo Verde archipelago.",
                "contact_email": "info@cvtradeinvest.com",
                "contact_phone": "+238 260 37 00",
                "population": 600000,
                "gdp": 3.20,
                "official_language": "portuguese",
                "capital_city": "Praia",
                "currency_name": "Cape Verdean Escudo",
                "currency_code": "CVE",
                "currency_symbol": "$",
                "is_active": True,
            },
            {
                "country_name": "Côte d'Ivoire",
                "slug": "cote-divoire",
                "country_code": "CIV",
                "flag_emoji": "🇨🇮",
                "ipa_full_name": "Centre de Promotion des Investissements en Côte d'Ivoire",
                "ipa_acronym": "CEPICI",
                "ipa_website": "https://www.cepici.gouv.ci",
                "overview": "CEPICI is the official investment promotion agency for Côte d'Ivoire.",
                "contact_email": "info@cepici.ci",
                "contact_phone": "+225 27 20 31 88 00",
                "population": 29200000,
                "gdp": 82.60,
                "official_language": "french",
                "capital_city": "Yamoussoukro",
                "currency_name": "West African CFA Franc",
                "currency_code": "XOF",
                "currency_symbol": "CFA",
                "is_active": True,
            },
            {
                "country_name": "The Gambia",
                "slug": "gambia",
                "country_code": "GMB",
                "flag_emoji": "🇬🇲",
                "ipa_full_name": "Gambia Investment and Export Promotion Agency",
                "ipa_acronym": "GIEPA",
                "ipa_website": "https://www.giepa.gm",
                "overview": "GIEPA promotes and facilitates private investment and exports in The Gambia.",
                "contact_email": "info@giepa.gm",
                "contact_phone": "+220 437 6477",
                "population": 2800000,
                "gdp": 2.60,
                "official_language": "english",
                "capital_city": "Banjul",
                "currency_name": "Gambian Dalasi",
                "currency_code": "GMD",
                "currency_symbol": "D",
                "is_active": True,
            },
            {
                "country_name": "Guinea",
                "slug": "guinea",
                "country_code": "GIN",
                "flag_emoji": "🇬🇳",
                "ipa_full_name": "Guinea Development Board",
                "ipa_acronym": "GDB",
                "ipa_website": "https://www.invest.gov.gn",
                "overview": "The Guinea Development Board improves the business climate and supports investment facilitation in Guinea.",
                "contact_email": "contact@invest.gov.gn",
                "contact_phone": "+224 622 20 10 10",
                "population": 14500000,
                "gdp": 21.70,
                "official_language": "french",
                "capital_city": "Conakry",
                "currency_name": "Guinean Franc",
                "currency_code": "GNF",
                "currency_symbol": "GF",
                "is_active": True,
            },
            {
                "country_name": "Guinea-Bissau",
                "slug": "guinea-bissau",
                "country_code": "GNB",
                "flag_emoji": "🇬🇼",
                "ipa_full_name": "Centro de Promoção do Investimento",
                "ipa_acronym": "CPI-GB",
                "ipa_website": "https://www.cpi-guineabissau.com",
                "overview": "CPI-GB promotes private investment and economic diversification in Guinea-Bissau.",
                "contact_email": "info@cpi-gb.org",
                "contact_phone": "+245 955 263 333",
                "population": 2100000,
                "gdp": 2.10,
                "official_language": "portuguese",
                "capital_city": "Bissau",
                "currency_name": "West African CFA Franc",
                "currency_code": "XOF",
                "currency_symbol": "CFA",
                "is_active": True,
            },
            {
                "country_name": "Liberia",
                "slug": "liberia",
                "country_code": "LBR",
                "flag_emoji": "🇱🇷",
                "ipa_full_name": "National Investment Commission",
                "ipa_acronym": "NIC",
                "ipa_website": "https://www.nic.gov.lr",
                "overview": "NIC promotes and facilitates both domestic and foreign investments in Liberia.",
                "contact_email": "info@nic.gov.lr",
                "contact_phone": "+231 77 007 0000",
                "population": 5500000,
                "gdp": 5.10,
                "official_language": "english",
                "capital_city": "Monrovia",
                "currency_name": "Liberian Dollar",
                "currency_code": "LRD",
                "currency_symbol": "$",
                "is_active": True,
            },
            {
                "country_name": "Senegal",
                "slug": "senegal",
                "country_code": "SEN",
                "flag_emoji": "🇸🇳",
                "ipa_full_name": "Agence Nationale chargée de la Promotion de l'Investissement et des Grands Travaux",
                "ipa_acronym": "APIX",
                "ipa_website": "https://www.investinsenegal.com",
                "overview": "APIX promotes private investment and manages major infrastructure projects in Senegal.",
                "contact_email": "contact@apix.sn",
                "contact_phone": "+221 33 849 05 55",
                "population": 18600000,
                "gdp": 36.90,
                "official_language": "french",
                "capital_city": "Dakar",
                "currency_name": "West African CFA Franc",
                "currency_code": "XOF",
                "currency_symbol": "CFA",
                "is_active": True,
            },
            {
                "country_name": "Sierra Leone",
                "slug": "sierra-leone",
                "country_code": "SLE",
                "flag_emoji": "🇸🇱",
                "ipa_full_name": "National Investment Board",
                "ipa_acronym": "NIB-SL",
                "ipa_website": "https://www.nib.gov.sl",
                "overview": "The National Investment Board promotes and facilitates investment and exports in Sierra Leone.",
                "contact_email": "info@nib.gov.sl",
                "contact_phone": "+232 76 610 610",
                "population": 8800000,
                "gdp": 6.70,
                "official_language": "english",
                "capital_city": "Freetown",
                "currency_name": "Sierra Leonean Leone",
                "currency_code": "SLL",
                "currency_symbol": "Le",
                "is_active": True,
            },
            {
                "country_name": "Togo",
                "slug": "togo",
                "country_code": "TGO",
                "flag_emoji": "🇹🇬",
                "ipa_full_name": "Centre de Formalités des Entreprises et de Promotion des Investissements",
                "ipa_acronym": "CEPICI-Togo",
                "ipa_website": "https://www.investingtogo.tg",
                "overview": "Togo's investment promotion agency facilitates investment and free zone development.",
                "contact_email": "contact@cepici.tg",
                "contact_phone": "+228 22 21 03 91",
                "population": 9300000,
                "gdp": 9.80,
                "official_language": "french",
                "capital_city": "Lomé",
                "currency_name": "West African CFA Franc",
                "currency_code": "XOF",
                "currency_symbol": "CFA",
                "is_active": True,
            },
        ]

        member_states = []
        for data in states_data:
            state, created = MemberStateIPA.objects.get_or_create(slug=data["slug"], defaults=data)
            member_states.append(state)
            status = "✓" if created else "↻"
            self.stdout.write(f"  {status} {state.ipa_acronym} - {state.country_name}")

        self.stdout.write(self.style.SUCCESS(f"✓ Created {len(member_states)} member states"))
        return member_states

    def create_hq_admins(self):
        """Create IPAWAS HQ administrators"""
        self.stdout.write("Creating HQ Administrators...")

        admins_data = [
            {
                "email": "admin@ipawas.org",
                "first_name": "Ibrahim",
                "last_name": "Mensah",
                "job_title": "Executive Director",
                "phone": "+234 906 204 0061",
            },
            {
                "email": "operations@ipawas.org",
                "first_name": "Amina",
                "last_name": "Diallo",
                "job_title": "Operations Manager",
                "phone": "+234 906 204 0062",
            },
            {
                "email": "programs@ipawas.org",
                "first_name": "Kwame",
                "last_name": "Osei",
                "job_title": "Programs Coordinator",
                "phone": "+234 906 204 0063",
            },
        ]

        admins = []
        for data in admins_data:
            user, created = User.objects.get_or_create(
                email=data["email"],
                defaults={
                    "first_name": data["first_name"],
                    "last_name": data["last_name"],
                    "user_type": "ipawas_admin",
                    "is_staff": True,
                    "is_active": True,
                    "email_verified": True,
                    "phone_number": data.get("phone", ""),
                },
            )

            if created:
                password = "Ipawas2025!"
                user.set_password(password)
                user.save()

                self.credentials.append(
                    {
                        "type": "HQ Admin",
                        "name": user.get_full_name(),
                        "email": user.email,
                        "password": password,
                        "role": data.get("job_title", "Administrator"),
                    }
                )

            admins.append(user)
            status = "✓" if created else "↻"
            self.stdout.write(f"  {status} {user.get_full_name()} ({user.email})")

        self.stdout.write(self.style.SUCCESS(f"✓ Created {len(admins)} HQ admins"))
        return admins

    def create_ipa_staff(self, member_state):
        """Create IPA staff for a member state"""

        staff_templates = [
            {
                "role": "ipa_director",
                "title": "Director General",
                "permissions": {
                    "can_edit_profile": True,
                    "can_create_opportunities": True,
                    "can_publish_opportunities": True,
                    "can_manage_users": True,
                    "can_view_analytics": True,
                },
                "is_primary": True,
            },
            {
                "role": "ipa_officer",
                "title": "Investment Officer",
                "permissions": {
                    "can_edit_profile": True,
                    "can_create_opportunities": True,
                    "can_publish_opportunities": False,
                    "can_manage_users": False,
                    "can_view_analytics": True,
                },
                "is_primary": False,
            },
            {
                "role": "ipa_data_entry",
                "title": "Data Analyst",
                "permissions": {
                    "can_edit_profile": False,
                    "can_create_opportunities": True,
                    "can_publish_opportunities": False,
                    "can_manage_users": False,
                    "can_view_analytics": True,
                },
                "is_primary": False,
            },
        ]

        first_names = [
            "Ade",
            "Kofi",
            "Amara",
            "Femi",
            "Zainab",
            "Yaw",
            "Ama",
            "Sekou",
            "Fatou",
            "Kwesi",
            "Nana",
            "Binta",
            "Abdul",
            "Aissatou",
            "Moussa",
        ]
        last_names = [
            "Adeyemi",
            "Mensah",
            "Kamara",
            "Diop",
            "Traore",
            "Koné",
            "Sow",
            "Ba",
            "Ndiaye",
            "Diallo",
            "Sesay",
            "Keita",
            "Touré",
        ]

        staff_members = []
        for idx, template in enumerate(staff_templates):
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            email = f"{first_name.lower()}.{last_name.lower()}@{member_state.slug}.ipa"

            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "first_name": first_name,
                    "last_name": last_name,
                    "user_type": "ipa_staff",
                    "is_active": True,
                    "email_verified": True,
                    "phone_number": f"+{random.randint(200, 999)} {random.randint(10, 99)} {random.randint(1000, 9999)} {random.randint(1000, 9999)}",
                },
            )

            if created:
                password = f"{member_state.ipa_acronym}2025!"
                user.set_password(password)
                user.save()

                ipa_profile, _ = IPAUser.objects.get_or_create(
                    user=user,
                    defaults={
                        "member_state": member_state,
                        "role": template["role"],
                        "is_primary_contact": template["is_primary"],
                        **template["permissions"],
                    },
                )

                self.credentials.append(
                    {
                        "type": "IPA Staff",
                        "country": member_state.country_name,
                        "ipa": member_state.ipa_acronym,
                        "name": user.get_full_name(),
                        "email": user.email,
                        "password": password,
                        "role": template["title"],
                    }
                )

            staff_members.append(user)

        self.stdout.write(f"  ✓ {member_state.ipa_acronym}: {len(staff_members)} staff members")
        return staff_members

    def create_sectors(self):
        """Create investment sectors"""
        self.stdout.write("Creating Sectors...")

        try:
            from core.models import Sector
        except ImportError:
            self.stdout.write(self.style.WARNING("  ⚠ Sector model not found, skipping"))
            return []

        sectors_data = [
            {
                "name": "Agriculture & Agribusiness",
                "slug": "agriculture-agribusiness",
                "description": "Agricultural production, processing, and value chain development across West Africa.",
                "icon_class": "fa-seedling",
                "color": "#4CAF50",
            },
            {
                "name": "Energy & Renewable Energy",
                "slug": "energy-renewable",
                "description": "Power generation, distribution, and renewable energy projects including solar and wind.",
                "icon_class": "fa-bolt",
                "color": "#FF9800",
            },
            {
                "name": "Manufacturing & Industrial Parks",
                "slug": "manufacturing",
                "description": "Industrial manufacturing, processing facilities, and special economic zones.",
                "icon_class": "fa-industry",
                "color": "#607D8B",
            },
            {
                "name": "ICT & Digital Economy",
                "slug": "ict-digital",
                "description": "Information technology, telecommunications, fintech, and digital services.",
                "icon_class": "fa-microchip",
                "color": "#2196F3",
            },
            {
                "name": "Infrastructure & Logistics",
                "slug": "infrastructure-logistics",
                "description": "Transportation, ports, roads, railways, and logistics infrastructure.",
                "icon_class": "fa-road",
                "color": "#795548",
            },
            {
                "name": "Mining & Natural Resources",
                "slug": "mining-natural-resources",
                "description": "Mineral extraction, processing, and sustainable resource management.",
                "icon_class": "fa-gem",
                "color": "#9C27B0",
            },
            {
                "name": "Tourism & Hospitality",
                "slug": "tourism-hospitality",
                "description": "Hotels, resorts, eco-tourism, and cultural heritage tourism development.",
                "icon_class": "fa-umbrella-beach",
                "color": "#00BCD4",
            },
            {
                "name": "Financial Services",
                "slug": "financial-services",
                "description": "Banking, insurance, investment funds, and financial technology.",
                "icon_class": "fa-university",
                "color": "#3F51B5",
            },
        ]

        sectors = []
        for data in sectors_data:
            slug = data.pop("slug")
            sector, created = Sector.objects.get_or_create(slug=slug, defaults=data)
            sectors.append(sector)
            status = "✓" if created else "↻"
            self.stdout.write(f"  {status} {sector.name}")

        self.stdout.write(self.style.SUCCESS(f"✓ Created {len(sectors)} sectors"))
        return sectors

    def create_investment_incentives(self):
        """Create investment incentives for each country"""
        self.stdout.write("Creating Investment Incentives...")

        try:
            from members.models import InvestmentIncentive
        except ImportError:
            self.stdout.write(
                self.style.WARNING("  ⚠ InvestmentIncentive model not found, skipping")
            )
            return

        incentives_count = 0
        for state in self.member_states[:6]:  # Sample for first 6 countries
            years = random.choice([5, 7, 10])
            incentives_templates = [
                {
                    "title": "Tax Holiday",
                    "description": f"Enjoy {years} years of corporate tax exemption for qualifying investments.",
                    "incentive_type": "tax_holiday",
                    "duration": f"{years} years",
                },
                {
                    "title": "Free Zone Benefits",
                    "description": "Tax-free operations, duty-free imports, and simplified regulatory procedures.",
                    "incentive_type": "free_zone",
                    "duration": "Ongoing",
                },
                {
                    "title": "Import Duty Exemption",
                    "description": "Exemption from customs duties on machinery, equipment, and raw materials.",
                    "incentive_type": "customs_exemption",
                    "duration": "Ongoing",
                },
            ]

            for inc_data in incentives_templates:
                title = inc_data["title"]
                defaults = {k: v for k, v in inc_data.items() if k != "title"}
                InvestmentIncentive.objects.get_or_create(
                    member_state=state, title=title, defaults=defaults
                )
                incentives_count += 1

        self.stdout.write(self.style.SUCCESS(f"✓ Created {incentives_count} incentives"))

    def create_investment_opportunities(self):
        """Create investment opportunities"""
        self.stdout.write("Creating Investment Opportunities...")

        try:
            from opportunities.models import InvestmentOpportunity
        except ImportError:
            self.stdout.write(
                self.style.WARNING("  ⚠ InvestmentOpportunity model not found, skipping")
            )
            return

        opportunities_templates = [
            # Agriculture
            {
                "title": "Rice Processing and Export Facility",
                "sector_idx": 0,  # Agriculture
                "summary": "Establish modern rice milling and packaging facility for domestic consumption and export to regional markets.",
                "investment_min": 5000000,
                "investment_max": 15000000,
                "opportunity_type": "greenfield",
                "project_stage": "ready-to-implement",
            },
            {
                "title": "Cassava Processing Plant",
                "sector_idx": 0,
                "summary": "High-capacity cassava processing for starch, flour, and ethanol production.",
                "investment_min": 3000000,
                "investment_max": 8000000,
                "opportunity_type": "greenfield",
                "project_stage": "feasibility",
            },
            # Energy
            {
                "title": "Solar Power Generation Project",
                "sector_idx": 1,  # Energy
                "summary": "50MW solar photovoltaic power plant with grid connection and power purchase agreement.",
                "investment_min": 40000000,
                "investment_max": 60000000,
                "opportunity_type": "ppp",
                "project_stage": "ready-to-implement",
            },
            {
                "title": "Mini-Grid Rural Electrification",
                "sector_idx": 1,
                "summary": "Solar-hybrid mini-grids to provide electricity to underserved rural communities.",
                "investment_min": 2000000,
                "investment_max": 5000000,
                "opportunity_type": "greenfield",
                "project_stage": "concept",
            },
            # Manufacturing
            {
                "title": "Pharmaceutical Manufacturing Plant",
                "sector_idx": 2,  # Manufacturing
                "summary": "GMP-certified pharmaceutical manufacturing facility for essential medicines.",
                "investment_min": 20000000,
                "investment_max": 50000000,
                "opportunity_type": "greenfield",
                "project_stage": "feasibility",
            },
            {
                "title": "Textile and Garment Factory",
                "sector_idx": 2,
                "summary": "Integrated textile manufacturing and garment production for export markets.",
                "investment_min": 10000000,
                "investment_max": 25000000,
                "opportunity_type": "greenfield",
                "project_stage": "ready-to-implement",
            },
            # ICT
            {
                "title": "Data Center Development",
                "sector_idx": 3,  # ICT
                "summary": "Tier III data center facility to serve growing cloud computing and hosting demand.",
                "investment_min": 30000000,
                "investment_max": 70000000,
                "opportunity_type": "greenfield",
                "project_stage": "concept",
            },
            # Infrastructure
            {
                "title": "Container Terminal Expansion",
                "sector_idx": 4,  # Infrastructure
                "summary": "Expand port container handling capacity with modern equipment and warehousing.",
                "investment_min": 100000000,
                "investment_max": 200000000,
                "opportunity_type": "ppp",
                "project_stage": "ready-to-implement",
            },
            {
                "title": "Industrial Park Development",
                "sector_idx": 4,
                "summary": "Develop fully-serviced industrial park with power, water, and logistics infrastructure.",
                "investment_min": 50000000,
                "investment_max": 150000000,
                "opportunity_type": "ppp",
                "project_stage": "feasibility",
            },
            # Tourism
            {
                "title": "Beach Resort and Spa",
                "sector_idx": 6,  # Tourism
                "summary": "4-star beach resort with 150 rooms, conference facilities, and wellness spa.",
                "investment_min": 15000000,
                "investment_max": 30000000,
                "opportunity_type": "greenfield",
                "project_stage": "ready-to-implement",
            },
        ]

        opportunities_count = 0
        for state in self.member_states:
            # Create 2-4 opportunities per country
            num_opps = random.randint(2, 4)
            selected_templates = random.sample(
                opportunities_templates, min(num_opps, len(opportunities_templates))
            )

            for template in selected_templates:
                sector = self.sectors[template["sector_idx"]] if self.sectors else None
                # Make title unique per country to avoid slug collisions
                title = f"{template['title']} – {state.country_name}"

                opp_data = {
                    "primary_country": state,
                    "primary_sector": sector,
                    "summary": template["summary"],
                    "investment_required_min": Decimal(template["investment_min"]),
                    "investment_required_max": Decimal(template["investment_max"]),
                    "opportunity_type": template["opportunity_type"],
                    "project_stage": template["project_stage"],
                    "status": "draft",
                    "priority_level": random.choice(["high", "medium", "standard"]),
                    "featured": random.choice([True, False]),
                    "created_by": random.choice(
                        self.all_ipa_staff.get(state.slug, [self.hq_admins[0]])
                    ),
                }

                InvestmentOpportunity.objects.get_or_create(
                    primary_country=state, title=title, defaults=opp_data
                )
                opportunities_count += 1

        self.stdout.write(self.style.SUCCESS(f"✓ Created {opportunities_count} opportunities"))

    def create_events(self):
        """Create events (forums, workshops, webinars)"""
        self.stdout.write("Creating Events...")

        try:
            from core.models import Event
        except ImportError:
            self.stdout.write(self.style.WARNING("  ⚠ Event model not found, skipping"))
            return

        events_data = [
            {
                "title": "West Africa Investment Forum 2025",
                "event_type": "forum",
                "description": "Annual regional investment promotion forum bringing together investors, IPAs, and policymakers.",
                "start_date": timezone.now() + timedelta(days=90),
                "duration_days": 2,
                "is_virtual": False,
                "country_idx": 0,  # Nigeria
                "city": "Abuja",
            },
            {
                "title": "IPA Capacity Building Workshop",
                "event_type": "workshop",
                "description": "Training workshop on modern investment promotion strategies and digital tools.",
                "start_date": timezone.now() + timedelta(days=45),
                "duration_days": 3,
                "is_virtual": False,
                "country_idx": 1,  # Ghana
                "city": "Accra",
            },
            {
                "title": "Renewable Energy Investor Webinar",
                "event_type": "webinar",
                "description": "Online presentation of solar and wind investment opportunities across West Africa.",
                "start_date": timezone.now() + timedelta(days=30),
                "duration_days": 1,
                "is_virtual": True,
                "country_idx": None,
                "city": "Online",
            },
            {
                "title": "Agriculture Investment Roundtable",
                "event_type": "conference",
                "description": "High-level discussion on agricultural transformation and investment needs.",
                "start_date": timezone.now() + timedelta(days=60),
                "duration_days": 1,
                "is_virtual": False,
                "country_idx": 9,  # Senegal
                "city": "Dakar",
            },
        ]

        events_count = 0
        for event_data in events_data:
            start_dt = event_data["start_date"]
            end_dt = start_dt + timedelta(days=event_data["duration_days"])
            host_country = (
                self.member_states[event_data["country_idx"]]
                if event_data["country_idx"] is not None
                else None
            )

            Event.objects.get_or_create(
                title=event_data["title"],
                defaults={
                    "event_type": event_data["event_type"],
                    "description": event_data["description"],
                    "start_date": start_dt.date(),
                    "end_date": end_dt.date(),
                    "is_virtual": event_data["is_virtual"],
                    "host_country": host_country,
                    "city": event_data["city"],
                    "status": "upcoming",
                    "created_by": self.hq_admins[0],
                },
            )
            events_count += 1

        self.stdout.write(self.style.SUCCESS(f"✓ Created {events_count} events"))

    def create_publications(self):
        """Create publications and documents"""
        self.stdout.write("Creating Publications...")

        try:
            from core.models import Publication
        except ImportError:
            self.stdout.write(self.style.WARNING("  ⚠ Publication model not found, skipping"))
            return

        publications_data = [
            {
                "title": "IPAWAS Annual Report 2024",
                "pub_type": "annual_report",
                "description": "Comprehensive overview of IPAWAS activities, achievements, and financial performance.",
                "year": 2024,
            },
            {
                "title": "West Africa FDI Trends 2024",
                "pub_type": "investment_report",
                "description": "Analysis of foreign direct investment flows, sectors, and source countries.",
                "year": 2024,
            },
            {
                "title": "Investment Climate Policy Brief",
                "pub_type": "policy_brief",
                "description": "Recommendations for improving the regional investment climate.",
                "year": 2025,
            },
            {
                "title": "Agribusiness Investment Guide",
                "pub_type": "guide",
                "description": "Comprehensive guide to agricultural investment opportunities in West Africa.",
                "year": 2025,
            },
        ]

        pubs_count = 0
        for pub_data in publications_data:
            pub_date = (timezone.now() - timedelta(days=random.randint(30, 180))).date()
            Publication.objects.get_or_create(
                title=pub_data["title"],
                defaults={
                    "publication_type": pub_data["pub_type"],
                    "description": pub_data["description"],
                    "year": pub_data["year"],
                    "published": True,
                    "publication_date": pub_date,
                    "created_by": self.hq_admins[0],
                },
            )
            pubs_count += 1

        self.stdout.write(self.style.SUCCESS(f"✓ Created {pubs_count} publications"))

    # def create_news_articles(self):
    #     """Create news articles"""
    #     self.stdout.write("Creating News Articles...")

    #     try:
    #         from core.models import NewsArticle
    #     except ImportError:
    #         self.stdout.write(self.style.WARNING("  ⚠ NewsArticle model not found, skipping"))
    #         return

    #     news_data = [
    #         {
    #             "title": "IPAWAS Launches New Investment Portal",
    #             "summary": "Enhanced digital platform streamlines investor access to regional opportunities.",
    #             "category": "platform",
    #         },
    #         {
    #             "title": "Ghana Attracts $500M Manufacturing Investment",
    #             "summary": "Major pharmaceutical company announces new production facility in Accra.",
    #             "category": "success_story",
    #         },
    #         {
    #             "title": "Regional Renewable Energy Initiative Launched",
    #             "summary": "IPAWAS partners with development banks to promote solar investments.",
    #             "category": "program",
    #         },
    #     ]

    #     news_count = 0
    #     for article_data in news_data:
    #         NewsArticle.objects.get_or_create(
    #             title=article_data["title"],
    #             defaults={
    #                 "summary": article_data["summary"],
    #                 "category": article_data["category"],
    #                 "published": True,
    #                 "published_date": timezone.now() - timedelta(days=random.randint(1, 30)),
    #                 "author": self.hq_admins[1],
    #             },
    #         )
    #         news_count += 1

    #     self.stdout.write(self.style.SUCCESS(f"✓ Created {news_count} news articles"))

    def create_success_stories(self):
        """Create success stories"""
        self.stdout.write("Creating Success Stories...")

        try:
            from members.models import SuccessStory
        except ImportError:
            self.stdout.write(self.style.WARNING("  ⚠ SuccessStory model not found, skipping"))
            return

        stories_data = [
            {
                "title": "Solar Farm Powers 50,000 Homes in Senegal",
                "country_idx": 9,  # Senegal
                "sector_idx": 1,  # Energy
                "summary": "European investor partners with APIX to develop 40MW solar facility.",
                "company_name": "SolarAfrica GmbH",
                "investment_amount": 35000000,
                "year": 2024,
            },
            {
                "title": "Tech Hub Creates 2,000 Jobs in Nigeria",
                "country_idx": 0,  # Nigeria
                "sector_idx": 3,  # ICT
                "summary": "International technology company establishes development center in Lagos.",
                "company_name": "TechBridge International",
                "investment_amount": 25000000,
                "year": 2024,
            },
        ]

        stories_count = 0
        for story_data in stories_data:
            country = self.member_states[story_data["country_idx"]]
            sector = self.sectors[story_data["sector_idx"]] if self.sectors else None

            SuccessStory.objects.get_or_create(
                title=story_data["title"],
                defaults={
                    "member_state": country,
                    "sector": sector,
                    "company_name": story_data["company_name"],
                    "summary": story_data["summary"],
                    "investment_amount": Decimal(story_data["investment_amount"]),
                    "year": story_data["year"],
                    "featured": True,
                    "published": True,
                },
            )
            stories_count += 1

        self.stdout.write(self.style.SUCCESS(f"✓ Created {stories_count} success stories"))

    def create_fdi_data(self):
        """Create FDI data points for WAIIS"""
        self.stdout.write("Creating FDI Data Points...")

        try:
            from members.models import FDIDataPoint
        except ImportError:
            self.stdout.write(self.style.WARNING("  ⚠ FDIDataPoint model not found, skipping"))
            return

        data_points = 0
        years = [2022, 2023, 2024]
        data_sources = ["UNCTAD", "World Bank", "IMF", "National Statistics Office", "Central Bank"]

        for state in self.member_states:  # All member states
            base_gdp = float(state.gdp or 0) * 1_000_000_000  # gdp stored in billions
            base_fdi_inflow = base_gdp * random.uniform(0.02, 0.05)  # 2-5% of GDP
            base_fdi_stock = base_fdi_inflow * random.uniform(5, 10)  # Stock is cumulative
            base_trade = base_gdp * random.uniform(0.3, 0.6)  # 30-60% of GDP

            for year in years:
                # Add some year-over-year growth/decline
                year_factor = 1 + ((year - 2022) * random.uniform(-0.05, 0.15))

                # FDI Inflow
                fdi_inflow_value = base_fdi_inflow * year_factor
                FDIDataPoint.objects.get_or_create(
                    member_state=state,
                    data_type="fdi_inflow",
                    year=year,
                    defaults={
                        "value": Decimal(fdi_inflow_value / 1_000_000),  # Convert to millions
                        "value_display": f"${fdi_inflow_value/1_000_000:,.1f}M",
                        "data_source": random.choice(data_sources),
                        "validation_status": random.choice(
                            ["published", "published", "under_review"]
                        ),
                        "notes": f"FDI inflow data for {year} from official sources.",
                    },
                )
                data_points += 1

                # FDI Outflow (smaller, usually)
                fdi_outflow_value = fdi_inflow_value * random.uniform(0.1, 0.3)
                FDIDataPoint.objects.get_or_create(
                    member_state=state,
                    data_type="fdi_outflow",
                    year=year,
                    defaults={
                        "value": Decimal(fdi_outflow_value / 1_000_000),
                        "value_display": f"${fdi_outflow_value/1_000_000:,.1f}M",
                        "data_source": random.choice(data_sources),
                        "validation_status": "published",
                        "notes": f"FDI outflow data for {year}.",
                    },
                )
                data_points += 1

                # FDI Stock (cumulative)
                fdi_stock_value = base_fdi_stock * year_factor
                FDIDataPoint.objects.get_or_create(
                    member_state=state,
                    data_type="fdi_stock",
                    year=year,
                    defaults={
                        "value": Decimal(fdi_stock_value / 1_000_000),
                        "value_display": f"${fdi_stock_value/1_000_000:,.1f}M",
                        "data_source": random.choice(data_sources),
                        "validation_status": "published",
                        "notes": f"Total FDI stock as of end of {year}.",
                    },
                )
                data_points += 1

                # GDP
                gdp_value = base_gdp * year_factor
                FDIDataPoint.objects.get_or_create(
                    member_state=state,
                    data_type="gdp",
                    year=year,
                    defaults={
                        "value": Decimal(gdp_value / 1_000_000),
                        "value_display": f"${gdp_value/1_000_000_000:,.1f}B",
                        "data_source": random.choice(
                            ["World Bank", "IMF", "National Statistics Office"]
                        ),
                        "validation_status": "published",
                        "notes": f"GDP at current prices for {year}.",
                    },
                )
                data_points += 1

                # Trade Volume
                trade_value = base_trade * year_factor
                FDIDataPoint.objects.get_or_create(
                    member_state=state,
                    data_type="trade_volume",
                    year=year,
                    defaults={
                        "value": Decimal(trade_value / 1_000_000),
                        "value_display": f"${trade_value/1_000_000_000:,.1f}B",
                        "data_source": "WTO",
                        "validation_status": "published",
                        "notes": f"Total trade (exports + imports) for {year}.",
                    },
                )
                data_points += 1

        self.stdout.write(self.style.SUCCESS(f"✓ Created {data_points} FDI data points"))

    def create_activities(self, member_states, hq_admins, all_ipa_staff):
        """Create sample dashboard activities"""
        self.stdout.write("Creating Dashboard Activities...")

        activities_created = 0

        for admin in hq_admins[:2]:
            for i in range(5):
                IPADashboardActivity.objects.create(
                    user=admin,
                    action_type=random.choice(["login", "profile_view", "settings_change"]),
                    description=f"{admin.get_full_name()} performed system administration",
                    timestamp=timezone.now() - timedelta(days=random.randint(1, 30)),
                )
                activities_created += 1

        for state in member_states[:5]:
            staff = all_ipa_staff.get(state.slug, [])
            for user in staff:
                actions = [
                    ("login", f"{user.get_full_name()} logged into dashboard"),
                    ("opportunity_create", f"Created investment opportunity"),
                    ("profile_update", f"Updated {state.ipa_acronym} profile"),
                    ("inquiry_view", f"Viewed investor inquiry"),
                ]

                for action_type, desc in random.sample(actions, 2):
                    IPADashboardActivity.objects.create(
                        user=user,
                        member_state=state,
                        action_type=action_type,
                        description=desc,
                        timestamp=timezone.now() - timedelta(days=random.randint(1, 14)),
                    )
                    activities_created += 1

        self.stdout.write(self.style.SUCCESS(f"✓ Created {activities_created} activities"))

    def create_notifications(self, member_states, all_ipa_staff):
        """Create sample notifications"""
        self.stdout.write("Creating Notifications...")

        notifications_created = 0

        for state in member_states[:6]:
            staff = all_ipa_staff.get(state.slug, [])
            primary_contact = next(
                (
                    s
                    for s in staff
                    if hasattr(s, "ipa_profile") and s.ipa_profile.is_primary_contact
                ),
                None,
            )

            if primary_contact:

                ipa_user = IPAUser.objects.get(user=primary_contact)

                notifications = [
                    {
                        "type": "inquiry",
                        "title": "New Investor Inquiry",
                        "message": "A new inquiry has been submitted regarding manufacturing opportunities.",
                    },
                    {
                        "type": "approval_needed",
                        "title": "Content Pending Approval",
                        "message": "Investment opportunity draft needs your review.",
                    },
                ]

                for notif in notifications:
                    IPANotification.objects.create(
                        recipient=ipa_user,
                        notification_type=notif["type"],
                        title=notif["title"],
                        message=notif["message"],
                        is_read=random.choice([True, False]),
                        created_at=timezone.now() - timedelta(days=random.randint(1, 7)),
                    )
                    notifications_created += 1

        self.stdout.write(self.style.SUCCESS(f"✓ Created {notifications_created} notifications"))

    def create_invitations(self, member_states, hq_admins):
        """Create sample pending invitations"""
        self.stdout.write("Creating Sample Invitations...")

        invitations_created = 0

        for state in member_states[:4]:
            try:
                Invitation.objects.create(
                    email=f"pending.invite@{state.slug}.ipa",
                    member_state=state,
                    role="ipa_officer",
                    invited_by=random.choice(hq_admins),
                    invited_at=timezone.now() - timedelta(days=3),
                    expires_at=timezone.now() + timedelta(days=4),
                    status="pending",
                )
                invitations_created += 1
            except Exception:
                pass  # Skip if duplicate pending invitation exists

        self.stdout.write(self.style.SUCCESS(f"✓ Created {invitations_created} invitations"))

    def save_credentials(self):
        """Save all credentials to file"""
        import os
        from django.conf import settings
        output_path = os.path.join(settings.BASE_DIR, "credentials.txt")

        with open(output_path, "w") as f:
            f.write("=" * 80 + "\n")
            f.write("IPAWAS PLATFORM - COMPLETE TEST CREDENTIALS\n")
            f.write("Generated: " + timezone.now().strftime("%Y-%m-%d %H:%M:%S") + "\n")
            f.write("=" * 80 + "\n\n")

            f.write("HQ ADMINISTRATORS\n")
            f.write("-" * 80 + "\n")
            for cred in [c for c in self.credentials if c["type"] == "HQ Admin"]:
                f.write(f"Name: {cred['name']}\n")
                f.write(f"Email: {cred['email']}\n")
                f.write(f"Password: {cred['password']}\n")
                f.write(f"Role: {cred['role']}\n")
                f.write("-" * 80 + "\n")

            f.write("\n\nIPA STAFF BY MEMBER STATE\n")
            f.write("=" * 80 + "\n")

            current_country = None
            for cred in [c for c in self.credentials if c["type"] == "IPA Staff"]:
                if current_country != cred["country"]:
                    current_country = cred["country"]
                    f.write(f"\n{cred['country']} ({cred['ipa']})\n")
                    f.write("-" * 80 + "\n")

                f.write(f"Name: {cred['name']}\n")
                f.write(f"Email: {cred['email']}\n")
                f.write(f"Password: {cred['password']}\n")
                f.write(f"Role: {cred['role']}\n")
                f.write("\n")

            f.write("\n" + "=" * 80 + "\n")
            f.write("LOGIN URL: https://your-domain.com/dashboard/login/\n")
            f.write("=" * 80 + "\n")

    def print_summary(self):
        """Print summary of created data"""
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(self.style.SUCCESS("DATA CREATION SUMMARY"))
        self.stdout.write("=" * 80)

        self.stdout.write(f"Member States: {MemberStateIPA.objects.count()}")
        self.stdout.write(f"HQ Admins: {User.objects.filter(user_type='ipawas_admin').count()}")
        self.stdout.write(f"IPA Staff: {User.objects.filter(user_type='ipa_staff').count()}")

        try:

            self.stdout.write(f"Sectors: {Sector.objects.count()}")
            self.stdout.write(f"Investment Opportunities: {InvestmentOpportunity.objects.count()}")
            self.stdout.write(f"Events: {Event.objects.count()}")
            self.stdout.write(f"Publications: {Publication.objects.count()}")
        except ImportError:
            pass

        try:

            self.stdout.write(f"FDI Data Points: {FDIDataPoint.objects.count()}")
        except ImportError:
            pass

        self.stdout.write(f"Activities: {IPADashboardActivity.objects.count()}")
        self.stdout.write(f"Notifications: {IPANotification.objects.count()}")
        self.stdout.write(f"Invitations: {Invitation.objects.count()}")
        self.stdout.write("=" * 80 + "\n")
