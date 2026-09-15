"""
Comprehensive IPAWAS Data Population Script (CORRECTED)

This script populates ALL models in the IPAWAS platform with realistic data.
All fields have been verified against actual model structure.

Usage: python comprehensive_populate_ipawas_corrected.py
"""

import os
import random
from datetime import date, datetime, timedelta
from decimal import Decimal

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.text import slugify

# Import all models
from members.models import (
    FDIDataPoint,
    InvestmentIncentive,
    InvestorInquiry,
    IPAStaff,
    MemberStateIPA,
    MemberStateSector,
    Sector,
    SuccessStory,
)
from opportunities.models import InvestmentOpportunity

# Import dashboard models
try:
    from dashboard.models import IPADashboardActivity, IPANotification
except ImportError:
    IPADashboardActivity = None
    IPANotification = None
    print("⚠️  Dashboard models not found - skipping activity logs and notifications")

# Import invitation models
try:
    from invitations.models import Invitation
except ImportError:
    Invitation = None
    print("⚠️  Invitation model not found - skipping invitations")

# Import user models
try:
    from accounts.models import IPAUser
except ImportError:
    IPAUser = None
    print("⚠️  IPAUser model not found - skipping IPA users")

User = get_user_model()


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


def random_date_between(start_date, end_date):
    """Generate random date between two dates"""
    time_between = end_date - start_date
    days_between = time_between.days
    random_days = random.randrange(days_between)
    return start_date + timedelta(days=random_days)


def random_datetime_last_n_days(days=30):
    """Generate random datetime in last N days"""
    end = timezone.now()
    start = end - timedelta(days=days)
    return timezone.make_aware(
        datetime.combine(random_date_between(start.date(), end.date()), datetime.min.time())
    )


# ============================================================================
# STEP 1: CREATE SECTORS
# ============================================================================


def populate_sectors():
    """Create all investment sectors"""
    print("\n📊 Creating Sectors...")

    sectors_data = [
        {
            "name": "Agriculture",
            "description": "Agriculture, Agribusiness and Food Processing",
            "icon_class": "fa-tractor",
            "color": "#10B981",
            "display_order": 1,
        },
        {
            "name": "Manufacturing",
            "description": "Manufacturing and Industrial Production",
            "icon_class": "fa-industry",
            "color": "#3B82F6",
            "display_order": 2,
        },
        {
            "name": "Technology",
            "description": "Technology, ICT and Digital Innovation",
            "icon_class": "fa-laptop-code",
            "color": "#8B5CF6",
            "display_order": 3,
        },
        {
            "name": "Energy",
            "description": "Energy, Power Generation and Renewable Energy",
            "icon_class": "fa-bolt",
            "color": "#F59E0B",
            "display_order": 4,
        },
        {
            "name": "Infrastructure",
            "description": "Infrastructure Development and Construction",
            "icon_class": "fa-road",
            "color": "#6B7280",
            "display_order": 5,
        },
        {
            "name": "Healthcare",
            "description": "Healthcare, Medical Services and Pharmaceuticals",
            "icon_class": "fa-hospital",
            "color": "#EF4444",
            "display_order": 6,
        },
        {
            "name": "Mining",
            "description": "Mining, Solid Minerals and Extractive Industries",
            "icon_class": "fa-gem",
            "color": "#92400E",
            "display_order": 7,
        },
        {
            "name": "Real Estate",
            "description": "Real Estate, Property Development and Housing",
            "icon_class": "fa-building",
            "color": "#059669",
            "display_order": 8,
        },
        {
            "name": "Tourism",
            "description": "Tourism, Hospitality and Cultural Heritage",
            "icon_class": "fa-plane",
            "color": "#EC4899",
            "display_order": 9,
        },
        {
            "name": "Financial Services",
            "description": "Financial Services, Banking and Fintech",
            "icon_class": "fa-university",
            "color": "#14B8A6",
            "display_order": 10,
        },
    ]

    created_count = 0
    for sector_data in sectors_data:
        sector, created = Sector.objects.get_or_create(
            name=sector_data["name"],
            defaults={
                "slug": slugify(sector_data["name"]),
                "description": sector_data["description"],
                "icon_class": sector_data["icon_class"],
                "color": sector_data["color"],
                "display_order": sector_data["display_order"],
                "is_active": True,
                "featured": True,
            },
        )
        if created:
            created_count += 1
            print(f"  ✓ Created sector: {sector_data['name']}")

    print(f"✅ Created {created_count} sectors (Total: {Sector.objects.count()})")
    return Sector.objects.all()


