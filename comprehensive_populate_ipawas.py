"""
Comprehensive IPAWAS Data Population Script

This script populates ALL models in the IPAWAS platform with realistic data:
- Member States (12 active, 3 former)
- Sectors and Member State Sectors
- Investment Opportunities
- Investment Incentives
- Success Stories
- IPA Staff
- FDI Data Points
- Investor Inquiries
- Dashboard Activities
- Notifications
- User Accounts and IPA Users
- Invitations

Usage: python comprehensive_populate_ipawas.py
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
        ("Agriculture", "fa-tractor", "Agriculture, Agribusiness and Food Processing"),
        ("Manufacturing", "fa-industry", "Manufacturing and Industrial Production"),
        ("Technology", "fa-laptop-code", "Technology, ICT and Digital Innovation"),
        ("Energy", "fa-bolt", "Energy, Power Generation and Renewable Energy"),
        ("Infrastructure", "fa-road", "Infrastructure Development and Construction"),
        ("Healthcare", "fa-hospital", "Healthcare, Medical Services and Pharmaceuticals"),
        ("Mining", "fa-gem", "Mining, Solid Minerals and Extractive Industries"),
        ("Real Estate", "fa-building", "Real Estate, Property Development and Housing"),
        ("Tourism", "fa-plane", "Tourism, Hospitality and Cultural Heritage"),
        ("Financial Services", "fa-university", "Financial Services, Banking and Fintech"),
        ("Fisheries", "fa-fish", "Fisheries, Aquaculture and Marine Resources"),
        ("Forestry", "fa-tree", "Forestry, Wood Products and Pulp Production"),
        ("Logistics", "fa-truck", "Transport, Logistics and Supply Chain"),
        ("Education", "fa-graduation-cap", "Education, Training and Skill Development"),
        (
            "Telecommunications",
            "fa-broadcast-tower",
            "Telecommunications and Network Infrastructure",
        ),
    ]

    created_count = 0
    for name, icon, description in sectors_data:
        sector, created = Sector.objects.get_or_create(
            name=name,
            defaults={
                "slug": slugify(name),
                "description": description,
                "icon_class": icon,
                "is_active": True,
            },
        )
        if created:
            created_count += 1
            print(f"  ✓ Created sector: {name}")

    print(f"✅ Created {created_count} sectors (Total: {Sector.objects.count()})")
    return Sector.objects.all()


# ============================================================================
# STEP 2: CREATE MEMBER STATES (12 Active + 3 Former)
# ============================================================================


def populate_member_states():
    """Populate all IPAWAS member states with comprehensive data"""
    print("\n🌍 Creating Member States...")

    member_states_data = [
        # ACTIVE MEMBERS
        {
            "country_name": "Nigeria",
            "country_code": "NGA",
            "ipa_full_name": "Nigerian Investment Promotion Commission",
            "ipa_acronym": "NIPC",
            "overview": """The Nigerian Investment Promotion Commission (NIPC) was established by Nigerian Investment Promotion Act Chapter N117 Laws of the Federation of Nigeria 2004 to encourage, promote and co-ordinate investments in the Nigerian economy. The NIPC Act allowed foreign investors to own up to 100% of the equity of any enterprise in the country except those under the 'Negative List.' NIPC serves as the One-Stop Agency for coordinating and approving the establishment of businesses with foreign involvement. NIPC's One Stop Investment Center (OSIC) houses 17 Government agencies to render investment facilitation services.""",
            "ipa_website": "https://www.nipc.gov.ng",
            "is_active": True,
            "featured": True,
            "capital_city": "Abuja",
            "major_cities": ["Lagos", "Abuja", "Kano", "Port Harcourt"],
            "official_language": "english",
            "geographic_region": "gulf_of_guinea",
            "population": 227000000,
            "gdp": Decimal("252.00"),
            "currency_name": "Nigerian Naira",
            "currency_code": "NGN",
            "currency_symbol": "₦",
            "contact_email": "info@nipc.gov.ng",
            "contact_phone": "+234-9-461-3000",
            "physical_address": "Plot 1181, Aguiyi Ironsi Street, Maitama District, Abuja FCT, Nigeria",
            "priority_sectors": [
                "Agriculture",
                "Manufacturing",
                "Technology",
                "Energy",
                "Infrastructure",
                "Healthcare",
                "Mining",
                "Real Estate",
            ],
        },
        {
            "country_name": "Ghana",
            "country_code": "GHA",
            "ipa_full_name": "Ghana Investment Promotion Centre",
            "ipa_acronym": "GIPC",
            "overview": """The Ghana Investment Promotion Centre (GIPC) is a government agency established under the GIPC Act, 2013 (Act 865) to encourage, promote, and facilitate investments across all sectors of the Ghanaian economy. It serves as Ghana's primary institution for investment promotion, providing a one-stop shop for investors through information, guidance, registration, and aftercare services. GIPC actively champions a transparent and business-friendly environment, driving Ghana's position as one of the most attractive and stable investment destinations in West Africa.""",
            "ipa_website": "https://www.gipc.gov.gh",
            "is_active": True,
            "featured": True,
            "capital_city": "Accra",
            "major_cities": ["Accra", "Kumasi", "Takoradi", "Tamale"],
            "official_language": "english",
            "geographic_region": "gulf_of_guinea",
            "population": 33800000,
            "gdp": Decimal("87.50"),
            "currency_name": "Ghanaian Cedi",
            "currency_code": "GHS",
            "currency_symbol": "₵",
            "contact_email": "info@gipc.gov.gh",
            "contact_phone": "+233-30-266-5125",
            "physical_address": "Free Trade Zone Enclave, Airport City, Accra, Ghana",
            "priority_sectors": [
                "Agriculture",
                "Manufacturing",
                "Energy",
                "Infrastructure",
                "Tourism",
                "Technology",
                "Financial Services",
            ],
        },
        {
            "country_name": "Benin",
            "country_code": "BEN",
            "ipa_full_name": "Agence de Promotion des Investissements et des Exportations",
            "ipa_acronym": "APIEX",
            "overview": """APIEX was established to promote and facilitate investment and exports in Benin. It serves as the country's one-stop investment platform, supporting investors through project setup, registration, and aftercare. APIEX focuses on improving the business climate, promoting strategic sectors, and supporting Benin's industrialization goals under the national development plan.""",
            "ipa_website": "https://www.apiex.bj",
            "is_active": True,
            "featured": False,
            "capital_city": "Porto-Novo",
            "major_cities": ["Cotonou", "Porto-Novo", "Parakou"],
            "official_language": "french",
            "geographic_region": "gulf_of_guinea",
            "population": 13400000,
            "gdp": Decimal("20.50"),
            "currency_name": "West African CFA Franc",
            "currency_code": "XOF",
            "currency_symbol": "CFA",
            "contact_email": "info@apiex.bj",
            "contact_phone": "+229-21-30-04-00",
            "physical_address": "Cotonou, Benin",
            "priority_sectors": [
                "Agriculture",
                "Manufacturing",
                "Infrastructure",
                "Energy",
                "Tourism",
            ],
        },
        {
            "country_name": "Cabo Verde",
            "country_code": "CPV",
            "ipa_full_name": "Cabo Verde TradeInvest",
            "ipa_acronym": "CVTI",
            "overview": """Cabo Verde TradeInvest facilitates and promotes investment across the archipelago, focusing on sustainable sectors such as tourism, renewable energy, and ICT. It offers investor assistance, project evaluation, and facilitation of incentives for domestic and foreign investors.""",
            "ipa_website": "https://www.cvtradeinvest.com",
            "is_active": True,
            "featured": False,
            "capital_city": "Praia",
            "major_cities": ["Praia", "Mindelo", "Santa Maria"],
            "official_language": "portuguese",
            "geographic_region": "west_coast",
            "population": 600000,
            "gdp": Decimal("3.20"),
            "gdp_growth_rate": Decimal("4.5"),
            "currency_name": "Cape Verdean Escudo",
            "currency_code": "CVE",
            "currency_symbol": "CVE",
            "time_zone": "Atlantic/Cape_Verde",
            "contact_email": "info@cvtradeinvest.com",
            "contact_phone": "+238-260-3600",
            "physical_address": "Praia, Cabo Verde",
            "priority_sectors": [
                "Tourism",
                "Energy",
                "Technology",
                "Fisheries",
                "Logistics",
            ],
        },
        {
            "country_name": "Côte d'Ivoire",
            "country_code": "CIV",
            "ipa_full_name": "Centre de Promotion des Investissements en Côte d'Ivoire",
            "ipa_acronym": "CEPICI",
            "overview": """CEPICI is the official investment promotion agency responsible for attracting and facilitating domestic and foreign investments in Côte d'Ivoire. It provides a one-stop shop for business registration, investment facilitation, and aftercare, contributing to the nation's status as a leading West African business hub.""",
            "ipa_website": "https://www.cepici.gouv.ci",
            "is_active": True,
            "featured": True,
            "capital_city": "Yamoussoukro",
            "major_cities": ["Abidjan", "Bouaké", "Yamoussoukro"],
            "official_language": "french",
            "geographic_region": "gulf_of_guinea",
            "population": 29200000,
            "gdp": Decimal("82.60"),
            "gdp_growth_rate": Decimal("6.2"),
            "currency_name": "West African CFA Franc",
            "currency_code": "XOF",
            "currency_symbol": "CFA",
            "time_zone": "Africa/Abidjan",
            "contact_email": "info@cepici.gouv.ci",
            "contact_phone": "+225-20-31-60-00",
            "physical_address": "Abidjan, Côte d'Ivoire",
            "priority_sectors": [
                "Agriculture",
                "Manufacturing",
                "Energy",
                "Infrastructure",
                "Technology",
            ],
        },
        {
            "country_name": "The Gambia",
            "country_code": "GMB",
            "ipa_full_name": "Gambia Investment and Export Promotion Agency",
            "ipa_acronym": "GIEPA",
            "overview": """GIEPA is mandated to promote and facilitate private investment and exports in The Gambia. It provides investor facilitation, aftercare services, and policy advocacy to enhance the country's competitiveness as a small but strategic West African economy.""",
            "ipa_website": "https://www.giepa.gm",
            "is_active": True,
            "featured": False,
            "capital_city": "Banjul",
            "major_cities": ["Banjul", "Serekunda", "Brikama"],
            "official_language": "english",
            "geographic_region": "west_coast",
            "population": 2800000,
            "gdp": Decimal("2.60"),
            "gdp_growth_rate": Decimal("5.3"),
            "currency_name": "Gambian Dalasi",
            "currency_code": "GMD",
            "currency_symbol": "D",
            "time_zone": "Africa/Banjul",
            "contact_email": "info@giepa.gm",
            "contact_phone": "+220-422-8230",
            "physical_address": "Banjul, The Gambia",
            "priority_sectors": [
                "Tourism",
                "Agriculture",
                "Energy",
                "Manufacturing",
                "Technology",
            ],
        },
        {
            "country_name": "Guinea",
            "country_code": "GIN",
            "ipa_full_name": "Guinea Development Board",
            "ipa_acronym": "GDB",
            "overview": """The Guinea Development Board was established to improve the business climate and support investment facilitation in Guinea. It assists investors in project setup, provides incentives, and promotes Guinea's vast natural resources and emerging sectors.""",
            "ipa_website": "https://www.invest.gov.gn",
            "is_active": True,
            "featured": False,
            "capital_city": "Conakry",
            "major_cities": ["Conakry", "Kankan", "Labé"],
            "official_language": "french",
            "geographic_region": "west_coast",
            "population": 14500000,
            "gdp": Decimal("21.70"),
            "gdp_growth_rate": Decimal("5.6"),
            "currency_name": "Guinean Franc",
            "currency_code": "GNF",
            "currency_symbol": "FG",
            "time_zone": "Africa/Conakry",
            "contact_email": "info@invest.gov.gn",
            "contact_phone": "+224-622-40-00-00",
            "physical_address": "Conakry, Guinea",
            "priority_sectors": [
                "Mining",
                "Energy",
                "Agriculture",
                "Infrastructure",
                "Manufacturing",
            ],
        },
        {
            "country_name": "Guinea-Bissau",
            "country_code": "GNB",
            "ipa_full_name": "Centro de Promoção do Investimento",
            "ipa_acronym": "CPI-GB",
            "overview": """CPI-GB promotes private investment and supports economic diversification in Guinea-Bissau. The agency assists investors through facilitation services and encourages sustainable projects that strengthen national industries.""",
            "ipa_website": "https://www.cpi-guineabissau.com",
            "is_active": True,
            "featured": False,
            "capital_city": "Bissau",
            "major_cities": ["Bissau", "Bafatá", "Gabu"],
            "official_language": "portuguese",
            "geographic_region": "west_coast",
            "population": 2100000,
            "gdp": Decimal("2.10"),
            "gdp_growth_rate": Decimal("4.5"),
            "currency_name": "West African CFA Franc",
            "currency_code": "XOF",
            "currency_symbol": "CFA",
            "time_zone": "Africa/Bissau",
            "contact_email": "info@cpi-guineabissau.com",
            "contact_phone": "+245-320-5700",
            "physical_address": "Bissau, Guinea-Bissau",
            "priority_sectors": [
                "Agriculture",
                "Fisheries",
                "Energy",
                "Infrastructure",
                "Tourism",
            ],
        },
        {
            "country_name": "Liberia",
            "country_code": "LBR",
            "ipa_full_name": "National Investment Commission",
            "ipa_acronym": "NIC",
            "overview": """The National Investment Commission (NIC) promotes and facilitates both domestic and foreign investments in Liberia. It is a key driver of private sector development and industrial diversification, ensuring investors benefit from the nation's reform-driven policies.""",
            "ipa_website": "https://www.nic.gov.lr",
            "is_active": True,
            "featured": False,
            "capital_city": "Monrovia",
            "major_cities": ["Monrovia", "Gbarnga", "Buchanan"],
            "official_language": "english",
            "geographic_region": "west_coast",
            "population": 5500000,
            "gdp": Decimal("5.10"),
            "gdp_growth_rate": Decimal("4.8"),
            "currency_name": "Liberian Dollar",
            "currency_code": "LRD",
            "currency_symbol": "L$",
            "time_zone": "Africa/Monrovia",
            "contact_email": "info@nic.gov.lr",
            "contact_phone": "+231-77-500-500",
            "physical_address": "Monrovia, Liberia",
            "priority_sectors": [
                "Agriculture",
                "Mining",
                "Forestry",
                "Energy",
                "Infrastructure",
            ],
        },
        {
            "country_name": "Senegal",
            "country_code": "SEN",
            "ipa_full_name": "Agence Nationale chargée de la Promotion de l'Investissement et des Grands Travaux",
            "ipa_acronym": "APIX",
            "overview": """APIX promotes private investment and manages major infrastructure projects in Senegal. It is instrumental in positioning Senegal as a top investment destination in Africa through reforms, facilitation, and large-scale public-private partnerships.""",
            "ipa_website": "https://www.investinsenegal.com",
            "is_active": True,
            "featured": False,
            "capital_city": "Dakar",
            "major_cities": ["Dakar", "Thiès", "Saint-Louis"],
            "official_language": "french",
            "geographic_region": "west_coast",
            "population": 18600000,
            "gdp": Decimal("36.90"),
            "gdp_growth_rate": Decimal("8.2"),
            "currency_name": "West African CFA Franc",
            "currency_code": "XOF",
            "currency_symbol": "CFA",
            "time_zone": "Africa/Dakar",
            "contact_email": "contact@apix.sn",
            "contact_phone": "+221-33-849-05-55",
            "physical_address": "Dakar, Senegal",
            "priority_sectors": [
                "Agriculture",
                "Energy",
                "Infrastructure",
                "Manufacturing",
                "Technology",
            ],
        },
        {
            "country_name": "Sierra Leone",
            "country_code": "SLE",
            "ipa_full_name": "National Investment Board",
            "ipa_acronym": "NIB-SL",
            "overview": """The National Investment Board promotes and facilitates investment and exports in Sierra Leone, focusing on private sector growth and economic diversification. It offers facilitation, aftercare, and advocacy for both domestic and international investors.""",
            "ipa_website": "https://www.nib.gov.sl",
            "is_active": True,
            "featured": False,
            "capital_city": "Freetown",
            "major_cities": ["Freetown", "Bo", "Kenema"],
            "official_language": "english",
            "geographic_region": "west_coast",
            "population": 8800000,
            "gdp": Decimal("6.70"),
            "gdp_growth_rate": Decimal("3.2"),
            "currency_name": "Leone",
            "currency_code": "SLE",
            "currency_symbol": "Le",
            "time_zone": "Africa/Freetown",
            "contact_email": "info@nib.gov.sl",
            "contact_phone": "+232-76-610-610",
            "physical_address": "Freetown, Sierra Leone",
            "priority_sectors": [
                "Agriculture",
                "Mining",
                "Tourism",
                "Energy",
                "Infrastructure",
            ],
        },
        {
            "country_name": "Togo",
            "country_code": "TGO",
            "ipa_full_name": "Centre de Formalités des Entreprises et de Promotion des Investissements",
            "ipa_acronym": "CFE-PI",
            "overview": """Togo's investment promotion agency facilitates domestic and foreign investment and manages free zone development. It promotes Togo as a logistics and manufacturing hub, leveraging its modern port and strategic location.""",
            "ipa_website": "https://www.investingtogo.tg",
            "is_active": True,
            "featured": False,
            "capital_city": "Lomé",
            "major_cities": ["Lomé", "Sokodé", "Kara"],
            "official_language": "french",
            "geographic_region": "gulf_of_guinea",
            "population": 9300000,
            "gdp": Decimal("9.80"),
            "gdp_growth_rate": Decimal("5.5"),
            "currency_name": "West African CFA Franc",
            "currency_code": "XOF",
            "currency_symbol": "CFA",
            "time_zone": "Africa/Lome",
            "contact_email": "info@investingtogo.tg",
            "contact_phone": "+228-22-21-70-70",
            "physical_address": "Lomé, Togo",
            "priority_sectors": [
                "Logistics",
                "Manufacturing",
                "Agriculture",
                "Energy",
                "Financial Services",
            ],
        },
        # FORMER MEMBERS (is_active=False)
        {
            "country_name": "Mali",
            "country_code": "MLI",
            "ipa_full_name": "Agence pour la Promotion des Investissements au Mali",
            "ipa_acronym": "API-Mali",
            "overview": "API-Mali was the investment promotion agency of Mali. Mali is no longer an active member of IPAWAS.",
            "ipa_website": "https://www.apimali.gov.ml",
            "is_active": False,
            "featured": False,
            "capital_city": "Bamako",
            "major_cities": ["Bamako", "Sikasso", "Mopti"],
            "official_language": "french",
            "geographic_region": "sahel",
            "population": 22000000,
            "gdp": Decimal("19.00"),
            "currency_name": "West African CFA Franc",
            "currency_code": "XOF",
            "currency_symbol": "CFA",
            "contact_email": "info@apimali.gov.ml",
            "contact_phone": "+223-20-29-76-49",
            "physical_address": "Bamako, Mali",
            "priority_sectors": [],
        },
        {
            "country_name": "Niger",
            "country_code": "NER",
            "ipa_full_name": "Agence Nigérienne de Promotion des Investissements",
            "ipa_acronym": "ANPIP",
            "overview": "ANPIP was the investment promotion agency of Niger. Niger is no longer an active member of IPAWAS.",
            "ipa_website": "https://www.anpip-niger.ne",
            "is_active": False,
            "featured": False,
            "capital_city": "Niamey",
            "major_cities": ["Niamey", "Zinder", "Maradi"],
            "official_language": "french",
            "geographic_region": "sahel",
            "population": 26000000,
            "gdp": Decimal("16.00"),
            "currency_name": "West African CFA Franc",
            "currency_code": "XOF",
            "currency_symbol": "CFA",
            "contact_email": "info@anpip-niger.ne",
            "contact_phone": "+227-20-72-35-64",
            "physical_address": "Niamey, Niger",
            "priority_sectors": [],
        },
        {
            "country_name": "Burkina Faso",
            "country_code": "BFA",
            "ipa_full_name": "Agence de Promotion des Investissements du Burkina Faso",
            "ipa_acronym": "API-BF",
            "overview": "API-BF was the investment promotion agency of Burkina Faso. Burkina Faso is no longer an active member of IPAWAS.",
            "ipa_website": "https://www.investburkina.com",
            "is_active": False,
            "featured": False,
            "capital_city": "Ouagadougou",
            "major_cities": ["Ouagadougou", "Bobo-Dioulasso", "Koudougou"],
            "official_language": "french",
            "geographic_region": "sahel",
            "population": 22000000,
            "gdp": Decimal("19.50"),
            "currency_name": "West African CFA Franc",
            "currency_code": "XOF",
            "currency_symbol": "CFA",
            "contact_email": "info@investburkina.com",
            "contact_phone": "+226-25-30-09-09",
            "physical_address": "Ouagadougou, Burkina Faso",
            "priority_sectors": [],
        },
    ]

    created_count = 0
    member_states = {}

    for data in member_states_data:
        priority_sectors = data.pop("priority_sectors", [])

        member_state, created = MemberStateIPA.objects.get_or_create(
            country_code=data["country_code"],
            defaults={
                "slug": slugify(data["country_name"]),
                "display_order": created_count + 1,
                **data,
            },
        )

        if created:
            created_count += 1
            print(f"  ✓ Created: {data['country_name']} ({data['ipa_acronym']})")

            # Add priority sectors
            if priority_sectors:
                for i, sector_name in enumerate(priority_sectors):
                    try:
                        sector = Sector.objects.get(name=sector_name)
                        MemberStateSector.objects.create(
                            member_state=member_state,
                            sector=sector,
                            is_priority=True,
                            display_order=i,
                            description=f"Priority sector for investment in {data['country_name']}",
                        )
                    except Sector.DoesNotExist:
                        print(f"    ⚠️  Sector '{sector_name}' not found")

        member_states[data["country_code"]] = member_state

    print(
        f"✅ Created {created_count} member states (Active: {MemberStateIPA.objects.filter(is_active=True).count()}, Former: {MemberStateIPA.objects.filter(is_active=False).count()})"
    )
    return member_states


