"""
Django Management Command: Populate IPAWAS Database (CORRECTED)
Location: apps/core/management/commands/populate_ipawas.py

Based on ACTUAL model structure:
- InvestmentOpportunity (opportunities/models.py) ✓
- IPADashboardActivity & IPANotification (dashboard/models.py) ✓
- FDIDataPoint (waiis/models.py) ✓
- User, IPAUser (inferred from services.py)
- MemberStateIPA (inferred from InvestmentOpportunity imports)
- Sector (inferred from InvestmentOpportunity imports)
"""

import random
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

User = get_user_model()


class Command(BaseCommand):
    help = "Populate IPAWAS with realistic test data"

    def __init__(self):
        super().__init__()
        self.credentials = []
        self.member_states = []
        self.sectors = []
        self.hq_admins = []
        self.all_ipa_staff = {}

    def add_arguments(self, parser):
        parser.add_argument("--clear", action="store_true", help="Clear existing data")

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("\n🚀 Populating IPAWAS Database...\n"))

        if options["clear"]:
            self.clear_data()

        with transaction.atomic():
            self.stdout.write(self.style.HTTP_INFO("\n📊 PHASE 1: Core Data"))
            self.member_states = self.create_member_states()
            self.sectors = self.create_sectors()
            self.hq_admins = self.create_hq_admins()

            self.stdout.write(self.style.HTTP_INFO("\n👥 PHASE 2: IPA Staff"))
            for state in self.member_states:
                self.all_ipa_staff[state.slug] = self.create_ipa_staff(state)

            self.stdout.write(self.style.HTTP_INFO("\n💼 PHASE 3: Investment Opportunities"))
            # self.create_opportunities()

            self.stdout.write(self.style.HTTP_INFO("\n📈 PHASE 4: FDI Data"))
            self.create_fdi_data()

            self.stdout.write(self.style.HTTP_INFO("\n🔔 PHASE 5: Dashboard"))
            self.create_activities()
            self.create_notifications()

        self.save_credentials()
        self.print_summary()
        self.stdout.write(self.style.SUCCESS("\n✅ Complete!\n"))

    def clear_data(self):
        """Clear data"""
        from dashboard.models import IPADashboardActivity, IPANotification
        from members.models import MemberStateIPA

        try:
            from opportunities.models import InvestmentOpportunity

            InvestmentOpportunity.objects.all().delete()
        except:
            pass

        try:
            from members.models import FDIDataPoint

            FDIDataPoint.objects.all().delete()
        except:
            pass

        try:
            from core.models import Sector

            Sector.objects.all().delete()
        except:
            pass

        try:
            from accounts.models import IPAUser

            IPAUser.objects.all().delete()
        except:
            pass

        IPADashboardActivity.objects.all().delete()
        IPANotification.objects.all().delete()

        User.objects.filter(user_type__in=["ipawas_admin", "ipa_staff"]).delete()
        MemberStateIPA.objects.all().delete()

    def create_member_states(self):
        """Create member states"""
        from members.models import MemberStateIPA

        states = [
            {
                "country_name": "Nigeria",
                "country_code": "NGA",
                "ipa_full_name": "Nigerian Investment Promotion Commission",
                "ipa_acronym": "NIPC",
                "slug": "nigeria",
                "population": 227000000,
                "gdp": Decimal("252000000000"),
                "currency_symbol": "Naira (₦)",
                "official_language": "English",
                "capital_city": "Abuja",
                "contact_email": "info@nipc.gov.ng",
                "contact_phone": "+234 9 461 3000",
                "ipa_website": "https://nipc.gov.ng",
            },
            {
                "country_name": "Ghana",
                "country_code": "GHA",
                "ipa_full_name": "Ghana Investment Promotion Centre",
                "ipa_acronym": "GIPC",
                "slug": "ghana",
                "population": 33800000,
                "gdp": Decimal("87500000000"),
                "currency_symbol": "Cedi (₵)",
                "official_language": "English",
                "capital_city": "Accra",
                "contact_email": "info@gipc.gov.gh",
                "contact_phone": "+233 30 266 5125",
                "ipa_website": "https://gipc.gov.gh",
            },
            {
                "country_name": "Senegal",
                "country_code": "SEN",
                "ipa_full_name": "APIX",
                "ipa_acronym": "APIX",
                "slug": "senegal",
                "population": 18600000,
                "gdp": Decimal("36900000000"),
                "currency_symbol": "CFA Franc",
                "official_language": "French",
                "capital_city": "Dakar",
                "contact_email": "contact@apix.sn",
                "contact_phone": "+221 33 849 05 55",
                "ipa_website": "https://investinsenegal.com",
            },
            {
                "country_name": "Côte d'Ivoire",
                "country_code": "CIV",
                "ipa_full_name": "CEPICI",
                "ipa_acronym": "CEPICI",
                "slug": "cote-divoire",
                "population": 29200000,
                "gdp": Decimal("82600000000"),
                "currency_symbol": "CFA Franc",
                "official_language": "French",
                "capital_city": "Yamoussoukro",
                "contact_email": "info@cepici.ci",
                "contact_phone": "+225 27 20 31 88 00",
                "ipa_website": "https://cepici.gouv.ci",
            },
            {
                "country_name": "Benin",
                "country_code": "BEN",
                "ipa_full_name": "APIEX",
                "ipa_acronym": "APIEX",
                "slug": "benin",
                "population": 13400000,
                "gdp": Decimal("20500000000"),
                "currency_symbol": "CFA Franc",
                "official_language": "French",
                "capital_city": "Porto-Novo",
                "contact_email": "contact@apiex.bj",
                "contact_phone": "+229 21 31 55 70",
                "ipa_website": "https://apiex.bj",
            },
            {
                "country_name": "Togo",
                "country_code": "TGO",
                "ipa_full_name": "CFE Togo",
                "ipa_acronym": "CFE",
                "slug": "togo",
                "population": 9300000,
                "gdp": Decimal("9800000000"),
                "currency_symbol": "CFA Franc",
                "official_language": "French",
                "capital_city": "Lomé",
                "contact_email": "contact@cfe.tg",
                "contact_phone": "+228 22 21 03 91",
                "ipa_website": "https://investingtogo.tg",
            },
        ]

        result = []
        for data in states:
            state, _ = MemberStateIPA.objects.get_or_create(slug=data["slug"], defaults=data)
            result.append(state)
            self.stdout.write(f"  ✓ {state.ipa_acronym}")

        self.stdout.write(self.style.SUCCESS(f"✓ {len(result)} member states"))
        return result

    def create_sectors(self):
        """Create sectors"""
        try:
            from core.models import Sector
        except ImportError:
            self.stdout.write(self.style.WARNING("  ⚠ Sector model not found"))
            return []

        sectors_data = [
            {"name": "Agriculture & Agribusiness", "slug": "agriculture"},
            {"name": "Energy & Renewable Energy", "slug": "energy"},
            {"name": "Manufacturing & Industry", "slug": "manufacturing"},
            {"name": "ICT & Digital Economy", "slug": "ict"},
            {"name": "Infrastructure & Logistics", "slug": "infrastructure"},
            {"name": "Mining & Natural Resources", "slug": "mining"},
            {"name": "Tourism & Hospitality", "slug": "tourism"},
            # {"name": "Financial Services", "slug": "finance"},
        ]

        result = []
        for data in sectors_data:
            sector, _ = Sector.objects.get_or_create(slug=data["slug"], defaults=data)
            result.append(sector)
            self.stdout.write(f"  ✓ {sector.name}")

        self.stdout.write(self.style.SUCCESS(f"✓ {len(result)} sectors"))
        return result

    def create_hq_admins(self):
        """Create HQ admins"""
        admins_data = [
            {"email": "admin@ipawas.org", "first_name": "Ibrahim", "last_name": "Mensah"},
            {"email": "ops@ipawas.org", "first_name": "Amina", "last_name": "Diallo"},
        ]

        result = []
        for data in admins_data:
            user, created = User.objects.get_or_create(
                email=data["email"],
                defaults={
                    # "username": data["email"],
                    "first_name": data["first_name"],
                    "last_name": data["last_name"],
                    "user_type": "ipawas_admin",
                    "is_staff": True,
                    "is_active": True,
                    "email_verified": True,
                },
            )

            if created:
                password = "Ipawas2025!"
                user.set_password(password)
                user.save()
                self.credentials.append(
                    {
                        "type": "HQ",
                        "name": user.get_full_name(),
                        "email": user.email,
                        "password": password,
                    }
                )

            result.append(user)
            self.stdout.write(f"  ✓ {user.get_full_name()}")

        self.stdout.write(self.style.SUCCESS(f"✓ {len(result)} HQ admins"))
        return result

    def create_ipa_staff(self, state):
        """Create IPA staff for a member state"""
        from accounts.models import IPAUser

        staff_data = [
            {
                "role": "ipa_director",
                "perms": {
                    "can_edit_profile": True,
                    "can_create_opportunities": True,
                    "can_publish_opportunities": True,
                    "can_manage_users": True,
                    "can_view_analytics": True,
                },
                "primary": True,
            },
            {
                "role": "ipa_officer",
                "perms": {
                    "can_edit_profile": True,
                    "can_create_opportunities": True,
                    "can_publish_opportunities": False,
                    "can_manage_users": False,
                    "can_view_analytics": True,
                },
                "primary": False,
            },
        ]

        names = [
            ("Ade", "Adeyemi"),
            ("Kofi", "Mensah"),
            ("Amara", "Kamara"),
            ("Femi", "Diop"),
            ("Zainab", "Traore"),
        ]

        result = []
        for i, template in enumerate(staff_data):
            first, last = random.choice(names)
            email = f"{first.lower()}.{last.lower()}@{state.slug}.ipa"

            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    # "username": email,
                    "first_name": first,
                    "last_name": last,
                    "user_type": "ipa_staff",
                    "is_active": True,
                    "email_verified": True,
                },
            )

            if created:
                password = f"{state.ipa_acronym}2025!"
                user.set_password(password)
                user.save()

                IPAUser.objects.create(
                    user=user,
                    member_state=state,
                    role=template["role"],
                    is_primary_contact=template["primary"],
                    **template["perms"],
                )

                self.credentials.append(
                    {
                        "type": "IPA",
                        "country": state.country_name,
                        "ipa": state.ipa_acronym,
                        "name": user.get_full_name(),
                        "email": user.email,
                        "password": password,
                        "role": template["role"],
                    }
                )

            result.append(user)

        self.stdout.write(f"  ✓ {state.ipa_acronym}: {len(result)} staff")
        return result

    # def create_opportunities(self):
    #     """Create investment opportunities"""
    #     try:
    #         from opportunities.models import InvestmentOpportunity
    #     except ImportError:
    #         self.stdout.write(self.style.WARNING("  ⚠ InvestmentOpportunity not found"))
    #         return

    #     if not self.sectors:
    #         self.stdout.write(self.style.WARNING("  ⚠ No sectors"))
    #         return

    #     templates = [
    #         {
    #             "title": "Rice Processing Facility",
    #             "sector_idx": 0,
    #             "summary": "Modern rice milling and packaging for domestic and export markets.",
    #             "min": Decimal("5000000"),
    #             "max": Decimal("15000000"),
    #             "type": "greenfield",
    #             "stage": "ready",
    #         },
    #         {
    #             "title": "Solar Power Plant",
    #             "sector_idx": 1,
    #             "summary": "50MW solar PV plant with grid connection and PPA.",
    #             "min": Decimal("40000000"),
    #             "max": Decimal("60000000"),
    #             "type": "ppp",
    #             "stage": "feasibility",
    #         },
    #         # {
    #         #     "title": "Pharmaceutical Plant",
    #         #     "sector_idx": 2,
    #         #     "summary": "GMP-certified facility for essential medicines.",
    #         #     "min": Decimal("20000000"),
    #         #     "max": Decimal("50000000"),
    #         #     "type": "greenfield",
    #         #     "stage": "concept",
    #         # },
    #         {
    #             "title": "Data Center",
    #             "sector_idx": 3,
    #             "summary": "Tier III facility for cloud computing.",
    #             "min": Decimal("30000000"),
    #             "max": Decimal("70000000"),
    #             "type": "greenfield",
    #             "stage": "feasibility",
    #         },
    #         # {
    #         #     "title": "Port Expansion",
    #         #     "sector_idx": 4,
    #         #     "summary": "Container terminal expansion with modern equipment.",
    #         #     "min": Decimal("100000000"),
    #         #     "max": Decimal("200000000"),
    #         #     "type": "ppp",
    #         #     "stage": "ready",
    #         # },
    #     ]

    #     count = 0
    #     for state in self.member_states:
    #         num = random.randint(2, 3)
    #         selected = random.sample(templates, min(num, len(templates)))

    #         for t in selected:
    #             staff = self.all_ipa_staff.get(state.slug, [])
    #             creator = random.choice(staff) if staff else self.hq_admins[0]

    #             InvestmentOpportunity.objects.get_or_create(
    #                 title=t["title"],
    #                 summary=t["summary"],
    #                 description=f"Detailed description of {t['title']} project in {state.country_name}.",
    #                 opportunity_type=t["type"],
    #                 primary_sector=self.sectors[t["sector_idx"]],
    #                 primary_country=state,
    #                 project_stage=t["stage"],
    #                 investment_required_min=t["min"],
    #                 investment_required_max=t["max"],
    #                 status=random.choice(["draft", "active", "active", "active"]),
    #                 priority_level=random.choice(["high", "medium", "standard"]),
    #                 published=random.choice([True, True, False]),
    #                 featured=random.choice([True, False, False, False]),
    #                 created_by=creator,
    #             )
    #             count += 1

    #     self.stdout.write(self.style.SUCCESS(f"✓ {count} opportunities"))

    def create_fdi_data(self):
        """Create FDI data"""
        try:
            from members.models import FDIDataPoint
        except ImportError:
            self.stdout.write(self.style.WARNING("  ⚠ FDIDataPoint not found"))
            return

        count = 0
        years = [2022, 2023, 2024]
        sources = ["UNCTAD", "World Bank", "IMF", "Central Bank"]

        for state in self.member_states:
            gdp = float(state.gdp)
            base_fdi = gdp * random.uniform(0.02, 0.05)
            base_stock = base_fdi * random.uniform(5, 10)
            base_trade = gdp * random.uniform(0.3, 0.6)

            for year in years:
                factor = 1 + ((year - 2022) * random.uniform(-0.05, 0.15))

                # FDI Inflow
                val = base_fdi * factor
                FDIDataPoint.objects.get_or_create(
                    member_state=state,
                    data_type="fdi_inflow",
                    year=year,
                    defaults={
                        "value": Decimal(val / 1_000_000),
                        "value_display": f"${val/1_000_000:,.1f}M",
                        "data_source": random.choice(sources),
                        "validation_status": "published",
                    },
                )
                count += 1

                # FDI Stock
                val = base_stock * factor
                FDIDataPoint.objects.get_or_create(
                    member_state=state,
                    data_type="fdi_stock",
                    year=year,
                    defaults={
                        "value": Decimal(val / 1_000_000),
                        "value_display": f"${val/1_000_000:,.1f}M",
                        "data_source": random.choice(sources),
                        "validation_status": "published",
                    },
                )
                count += 1

                # GDP
                val = gdp * factor
                FDIDataPoint.objects.get_or_create(
                    member_state=state,
                    data_type="gdp",
                    year=year,
                    defaults={
                        "value": Decimal(val / 1_000_000),
                        "value_display": f"${val/1_000_000_000:,.1f}B",
                        "data_source": "World Bank",
                        "validation_status": "published",
                    },
                )
                count += 1

                # Trade
                val = base_trade * factor
                FDIDataPoint.objects.get_or_create(
                    member_state=state,
                    data_type="trade_volume",
                    year=year,
                    defaults={
                        "value": Decimal(val / 1_000_000),
                        "value_display": f"${val/1_000_000_000:,.1f}B",
                        "data_source": "WTO",
                        "validation_status": "published",
                    },
                )
                count += 1

        self.stdout.write(self.style.SUCCESS(f"✓ {count} FDI data points"))

    def create_activities(self):
        """Create dashboard activities"""
        from dashboard.models import IPADashboardActivity

        count = 0
        for state in self.member_states[:3]:
            staff = self.all_ipa_staff.get(state.slug, [])
            for user in staff:
                for _ in range(3):
                    IPADashboardActivity.objects.create(
                        user=user,
                        member_state=state,
                        action_type=random.choice(
                            ["login", "opportunity_create", "profile_update"]
                        ),
                        description=f"{user.get_full_name()} performed action",
                        timestamp=timezone.now() - timedelta(days=random.randint(1, 14)),
                    )
                    count += 1

        self.stdout.write(self.style.SUCCESS(f"✓ {count} activities"))

    def create_notifications(self):
        """Create notifications"""
        from accounts.models import IPAUser
        from dashboard.models import IPANotification

        count = 0
        for state in self.member_states[:3]:
            staff = self.all_ipa_staff.get(state.slug, [])
            primary = next(
                (
                    s
                    for s in staff
                    if hasattr(s, "ipa_profile") and s.ipa_profile.is_primary_contact
                ),
                None,
            )

            if primary:
                ipa_user = IPAUser.objects.get(user=primary)
                IPANotification.objects.create(
                    recipient=ipa_user,
                    notification_type="inquiry",
                    title="New Investor Inquiry",
                    message="A new inquiry has been submitted.",
                    is_read=False,
                )
                count += 1

        self.stdout.write(self.style.SUCCESS(f"✓ {count} notifications"))

    # def save_credentials(self):
    #     """Save credentials"""
    #     with open("/mnt/user-data/outputs/credentials.txt", "wb") as f:
    #         f.write("IPAWAS CREDENTIALS\n")
    #         f.write("=" * 80 + "\n\n")

    #         f.write("HQ ADMINS\n" + "-" * 80 + "\n")
    #         for c in [x for x in self.credentials if x["type"] == "HQ"]:
    #             f.write(f"Email: {c['email']}\nPassword: {c['password']}\n\n")

    #         f.write("\nIPA STAFF\n" + "=" * 80 + "\n")
    #         current = None
    #         for c in [x for x in self.credentials if x["type"] == "IPA"]:
    #             if current != c["country"]:
    #                 current = c["country"]
    #                 f.write(f"\n{c['country']} ({c['ipa']})\n" + "-" * 80 + "\n")
    #             f.write(f"Email: {c['email']}\nPassword: {c['password']}\nRole: {c['role']}\n\n")
    def save_credentials(self):
        """Save credentials"""

        output_dir = Path(settings.BASE_DIR) / "outputs"
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / "credentials.txt"

        with open(output_file, "w", encoding="utf-8") as f:
            f.write("IPAWAS CREDENTIALS\n")
            f.write("=" * 80 + "\n\n")

            f.write("HQ ADMINS\n" + "-" * 80 + "\n")
            for c in [x for x in self.credentials if x["type"] == "HQ"]:
                f.write(f"Email: {c['email']}\nPassword: {c['password']}\n\n")

            f.write("\nIPA STAFF\n" + "=" * 80 + "\n")
            current = None
            for c in [x for x in self.credentials if x["type"] == "IPA"]:
                if current != c["country"]:
                    current = c["country"]
                    f.write(f"\n{c['country']} ({c['ipa']})\n" + "-" * 80 + "\n")
                f.write(
                    f"Email: {c['email']}\n" f"Password: {c['password']}\n" f"Role: {c['role']}\n\n"
                )

    def print_summary(self):
        """Print summary"""
        from members.models import MemberStateIPA

        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("SUMMARY")
        self.stdout.write("=" * 80)
        self.stdout.write(f"Member States: {MemberStateIPA.objects.count()}")
        self.stdout.write(f"HQ Admins: {User.objects.filter(user_type='ipawas_admin').count()}")
        self.stdout.write(f"IPA Staff: {User.objects.filter(user_type='ipa_staff').count()}")

        try:
            from opportunities.models import InvestmentOpportunity

            self.stdout.write(f"Opportunities: {InvestmentOpportunity.objects.count()}")
        except:
            pass

        try:
            from members.models import FDIDataPoint

            self.stdout.write(f"FDI Data: {FDIDataPoint.objects.count()}")
        except:
            pass

        self.stdout.write("=" * 80)