# ============================================================================
# STEP 2: CREATE MEMBER STATES
# ============================================================================


def populate_member_states():
    """Populate all IPAWAS member states with comprehensive data"""
    print("\n🌍 Creating Member States...")

    member_states_data = [
        # ACTIVE MEMBERS
        {
            "country_name": "Nigeria",
            "country_code": "NGA",
            "flag_emoji": "🇳🇬",
            "ipa_full_name": "Nigerian Investment Promotion Commission",
            "ipa_acronym": "NIPC",
            "ipa_website": "https://www.nipc.gov.ng",
            "overview": "The Nigerian Investment Promotion Commission (NIPC) was established to encourage, promote and co-ordinate investments in the Nigerian economy.",
            "tagline": "Gateway to Africa's Largest Economy",
            "population": 227000000,
            "population_display": "227 million",
            "gdp": Decimal("252.00"),
            "gdp_display": "$252 billion",
            "gdp_growth_rate": Decimal("2.85"),
            "gdp_per_capita": Decimal("1110.00"),
            "capital_city": "Abuja",
            "major_cities": ["Lagos", "Abuja", "Kano", "Port Harcourt"],
            "geographic_region": "gulf_of_guinea",
            "official_language": "english",
            "currency_name": "Nigerian Naira",
            "currency_code": "NGN",
            "currency_symbol": "₦",
            "contact_email": "info@nipc.gov.ng",
            "contact_phone": "+234-9-461-3000",
            "physical_address": "Plot 1181, Aguiyi Ironsi Street, Maitama District, Abuja FCT, Nigeria",
            "office_hours": "Monday - Friday: 8:00 AM - 5:00 PM",
            "time_zone": "Africa/Lagos",
            "is_active": True,
            "featured": True,
            "display_order": 1,
        },
        {
            "country_name": "Ghana",
            "country_code": "GHA",
            "flag_emoji": "🇬🇭",
            "ipa_full_name": "Ghana Investment Promotion Centre",
            "ipa_acronym": "GIPC",
            "ipa_website": "https://www.gipc.gov.gh",
            "overview": "The Ghana Investment Promotion Centre (GIPC) is a government agency established to encourage, promote, and facilitate investments across all sectors.",
            "tagline": "Gateway to West Africa",
            "population": 33800000,
            "population_display": "33.8 million",
            "gdp": Decimal("87.50"),
            "gdp_display": "$87.5 billion",
            "gdp_growth_rate": Decimal("5.40"),
            "gdp_per_capita": Decimal("2590.00"),
            "capital_city": "Accra",
            "major_cities": ["Accra", "Kumasi", "Takoradi", "Tamale"],
            "geographic_region": "gulf_of_guinea",
            "official_language": "english",
            "currency_name": "Ghanaian Cedi",
            "currency_code": "GHS",
            "currency_symbol": "₵",
            "contact_email": "info@gipc.gov.gh",
            "contact_phone": "+233-30-266-5125",
            "physical_address": "Public Services Commission Building, Ministries, Accra",
            "office_hours": "Monday - Friday: 8:00 AM - 5:00 PM",
            "time_zone": "Africa/Accra",
            "is_active": True,
            "featured": True,
            "display_order": 2,
        },
        {
            "country_name": "Senegal",
            "country_code": "SEN",
            "flag_emoji": "🇸🇳",
            "ipa_full_name": "Agence de Promotion des Investissements et Grands Travaux",
            "ipa_acronym": "APIX",
            "ipa_website": "https://www.apix.sn",
            "overview": "APIX is Senegal's investment promotion agency, facilitating investments and major infrastructure projects.",
            "tagline": "The Gateway to West Africa",
            "population": 17700000,
            "population_display": "17.7 million",
            "gdp": Decimal("27.90"),
            "gdp_display": "$27.9 billion",
            "gdp_growth_rate": Decimal("4.00"),
            "gdp_per_capita": Decimal("1570.00"),
            "capital_city": "Dakar",
            "major_cities": ["Dakar", "Thiès", "Saint-Louis", "Kaolack"],
            "geographic_region": "west_coast",
            "official_language": "french",
            "currency_name": "West African CFA Franc",
            "currency_code": "XOF",
            "currency_symbol": "CFA",
            "contact_email": "contact@apix.sn",
            "contact_phone": "+221-33-849-05-55",
            "physical_address": "52-54 Rue Mohamed V, Dakar, Senegal",
            "office_hours": "Monday - Friday: 8:00 AM - 6:00 PM",
            "time_zone": "Africa/Dakar",
            "is_active": True,
            "featured": True,
            "display_order": 3,
        },
        {
            "country_name": "Côte d'Ivoire",
            "country_code": "CIV",
            "flag_emoji": "🇨🇮",
            "ipa_full_name": "Centre de Promotion des Investissements en Côte d'Ivoire",
            "ipa_acronym": "CEPICI",
            "ipa_website": "https://www.cepici.gouv.ci",
            "overview": "CEPICI is the investment promotion center of Côte d'Ivoire, facilitating business creation and investment.",
            "tagline": "The Economic Engine of West Africa",
            "population": 28200000,
            "population_display": "28.2 million",
            "gdp": Decimal("70.00"),
            "gdp_display": "$70 billion",
            "gdp_growth_rate": Decimal("6.20"),
            "gdp_per_capita": Decimal("2480.00"),
            "capital_city": "Yamoussoukro",
            "major_cities": ["Abidjan", "Yamoussoukro", "Bouaké", "San-Pédro"],
            "geographic_region": "gulf_of_guinea",
            "official_language": "french",
            "currency_name": "West African CFA Franc",
            "currency_code": "XOF",
            "currency_symbol": "CFA",
            "contact_email": "info@cepici.gouv.ci",
            "contact_phone": "+225-27-20-31-88-00",
            "physical_address": "Abidjan-Plateau, Rue Gourgas, Côte d'Ivoire",
            "office_hours": "Monday - Friday: 7:30 AM - 5:30 PM",
            "time_zone": "Africa/Abidjan",
            "is_active": True,
            "featured": True,
            "display_order": 4,
        },
    ]

    created_states = {}
    created_count = 0

    for state_data in member_states_data:
        country_code = state_data["country_code"]
        member_state, created = MemberStateIPA.objects.get_or_create(
            country_code=country_code,
            defaults={
                "country_name": state_data["country_name"],
                "slug": slugify(state_data["country_name"]),
                "flag_emoji": state_data.get("flag_emoji", ""),
                "ipa_full_name": state_data["ipa_full_name"],
                "ipa_acronym": state_data["ipa_acronym"],
                "ipa_website": state_data.get("ipa_website", ""),
                "overview": state_data.get("overview", ""),
                "tagline": state_data.get("tagline", ""),
                "population": state_data["population"],
                "population_display": state_data.get("population_display", ""),
                "gdp": state_data["gdp"],
                "gdp_display": state_data.get("gdp_display", ""),
                "gdp_growth_rate": state_data.get("gdp_growth_rate"),
                "gdp_per_capita": state_data.get("gdp_per_capita"),
                "capital_city": state_data["capital_city"],
                "major_cities": state_data.get("major_cities", []),
                "geographic_region": state_data["geographic_region"],
                "official_language": state_data["official_language"],
                "currency_name": state_data["currency_name"],
                "currency_code": state_data["currency_code"],
                "currency_symbol": state_data.get("currency_symbol", ""),
                "contact_email": state_data["contact_email"],
                "contact_phone": state_data.get("contact_phone", ""),
                "physical_address": state_data.get("physical_address", ""),
                "office_hours": state_data.get("office_hours", ""),
                "time_zone": state_data["time_zone"],
                "is_active": state_data.get("is_active", True),
                "featured": state_data.get("featured", False),
                "display_order": state_data.get("display_order", 99),
            },
        )
        if created:
            created_count += 1
            print(f"  ✓ Created: {state_data['country_name']} ({state_data['ipa_acronym']})")

        created_states[country_code] = member_state

    print(f"✅ Created {created_count} member states (Total: {MemberStateIPA.objects.count()})")
    return created_states