# ============================================================================
# STEP 3: CREATE INVESTMENT INCENTIVES
# ============================================================================


def populate_incentives(member_states):
    """Create investment incentives for each member state"""
    print("\n💰 Creating Investment Incentives...")

    incentives_data = {
        "NGA": [
            {
                "title": "Economic Development Tax Incentive",
                "incentive_type": "tax_reduction",
                "description": "Annual 5% tax credit for qualifying investments in priority sectors",
                "duration": "5 to 10 years",
                "benefit_amount": "5% annual tax credit",
            },
            {
                "title": "Free Trade Zone Benefits",
                "incentive_type": "free_zone",
                "description": "Tax exemptions, duty-free imports, and repatriation guarantees for FTZ-based operations",
                "duration": "Ongoing while in FTZ",
                "benefit_amount": "100% tax exemption",
            },
            {
                "title": "Pioneer Status Incentive",
                "incentive_type": "tax_holiday",
                "description": "Tax holiday for industries producing goods not previously manufactured in Nigeria",
                "duration": "3-5 years (extendable)",
                "benefit_amount": "100% corporate tax exemption",
            },
        ],
        "GHA": [
            {
                "title": "Tax Holidays for Priority Sectors",
                "incentive_type": "tax_holiday",
                "description": "Tax holidays ranging from 5 to 10 years depending on location and activity",
                "duration": "5-10 years",
                "benefit_amount": "Variable based on location",
            },
            {
                "title": "Free Zone Privileges",
                "incentive_type": "free_zone",
                "description": "Tax exemptions and duty-free imports for free zone enterprises",
                "duration": "10 years (renewable)",
                "benefit_amount": "100% tax exemption",
            },
        ],
        "BEN": [
            {
                "title": "Investment Code Tax Exemptions",
                "incentive_type": "tax_exemption",
                "description": "Tax exemptions under the Investment Code for qualifying projects",
                "duration": "Up to 10 years",
                "benefit_amount": "Up to 100% exemption",
            },
            {
                "title": "Special Economic Zone Benefits",
                "incentive_type": "free_zone",
                "description": "Customs and VAT exemptions for SEZ-based enterprises",
                "duration": "15 years",
                "benefit_amount": "VAT and customs exemptions",
            },
        ],
    }

    created_count = 0
    for country_code, incentives in incentives_data.items():
        if country_code in member_states:
            member_state = member_states[country_code]
            for i, inc_data in enumerate(incentives):
                incentive, created = InvestmentIncentive.objects.get_or_create(
                    member_state=member_state,
                    title=inc_data["title"],
                    defaults={"display_order": i + 1, "is_active": True, **inc_data},
                )
                if created:
                    created_count += 1

    print(f"✅ Created {created_count} investment incentives")