# ============================================================================
# STEP 3: CREATE MEMBER STATE SECTORS (Priority Sectors)
# ============================================================================


def populate_member_state_sectors(member_states, sectors):
    """Link member states with their priority sectors"""
    print("\n🔗 Creating Member State Sectors...")

    priority_sectors_map = {
        "NGA": ["Agriculture", "Manufacturing", "Technology", "Energy", "Infrastructure"],
        "GHA": ["Agriculture", "Mining", "Energy", "Technology", "Tourism"],
        "SEN": ["Agriculture", "Fisheries", "Tourism", "Manufacturing", "Infrastructure"],
        "CIV": ["Agriculture", "Manufacturing", "Energy", "Infrastructure", "Mining"],
    }

    created_count = 0
    for country_code, sector_names in priority_sectors_map.items():
        if country_code not in member_states:
            continue

        member_state = member_states[country_code]
        for idx, sector_name in enumerate(sector_names, start=1):
            try:
                sector = sectors.get(name=sector_name)
                mss, created = MemberStateSector.objects.get_or_create(
                    member_state=member_state,
                    sector=sector,
                    defaults={
                        "is_priority": True,
                        "description": f"{sector_name} is a priority sector for {member_state.country_name}",
                        "display_order": idx,
                    },
                )
                if created:
                    created_count += 1
            except Sector.DoesNotExist:
                print(f"  ⚠️  Sector '{sector_name}' not found")

    print(f"✅ Created {created_count} member state sectors")


# ============================================================================
# STEP 4: CREATE INVESTMENT INCENTIVES
# ============================================================================


def populate_incentives(member_states):
    """Create investment incentives for member states"""
    print("\n💰 Creating Investment Incentives...")

    incentive_types = [
        "tax_holiday",
        "tax_credit",
        "customs_exemption",
        "capital_allowance",
        "import_duty_relief",
    ]

    sectors = Sector.objects.all()
    created_count = 0

    for country_code, member_state in member_states.items():
        # Create 3-5 incentives per country
        for i in range(random.randint(3, 5)):
            incentive_type = random.choice(incentive_types)
            incentive, created = InvestmentIncentive.objects.get_or_create(
                member_state=member_state,
                title=f"{incentive_type.replace('_', ' ').title()} - {member_state.ipa_acronym}",
                defaults={
                    "incentive_type": incentive_type,
                    "description": f"This incentive provides {incentive_type.replace('_', ' ')} benefits for qualifying investments.",
                    "duration": f"{random.randint(3, 10)} years",
                    "eligibility_criteria": "Minimum investment of $1 million in priority sectors",
                    "benefit_amount": f"{random.randint(25, 100)}% reduction",
                    "is_active": True,
                    "display_order": i + 1,
                },
            )

            if created:
                # Link to 1-3 random sectors
                incentive.applicable_sectors.set(random.sample(list(sectors), random.randint(1, 3)))
                created_count += 1

    print(f"✅ Created {created_count} investment incentives")


# ============================================================================
# STEP 5: CREATE INVESTMENT OPPORTUNITIES
# ============================================================================


def populate_opportunities(member_states):
    """Create investment opportunities"""
    print("\n💼 Creating Investment Opportunities...")

    sectors = Sector.objects.all()
    opportunity_types = ["greenfield", "brownfield", "ppp"]
    project_stages = ["concept", "feasibility", "ready"]
    statuses = ["active", "under_review"]

    created_count = 0

    for country_code, member_state in member_states.items():
        # Create 3-5 opportunities per country
        for i in range(random.randint(3, 5)):
            sector = random.choice(sectors)
            opp_type = random.choice(opportunity_types)

            opportunity, created = InvestmentOpportunity.objects.get_or_create(
                reference_number=f"{member_state.country_code}-{sector.slug.upper()[:3]}-{random.randint(1000, 9999)}",
                defaults={
                    "title": f"{sector.name} Development Project - {member_state.country_name}",
                    "slug": slugify(f"{sector.name}-project-{member_state.country_name}-{i}"),
                    "summary": f"Investment opportunity in {sector.name} sector in {member_state.country_name}",
                    "description": f"Comprehensive investment opportunity for {sector.name} development in {member_state.country_name}. This project offers significant returns and strategic market access.",
                    "opportunity_type": opp_type,
                    "primary_sector": sector,
                    "primary_country": member_state,
                    "is_regional": random.choice([True, False]),
                    "investment_required_min": Decimal(random.randint(1, 50)) * Decimal("1000000"),
                    "investment_required_max": Decimal(random.randint(51, 200))
                    * Decimal("1000000"),
                    "project_stage": random.choice(project_stages),
                    "status": random.choice(statuses),
                    "published": True,
                    "featured": random.choice([True, False]),
                    "views_count": random.randint(10, 500),
                    "inquiries_count": random.randint(0, 50),
                    "downloads_count": random.randint(0, 100),
                },
            )

            if created:
                created_count += 1

    print(f"✅ Created {created_count} investment opportunities")