# ============================================================================
# STEP 4: CREATE INVESTMENT OPPORTUNITIES
# ============================================================================


def populate_opportunities(member_states):
    """Create investment opportunities for member states"""
    print("\n💡 Creating Investment Opportunities...")

    # Sample opportunities for Nigeria
    nigeria_opportunities = [
        {
            "title": "Rice Milling and Processing Facility",
            "primary_sector": "Agriculture",
            "description": "Establishment of modern rice milling facility with 100,000 MT annual capacity",
            # "investment_size": Decimal("25000000"),
            "expected_roi": Decimal("18.5"),
            # "jobs_created": 450,
            # "project_duration": "24 months",
        },
        {
            "title": "Solar Power Generation Plant",
            "primary_sector": "Energy",
            "description": "Development of 50MW solar power plant to supply national grid",
            # "investment_size": Decimal("75000000"),
            "expected_roi": Decimal("14.2"),
            # "jobs_created": 200,
            # "project_duration": "18 months",
        },
        {
            "title": "Industrial Park Development",
            "primary_sector": "Infrastructure",
            "description": "Construction of 500-hectare industrial park with modern facilities",
            # "investment_size": Decimal("150000000"),
            "expected_roi": Decimal("16.8"),
            # "jobs_created": 2500,
            # "project_duration": "36 months",
        },
        {
            "title": "Fintech Payment Platform",
            "primary_sector": "Technology",
            "description": "Development of digital payment and financial inclusion platform",
            # "investment_size": Decimal("5000000"),
            "expected_roi": Decimal("35.0"),
            # "jobs_created": 150,
            # "project_duration": "12 months",
        },
    ]

    # Sample opportunities for Ghana
    ghana_opportunities = [
        {
            "title": "Cocoa Processing Factory",
            "primary_sector": "Agriculture",
            "description": "Modern cocoa processing facility for export-quality chocolate products",
            # "investment_size": Decimal("35000000"),
            "expected_roi": Decimal("22.5"),
            # "jobs_created": 600,
            # "project_duration": "20 months",
        },
        {
            "title": "Tourism Eco-Resort Development",
            "primary_sector": "Tourism",
            "description": "Luxury eco-resort with 200 rooms leveraging Ghana's natural beauty",
            # "investment_size": Decimal("45000000"),
            "expected_roi": Decimal("19.5"),
            # "jobs_created": 350,
            # "project_duration": "24 months",
        },
    ]

    created_count = 0

    # Create Nigeria opportunities
    if "NGA" in member_states:
        for opp_data in nigeria_opportunities:
            sector_name = opp_data.pop("primary_sector")
            try:
                sector = Sector.objects.get(name=sector_name)
                opp, created = InvestmentOpportunity.objects.get_or_create(
                    participating_countries=member_states["NGA"],
                    title=opp_data["title"],
                    defaults={
                        "primary_sector": sector,
                        "status": random.choice(["published", "published", "draft"]),
                        # "application_deadline": timezone.now().date()
                        # + timedelta(days=random.randint(90, 365)),
                        **opp_data,
                    },
                )
                if created:
                    created_count += 1
            except Sector.DoesNotExist:
                pass

    # Create Ghana opportunities
    if "GHA" in member_states:
        for opp_data in ghana_opportunities:
            sector_name = opp_data.pop("primary_sector")
            try:
                sector = Sector.objects.get(name=sector_name)
                opp, created = InvestmentOpportunity.objects.get_or_create(
                    member_state=member_states["GHA"],
                    title=opp_data["title"],
                    defaults={
                        "primary_sector": sector,
                        "status": "published",
                        # "application_deadline": timezone.now().date()
                        # + timedelta(days=random.randint(90, 365)),
                        **opp_data,
                    },
                )
                if created:
                    created_count += 1
            except Sector.DoesNotExist:
                pass

    print(f"✅ Created {created_count} investment opportunities")