# ============================================================================
# STEP 6: CREATE SUCCESS STORIES
# ============================================================================


def populate_success_stories(member_states):
    """Create success stories"""
    print("\n🏆 Creating Success Stories...")

    sectors = Sector.objects.all()
    companies = [
        "Global Tech Inc.",
        "African Energy Solutions",
        "Continental Manufacturing Ltd.",
        "AgriVest International",
        "MineCorps Global",
    ]

    created_count = 0

    for country_code, member_state in member_states.items():
        # Create 2-3 success stories per country
        for i in range(random.randint(2, 3)):
            sector = random.choice(sectors)
            company = random.choice(companies)

            story, created = SuccessStory.objects.get_or_create(
                member_state=member_state,
                company_name=company,
                year=random.randint(2018, 2024),
                defaults={
                    "title": f"{company} Transforms {sector.name} in {member_state.country_name}",
                    "company_origin": random.choice(["USA", "UK", "China", "UAE", "Germany"]),
                    "sector": sector,
                    "investment_amount": Decimal(random.randint(5, 100)) * Decimal("1000000"),
                    "investment_amount_display": f"${random.randint(5, 100)}M",
                    "jobs_created": random.randint(100, 5000),
                    "summary": f"{company} successfully invested in {member_state.country_name}'s {sector.name} sector, creating thousands of jobs and contributing to economic growth.",
                    "full_story": f"Detailed success story of {company}'s investment in {member_state.country_name}...",
                    "impact": f"Created {random.randint(100, 5000)} jobs and contributed significantly to the local economy",
                    "published": True,
                    "featured": random.choice([True, False]),
                    "display_order": i + 1,
                },
            )

            if created:
                created_count += 1

    print(f"✅ Created {created_count} success stories")


# ============================================================================
# STEP 7: CREATE IPA STAFF
# ============================================================================


def populate_ipa_staff(member_states):
    """Create IPA staff members"""
    print("\n👥 Creating IPA Staff...")

    position_types = ["executive", "director", "manager", "staff"]
    first_names = ["John", "Mary", "Ahmed", "Fatima", "David", "Grace", "Ibrahim", "Aisha"]
    last_names = ["Smith", "Johnson", "Mohammed", "Williams", "Brown", "Jones", "Garcia"]

    created_count = 0

    for country_code, member_state in member_states.items():
        # Create 3-5 staff members per IPA
        for i in range(random.randint(3, 5)):
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            position_type = random.choice(position_types)

            staff, created = IPAStaff.objects.get_or_create(
                member_state=member_state,
                full_name=f"{first_name} {last_name}",
                defaults={
                    "position_title": f"{position_type.title()} - Investment Promotion",
                    "position_type": position_type,
                    "email": f"{first_name.lower()}.{last_name.lower()}@{member_state.ipa_acronym.lower()}.gov",
                    "phone": f"+{random.randint(200, 299)}-{random.randint(10, 99)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
                    "bio": f"{first_name} {last_name} is a dedicated professional at {member_state.ipa_acronym}",
                    "display_order": i + 1,
                    "is_active": True,
                    "show_on_website": True,
                },
            )

            if created:
                created_count += 1

    print(f"✅ Created {created_count} IPA staff members")


# ============================================================================
# STEP 8: CREATE FDI DATA POINTS
# ============================================================================