# ============================================================================
# STEP 5: CREATE SUCCESS STORIES
# ============================================================================


def populate_success_stories(member_states):
    """Create success stories for member states"""
    print("\n🏆 Creating Success Stories...")

    stories_data = [
        {
            "country_code": "NGA",
            "sector": "Technology",
            "title": "Global Fintech Company Establishes Regional Hub in Lagos",
            "company_name": "PayTech Solutions Ltd",
            "company_country": "United States",
            "investment_amount": Decimal("15000000"),
            # "jobs_created": 250,
            "story": "PayTech Solutions established its West African headquarters in Lagos in 2022, creating 250 high-skilled jobs and processing over $2 billion in digital transactions annually.",
        },
        {
            "country_code": "GHA",
            "sector": "Agriculture",
            "title": "Dutch Agribusiness Invests in Cocoa Processing",
            "company_name": "AgriGlobal BV",
            "company_country": "Netherlands",
            "investment_amount": Decimal("45000000"),
            # "jobs_created": 800,
            "story": "AgriGlobal established a state-of-the-art cocoa processing facility in Kumasi, creating 800 jobs and increasing Ghana's cocoa export value by 15%.",
        },
    ]

    created_count = 0
    for story_data in stories_data:
        country_code = story_data.pop("country_code")
        sector_name = story_data.pop("sector")

        if country_code in member_states:
            try:
                sector = Sector.objects.get(name=sector_name)
                story, created = SuccessStory.objects.get_or_create(
                    member_state=member_states[country_code],
                    title=story_data["title"],
                    defaults={
                        "sector": sector,
                        "published": True,
                        "featured": random.choice([True, False]),
                        "year_established": random.randint(2020, 2024),
                        **story_data,
                    },
                )
                if created:
                    created_count += 1
            except Sector.DoesNotExist:
                pass

    print(f"✅ Created {created_count} success stories")


# ============================================================================
# STEP 6: CREATE IPA STAFF
# ============================================================================


def populate_ipa_staff(member_states):
    """Create IPA staff members for each member state"""
    print("\n👥 Creating IPA Staff Members...")

    # Staff positions
    positions = [
        ("Executive Director", True),
        ("Director of Investment Promotion", True),
        ("Director of Operations", True),
        ("Head of Investor Relations", True),
        ("Senior Investment Officer", False),
        ("Communications Manager", False),
    ]

    created_count = 0
    for country_code, member_state in list(member_states.items())[:4]:  # First 4 countries
        if member_state.is_active:
            for i, (position, show_on_website) in enumerate(positions[:4]):
                staff, created = IPAStaff.objects.get_or_create(
                    member_state=member_state,
                    position=position,
                    defaults={
                        "full_name": f"{random.choice(['John', 'Mary', 'Ahmed', 'Fatima', 'David', 'Grace'])} {random.choice(['Okafor', 'Mensah', 'Diallo', 'Santos', 'Williams'])}",
                        "email": f"{position.lower().replace(' ', '.')}@{member_state.ipa_acronym.lower()}.org",
                        "phone": f"+{random.randint(220, 250)}-{random.randint(20, 99)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
                        "bio": f"Experienced investment professional with over {random.randint(10, 25)} years in economic development and investment promotion.",
                        "is_active": True,
                        "show_on_website": show_on_website,
                        "display_order": i + 1,
                    },
                )
                if created:
                    created_count += 1

    print(f"✅ Created {created_count} IPA staff members")