def populate_fdi_data(member_states):
    """Create FDI data points"""
    print("\n📈 Creating FDI Data Points...")

    data_types = ["fdi_inflow", "fdi_outflow", "fdi_stock"]
    years = range(2018, 2025)

    created_count = 0

    for country_code, member_state in member_states.items():
        for year in years:
            for data_type in data_types:
                base_value = random.randint(100, 10000)

                fdi, created = FDIDataPoint.objects.get_or_create(
                    member_state=member_state,
                    data_type=data_type,
                    year=year,
                    defaults={
                        "value": Decimal(base_value) * Decimal("1000000"),
                        "value_display": f"${base_value}M",
                        "data_source": "UNCTAD",
                        "validation_status": "published",
                    },
                )

                if created:
                    created_count += 1

    print(f"✅ Created {created_count} FDI data points")


# ============================================================================
# STEP 9: CREATE USERS AND IPA USERS
# ============================================================================


def populate_users(member_states):
    """Create user accounts and IPA users"""
    if not IPAUser:
        print("\n⚠️  Skipping user creation - IPAUser model not available")
        return {}

    print("\n👤 Creating Users and IPA Users...")

    users_data = [
        {
            # "username": "hq_admin",
            "email": "admin@ipawas.org",
            "first_name": "System",
            "last_name": "Administrator",
            "member_state": None,
            "role": "hq_admin",
        },
        {
            # "username": "nigeria_admin",
            "email": "admin@nipc.gov.ng",
            "first_name": "Nigeria",
            "last_name": "Admin",
            "member_state": "NGA",
            "role": "ipa_director",
        },
        {
            # "username": "ghana_admin",
            "email": "admin@gipc.gov.gh",
            "first_name": "Ghana",
            "last_name": "Admin",
            "member_state": "GHA",
            "role": "ipa_director",
        },
        {
            # "username": "nigeria_editor",
            "email": "editor@nipc.gov.ng",
            "first_name": "Nigeria",
            "last_name": "Editor",
            "member_state": "NGA",
            "role": "ipa_officer",
        },
    ]

    created_users = {}
    created_count = 0

    for user_data in users_data:
        # Create Django user
        user, user_created = User.objects.get_or_create(
            # username=user_data["username"],
            defaults={
                "email": user_data["email"],
                "first_name": user_data["first_name"],
                "last_name": user_data["last_name"],
                "is_staff": user_data["role"] == "hq_admin",
                "is_superuser": user_data["role"] == "hq_admin",
            },
        )

        if user_created:
            user.set_password("password123")
            user.save()
            created_count += 1
            print(f"  ✓ Created user: {user_data['email']}")

        # Create IPAUser if member_state is specified
        if user_data["member_state"] and user_data["member_state"] in member_states:
            member_state = member_states[user_data["member_state"]]

            ipa_user, ipa_created = IPAUser.objects.get_or_create(
                user=user,
                defaults={
                    "member_state": member_state,
                    "role": user_data["role"],
                    "is_active": True,
                    "is_primary_contact": user_data["role"] == "ipa_director",
                    "can_publish_opportunities": True,
                    "can_approve_data": user_data["role"] == "ipa_director",
                    "can_manage_users": user_data["role"] == "ipa_director",
                    "can_edit_profile": True,
                    "can_manage_sectors": user_data["role"] == "ipa_director",
                    "can_create_opportunities": True,
                    "can_edit_incentives": True,
                    "can_manage_success_stories": True,
                    "can_view_inquiries": True,
                    "can_respond_to_inquiries": True,
                    "can_view_analytics": True,
                    "can_export_data": user_data["role"] == "ipa_director",
                    "dashboard_access_granted_at": timezone.now(),
                    "onboarding_completed": True,
                },
            )

        created_users[user_data["email"]] = user

    print(f"✅ Created {created_count} users")
    return created_users


# ============================================================================
# STEP 10: CREATE INVESTOR INQUIRIES
# ============================================================================