# ============================================================================
# STEP 7: CREATE FDI DATA POINTS
# ============================================================================


def populate_fdi_data(member_states):
    """Create FDI inflow data for member states"""
    print("\n📈 Creating FDI Data Points...")

    created_count = 0
    for country_code, member_state in member_states.items():
        if member_state.is_active:
            # Create data for last 5 years
            for year in range(2020, 2025):
                # FDI Inflow
                fdi_inflow, created = FDIDataPoint.objects.get_or_create(
                    member_state=member_state,
                    year=year,
                    data_type="fdi_inflow",
                    defaults={
                        "value": Decimal(str(random.uniform(500, 5000))),
                        "unit": "million_usd",
                        "source": "UNCTAD World Investment Report",
                        "validation_status": "published",
                        "notes": f"Foreign Direct Investment inflow for {year}",
                    },
                )
                if created:
                    created_count += 1

                # FDI Stock
                fdi_stock, created = FDIDataPoint.objects.get_or_create(
                    member_state=member_state,
                    year=year,
                    data_type="fdi_stock",
                    defaults={
                        "value": Decimal(str(random.uniform(10000, 50000))),
                        "unit": "million_usd",
                        "source": "UNCTAD",
                        "validation_status": "published",
                    },
                )
                if created:
                    created_count += 1

    print(f"✅ Created {created_count} FDI data points")