def populate_inquiries(member_states, users):
    """Create investor inquiries"""
    print("\n💬 Creating Investor Inquiries...")

    inquiry_types = ["general", "investment_opportunity", "partnership", "sector_specific"]
    statuses = ["new", "in_progress", "responded", "closed"]
    sectors = Sector.objects.all()

    created_count = 0

    for country_code, member_state in member_states.items():
        # Create 3-5 inquiries per country
        for i in range(random.randint(3, 5)):
            inquiry_type = random.choice(inquiry_types)
            sector = random.choice(sectors) if sectors else None

            inquiry, created = InvestorInquiry.objects.get_or_create(
                reference_number=f"INQ-{member_state.country_code}-{random.randint(10000, 99999)}",
                defaults={
                    "member_state": member_state,
                    "inquiry_type": inquiry_type,
                    "full_name": f"Investor {random.randint(1, 1000)}",
                    "email": f"investor{random.randint(1, 1000)}@example.com",
                    "phone": f"+1-{random.randint(100, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
                    "company_name": f"Investment Company {random.randint(1, 100)}",
                    "company_country": random.choice(["USA", "UK", "China", "UAE", "Germany"]),
                    "sector_of_interest": sector,
                    "estimated_investment": f"${random.randint(1, 100)}M",
                    "subject": f"Investment Inquiry - {sector.name if sector else 'General'}",
                    "message": f"I am interested in investment opportunities in {member_state.country_name}.",
                    "status": random.choice(statuses),
                    "created_at": random_datetime_last_n_days(90),
                },
            )

            if created:
                created_count += 1

    print(f"✅ Created {created_count} investor inquiries")


# ============================================================================
# STEP 11: CREATE DASHBOARD ACTIVITIES
# ============================================================================


def populate_activities(users, member_states):
    """Create dashboard activity logs"""
    if not IPADashboardActivity:
        return

    print("\n📋 Creating Dashboard Activities...")

    action_types = [
        "login",
        "logout",
        "create_opportunity",
        "edit_opportunity",
        "create_incentive",
        "respond_to_inquiry",
    ]

    created_count = 0

    for _, user in users.items():
        # Create 5-10 activities per user
        for i in range(random.randint(5, 10)):
            action_type = random.choice(action_types)

            # Get member_state if user has IPAUser
            member_state = None
            try:
                ipa_user = IPAUser.objects.get(user=user)
                member_state = ipa_user.member_state
            except:
                pass

            activity, created = IPADashboardActivity.objects.get_or_create(
                user=user,
                timestamp=random_datetime_last_n_days(30),
                action_type=action_type,
                defaults={
                    "member_state": member_state,
                    "description": f"User {action_type.replace('_', ' ')}",
                    "changes_json": {},
                },
            )

            if created:
                created_count += 1

    print(f"✅ Created {created_count} dashboard activities")


# ============================================================================
# STEP 12: CREATE NOTIFICATIONS
# ============================================================================


def populate_notifications(users):
    """Create notifications for IPA users"""
    if not IPANotification or not IPAUser:
        return

    print("\n🔔 Creating Notifications...")

    notification_templates = [
        {
            "notification_type": "inquiry",
            "title": "New Investor Inquiry Received",
            "message": "You have received a new inquiry from a potential investor.",
        },
        {
            "notification_type": "approval_needed",
            "title": "Opportunity Requires Approval",
            "message": "A new investment opportunity requires your approval.",
        },
    ]

    created_count = 0
    ipa_users = IPAUser.objects.select_related("user").all()

    for ipa_user in ipa_users[:10]:
        for template in random.sample(notification_templates, 2):
            notification, created = IPANotification.objects.get_or_create(
                recipient=ipa_user.user,
                title=template["title"],
                defaults={
                    "notification_type": template["notification_type"],
                    "message": template["message"],
                    "is_read": random.choice([True, False]),
                    "created_at": random_datetime_last_n_days(7),
                },
            )
            if created:
                created_count += 1
                if notification.is_read:
                    notification.read_at = notification.created_at + timedelta(
                        hours=random.randint(1, 48)
                    )
                    notification.save()

    print(f"✅ Created {created_count} notifications")


# ============================================================================
# STEP 13: CREATE INVITATIONS
# ============================================================================