# ============================================================================
# STEP 8: CREATE USER ACCOUNTS
# ============================================================================


def populate_users(member_states):
    """Create user accounts for different roles"""
    print("\n👤 Creating User Accounts...")

    users_data = [
        {
            "username": "hq_admin",
            "email": "admin@ipawas.org",
            "first_name": "System",
            "last_name": "Administrator",
            "user_type": "ipawas_admin",
            "is_staff": True,
            "is_superuser": True,
        },
        {
            "username": "nigeria_admin",
            "email": "admin@nipc.gov.ng",
            "first_name": "Chukwudi",
            "last_name": "Okonkwo",
            "user_type": "ipa_staff",
            "member_state": "NGA",
            "ipa_role": "ipa_director",
        },
        {
            "username": "ghana_admin",
            "email": "admin@gipc.gov.gh",
            "first_name": "Kwame",
            "last_name": "Mensah",
            "user_type": "ipa_staff",
            "member_state": "GHA",
            "ipa_role": "ipa_director",
        },
        {
            "username": "nigeria_editor",
            "email": "editor@nipc.gov.ng",
            "first_name": "Amina",
            "last_name": "Bello",
            "user_type": "ipa_staff",
            "member_state": "NGA",
            "ipa_role": "ipa_officer",
        },
    ]

    created_users = {}
    created_count = 0

    for user_data in users_data:
        member_state_code = user_data.pop("member_state", None)
        ipa_role = user_data.pop("ipa_role", None)
        user_type = user_data.pop("user_type")

        user, created = User.objects.get_or_create(
            username=user_data["username"],
            defaults={
                "email": user_data["email"],
                "first_name": user_data["first_name"],
                "last_name": user_data["last_name"],
                "is_staff": user_data.get("is_staff", False),
                "is_superuser": user_data.get("is_superuser", False),
                "is_active": True,
            },
        )

        if created:
            user.set_password("password123")  # Default password
            user.save()
            created_count += 1
            print(f"  ✓ Created user: {user.username} ({user.email})")

            # Create IPAUser profile if applicable
            if IPAUser and user_type == "ipa_staff" and member_state_code:
                member_state = member_states.get(member_state_code)
                if member_state:
                    ipa_user, ipa_created = IPAUser.objects.get_or_create(
                        user=user,
                        defaults={
                            "member_state": member_state,
                            "role": ipa_role or "ipa_director",
                            "is_primary_contact": ipa_role == "ipa_director",
                            "phone_number": f"+234-{random.randint(700, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
                        },
                    )
                    if ipa_created:
                        print(f"    ✓ Created IPAUser profile for {user.username}")

        created_users[user_data["username"]] = user

    print(f"✅ Created {created_count} user accounts")
    return created_users


# ============================================================================
# STEP 9: CREATE INVESTOR INQUIRIES
# ============================================================================


def populate_inquiries(member_states, users):
    """Create sample investor inquiries"""
    print("\n✉️  Creating Investor Inquiries...")

    inquiry_templates = [
        {
            "subject": "Investment Opportunity in Agricultural Processing",
            "message": "I represent a European consortium interested in establishing a food processing facility. We're looking for information on incentives, land availability, and regulatory requirements.",
            "sector": "Agriculture",
        },
        {
            "subject": "Renewable Energy Project Inquiry",
            "message": "Our company specializes in solar energy solutions. We're exploring opportunities to develop a 100MW solar farm. Could you provide information on PPP frameworks and grid connection requirements?",
            "sector": "Energy",
        },
        {
            "subject": "Manufacturing Investment Query",
            "message": "We're a textile manufacturer looking to expand into West Africa. Please share information about industrial zones, labor availability, and export incentives.",
            "sector": "Manufacturing",
        },
    ]

    created_count = 0
    for country_code in ["NGA", "GHA", "BEN", "CIV"]:
        if country_code in member_states:
            member_state = member_states[country_code]

            for template in inquiry_templates[:2]:  # 2 inquiries per country
                sector_name = template["sector"]
                try:
                    sector = Sector.objects.get(name=sector_name)
                    inquiry, created = InvestorInquiry.objects.get_or_create(
                        member_state=member_state,
                        email=f"investor{random.randint(1, 999)}@example.com",
                        subject=template["subject"],
                        defaults={
                            "full_name": f"{random.choice(['James', 'Maria', 'Chen', 'Aisha'])} {random.choice(['Smith', 'Garcia', 'Wang', 'Johnson'])}",
                            "company_name": f"{random.choice(['Global', 'International', 'Pan-African'])} {sector_name} Corp",
                            "country": random.choice(
                                ["United States", "United Kingdom", "China", "Germany", "France"]
                            ),
                            "phone": f"+1-{random.randint(200, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
                            "sector": sector,
                            # "investment_size_range": random.choice(
                            #     ["10m_50m", "50m_100m", "100m_plus"]
                            # ),
                            "message": template["message"],
                            "status": random.choice(["new", "in_progress", "responded"]),
                            "priority": random.choice(["medium", "high"]),
                        },
                    )
                    if created:
                        created_count += 1
                except Sector.DoesNotExist:
                    pass

    print(f"✅ Created {created_count} investor inquiries")


# ============================================================================
# STEP 10: CREATE DASHBOARD ACTIVITIES
# ============================================================================


def populate_activities(users, member_states):
    """Create dashboard activity logs"""
    if not IPADashboardActivity:
        return

    print("\n📝 Creating Dashboard Activities...")

    action_types = [
        "login",
        "profile_update",
        "opportunity_create",
        "opportunity_update",
        "inquiry_view",
        "inquiry_respond",
    ]

    created_count = 0
    # Create activities for the last 30 days
    for _ in range(50):  # 50 activities
        user = random.choice(list(users.values()))
        action_type = random.choice(action_types)

        member_state = None
        if hasattr(user, "ipa_user") and user.ipa_user:
            member_state = user.ipa_user.member_state
        elif "NGA" in member_states:
            member_state = member_states["NGA"]

        description = f"User {user.get_full_name()} performed {action_type}"

        activity = IPADashboardActivity.objects.create(
            user=user,
            member_state=member_state,
            action_type=action_type,
            description=description,
            timestamp=random_datetime_last_n_days(30),
        )
        created_count += 1

    print(f"✅ Created {created_count} dashboard activities")


# ============================================================================
# STEP 11: CREATE NOTIFICATIONS
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
            "message": "You have received a new inquiry from a potential investor in the Manufacturing sector.",
        },
        {
            "notification_type": "opportunity_expiring",
            "title": "Investment Opportunity Expiring Soon",
            "message": "The investment opportunity 'Solar Power Plant' will expire in 7 days.",
        },
        {
            "notification_type": "system_alert",
            "title": "System Maintenance Scheduled",
            "message": "The platform will undergo maintenance on Sunday from 2:00 AM to 4:00 AM GMT.",
        },
    ]

    created_count = 0
    ipa_users = IPAUser.objects.select_related("user").all()

    for ipa_user in ipa_users[:10]:  # First 10 IPA users
        for template in random.sample(notification_templates, 2):  # 2 random notifications each
            notification, created = IPANotification.objects.get_or_create(
                recipient=ipa_user,
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
# STEP 12: CREATE INVITATIONS
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
        {
            "email": "accepted@nipc.gov.ng",
            "member_state": "NGA",
            "role": "ipa_officer",
            "status": "accepted",
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
    print("IPAWAS COMPREHENSIVE DATA POPULATION")
    print("=" * 70)
    print("\nThis script will populate ALL models with realistic data.")
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

        # Step 3: Create incentives
        populate_incentives(member_states)

        # Step 4: Create opportunities
        populate_opportunities(member_states)

        # Step 5: Create success stories
        populate_success_stories(member_states)

        # Step 6: Create IPA staff
        populate_ipa_staff(member_states)

        # Step 7: Create FDI data
        populate_fdi_data(member_states)

        # Step 8: Create users
        users = populate_users(member_states)

        # Step 9: Create inquiries
        populate_inquiries(member_states, users)

        # Step 10: Create activities
        populate_activities(users, member_states)

        # Step 11: Create notifications
        populate_notifications(users)

        # Step 12: Create invitations
        populate_invitations(users, member_states)

        print("\n" + "=" * 70)
        print("✅ DATA POPULATION COMPLETE!")
        print("=" * 70)
        print("\n📊 Summary:")
        print(f"  • Sectors: {Sector.objects.count()}")
        print(f"  • Member States: {MemberStateIPA.objects.count()}")
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