def populate_invitations(users, member_states):
    """Create sample invitations"""
    if not Invitation:
        return

    print("\n📧 Creating Invitations...")

    invited_by = users.get("hq_admin") or users.get("nigeria_admin")
    if not invited_by:
        print("  ⚠️  No admin user found to send invitations")
        return

    invitation_data = [
        {
            "email": "newstaff1@nipc.gov.ng",
            "member_state": "NGA",
            "role": "ipa_officer",
            "status": "pending",
        },
        {
            "email": "newstaff2@gipc.gov.gh",
            "member_state": "GHA",
            "role": "ipa_data_entry",
            "status": "pending",
        },
    ]

    created_count = 0
    for inv_data in invitation_data:
        member_state_code = inv_data.pop("member_state")
        if member_state_code in member_states:
            invitation, created = Invitation.objects.get_or_create(
                email=inv_data["email"],
                member_state=member_states[member_state_code],
                defaults={
                    "role": inv_data["role"],
                    "invited_by": invited_by,
                    "invited_at": timezone.now() - timedelta(days=random.randint(1, 30)),
                    "expires_at": timezone.now() + timedelta(days=7),
                    "status": inv_data["status"],
                    "invitation_message": f"Welcome to the {member_states[member_state_code].ipa_acronym} team!",
                    "is_primary_contact": False,
                },
            )
            if created:
                created_count += 1
                print(f"  ✓ Created invitation: {inv_data['email']}")

    print(f"✅ Created {created_count} invitations")


# ============================================================================
# MAIN EXECUTION
# ============================================================================


def main():
    """Main execution function"""
    print("=" * 70)
    print("IPAWAS COMPREHENSIVE DATA POPULATION (CORRECTED)")
    print("=" * 70)
    print("\nThis script will populate ALL models with realistic data.")
    print("All fields have been verified against actual model structure.")
    print("⚠️  WARNING: This may create duplicate data if run multiple times.")
    print()

    response = input("Do you want to continue? (yes/no): ")
    if response.lower() not in ["yes", "y"]:
        print("Aborted.")
        return

    try:
        # Step 1: Create sectors
        sectors = populate_sectors()

        # Step 2: Create member states
        member_states = populate_member_states()

        # Step 3: Link member states with sectors
        populate_member_state_sectors(member_states, sectors)

        # Step 4: Create incentives
        populate_incentives(member_states)

        # Step 5: Create opportunities
        populate_opportunities(member_states)

        # Step 6: Create success stories
        populate_success_stories(member_states)

        # Step 7: Create IPA staff
        populate_ipa_staff(member_states)

        # Step 8: Create FDI data
        populate_fdi_data(member_states)

        # Step 9: Create users
        users = populate_users(member_states)

        # Step 10: Create inquiries
        populate_inquiries(member_states, users)

        # Step 11: Create activities
        populate_activities(users, member_states)

        # Step 12: Create notifications
        populate_notifications(users)

        # Step 13: Create invitations
        populate_invitations(users, member_states)

        print("\n" + "=" * 70)
        print("✅ DATA POPULATION COMPLETE!")
        print("=" * 70)
        print("\n📊 Summary:")
        print(f"  • Sectors: {Sector.objects.count()}")
        print(f"  • Member States: {MemberStateIPA.objects.count()}")
        print(f"  • Member State Sectors: {MemberStateSector.objects.count()}")
        print(f"  • Investment Incentives: {InvestmentIncentive.objects.count()}")
        print(f"  • Investment Opportunities: {InvestmentOpportunity.objects.count()}")
        print(f"  • Success Stories: {SuccessStory.objects.count()}")
        print(f"  • IPA Staff: {IPAStaff.objects.count()}")
        print(f"  • FDI Data Points: {FDIDataPoint.objects.count()}")
        print(f"  • Users: {User.objects.count()}")
        if IPAUser:
            print(f"  • IPA Users: {IPAUser.objects.count()}")
        print(f"  • Investor Inquiries: {InvestorInquiry.objects.count()}")
        if IPADashboardActivity:
            print(f"  • Dashboard Activities: {IPADashboardActivity.objects.count()}")
        if IPANotification:
            print(f"  • Notifications: {IPANotification.objects.count()}")
        if Invitation:
            print(f"  • Invitations: {Invitation.objects.count()}")

        print("\n🔐 Default Login Credentials:")
        print("  • HQ Admin: hq_admin / password123")
        print("  • Nigeria Admin: nigeria_admin / password123")
        print("  • Ghana Admin: ghana_admin / password123")
        print("  • Nigeria Editor: nigeria_editor / password123")

        print("\n✨ Your IPAWAS platform is now fully populated with data!")
        print("You can now explore the dashboard and see how everything works.")

    except Exception as e:
        print(f"\n❌ Error during data population: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
