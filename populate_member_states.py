"""
CORRECTED Data Population Script for IPAWAS Member States
Uses actual field names from the MemberStateIPA model

Usage: python populate_member_states_corrected.py
"""

import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from decimal import Decimal

from django.utils.text import slugify

from members.models import InvestmentIncentive, MemberStateIPA, MemberStateSector, Sector


def populate_sectors():
    """Create common investment sectors."""
    sectors_data = [
        ("Agriculture", "fa-tractor", "Agriculture and Agribusiness"),
        ("Manufacturing", "fa-industry", "Manufacturing and Industrial Production"),
        ("Technology", "fa-laptop-code", "Technology and ICT"),
        ("Energy", "fa-bolt", "Energy and Renewable Energy"),
        ("Infrastructure", "fa-road", "Infrastructure Development"),
        ("Healthcare", "fa-hospital", "Healthcare and Medical Services"),
        ("Solid Minerals", "fa-gem", "Mining and Solid Minerals"),
        ("Real Estate", "fa-building", "Real Estate and Construction"),
        ("Tourism", "fa-plane", "Tourism and Hospitality"),
        ("Financial Services", "fa-university", "Financial and Banking Services"),
        ("Fisheries", "fa-fish", "Fisheries and Aquaculture"),
        ("Forestry", "fa-tree", "Forestry and Wood Products"),
        ("Logistics", "fa-truck", "Transport and Logistics"),
    ]

    for name, icon, description in sectors_data:
        Sector.objects.get_or_create(
            name=name,
            defaults={"slug": slugify(name), "description": description, "is_active": True},
        )
    print(f"✓ Created {len(sectors_data)} sectors")


def populate_member_states():
    """Populate member states with corrected field names."""

    # Nigeria
    nigeria, created = MemberStateIPA.objects.get_or_create(
        country_name="Nigeria",
        defaults={
            "country_code": "NGA",
            "ipa_full_name": "Nigerian Investment Promotion Commission",
            "ipa_acronym": "NIPC",
            "overview": """The Nigerian Investment Promotion Commission (NIPC) was established by Nigerian Investment Promotion Act Chapter N117 Laws of the Federation of Nigeria 2004 to encourage, promote and co-ordinate investments in the Nigerian economy. Consequently, the NIPC Act allowed foreign investors to own up to 100% of the equity of any enterprise in the country except those under the 'Negative List.' This defines the role of NIPC as the One-Stop Agency that serves as the only co-coordinating and approving Centre for the establishment of businesses with foreign involvement in the country. NIPC also has a One Stop Investment Center (OSIC) that houses 17 Government agencies to render investment facilitation services, such as provision of investment information and processing the grant of approvals and licenses. NIPC also initiates and support measures to enhance the investment climate and competitiveness of the Nigerian economy.""",
            "ipa_website": "https://www.nipc.gov.ng",
            "is_active": True,
            "capital_city": "Abuja",
            "major_cities": ["Lagos", "Abuja", "Kano", "Port Harcourt"],
            "official_language": "english",  # Choice: "english", not "en"
            "geographic_region": "gulf_of_guinea",  # Field name: geographic_region, not region
            "population": 227000000,
            "gdp": Decimal("252.00"),  # Field name: gdp, not gdp_usd_billions
            "currency_name": "Nigerian Naira",
            "currency_code": "NGN",
            "currency_symbol": "₦",
            "contact_email": "info@nipc.gov.ng",
            "contact_phone": "+234-9-461-3000",
            "physical_address": "Plot 1181, Aguiyi Ironsi Street, Maitama District, Abuja FCT, Nigeria",  # Field: physical_address
        },
    )

    if created:
        sectors = [
            "Agriculture",
            "Manufacturing",
            "Technology",
            "Energy",
            "Infrastructure",
            "Healthcare",
            "Solid Minerals",
            "Real Estate",
        ]
        for i, sector_name in enumerate(sectors):
            sector = Sector.objects.get(name=sector_name)
            MemberStateSector.objects.create(
                member_state=nigeria, sector=sector, is_priority=True, display_order=i
            )

        InvestmentIncentive.objects.create(
            member_state=nigeria,
            title="Economic Development Tax Incentive",
            incentive_type="tax_reduction",
            description="Annual 5% tax credit for qualifying investments",
            duration="5 to 10 years",
            display_order=1,
        )
        InvestmentIncentive.objects.create(
            member_state=nigeria,
            title="Free Trade Zone Benefits",
            incentive_type="free_zone",
            description="Tax exemptions and duty-free imports for FTZ-based operations",
            display_order=2,
        )
        print("✓ Created Nigeria")

    # Ghana
    ghana, created = MemberStateIPA.objects.get_or_create(
        country_name="Ghana",
        defaults={
            "country_code": "GHA",
            "ipa_full_name": "Ghana Investment Promotion Centre",
            "ipa_acronym": "GIPC",
            "overview": """The Ghana Investment Promotion Centre (GIPC) is a government agency established under the GIPC Act, 2013 (Act 865) to encourage, promote, and facilitate investments across all sectors of the Ghanaian economy. It serves as Ghana's primary institution for investment promotion, providing a one-stop shop for investors through information, guidance, registration, and aftercare services. GIPC actively champions a transparent and business-friendly environment, driving Ghana's position as one of the most attractive and stable investment destinations in West Africa.""",
            "ipa_website": "https://www.gipc.gov.gh",
            "is_active": True,
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
        },
    )

    if created:
        sectors = [
            "Agriculture",
            "Manufacturing",
            "Energy",
            "Infrastructure",
            "Tourism",
            "Technology",
            "Financial Services",
        ]
        for i, sector_name in enumerate(sectors):
            sector = Sector.objects.get(name=sector_name)
            MemberStateSector.objects.create(
                member_state=ghana, sector=sector, is_priority=True, display_order=i
            )

        InvestmentIncentive.objects.create(
            member_state=ghana,
            title="Tax Holidays for Priority Sectors",
            incentive_type="tax_holiday",
            description="Tax holidays ranging from 5 to 10 years depending on location and activity",
            duration="5-10 years",
            display_order=1,
        )
        print("✓ Created Ghana")

    # Benin
    benin, created = MemberStateIPA.objects.get_or_create(
        country_name="Benin",
        defaults={
            "country_code": "BEN",
            "ipa_full_name": "Agence de Promotion des Investissements et des Exportations",
            "ipa_acronym": "APIEX",
            "overview": """APIEX was established to promote and facilitate investment and exports in Benin. It serves as the country's one-stop investment platform, supporting investors through project setup, registration, and aftercare. APIEX focuses on improving the business climate, promoting strategic sectors, and supporting Benin's industrialization goals under the national development plan.""",
            "ipa_website": "https://www.apiex.bj",
            "is_active": True,
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
        },
    )

    if created:
        sectors = ["Agriculture", "Manufacturing", "Infrastructure", "Energy", "Tourism"]
        for i, sector_name in enumerate(sectors):
            sector = Sector.objects.get(name=sector_name)
            MemberStateSector.objects.create(
                member_state=benin, sector=sector, is_priority=True, display_order=i
            )
        print("✓ Created Benin")

    # FORMER MEMBERS (is_active=False)

    # Mali
    mali, created = MemberStateIPA.objects.get_or_create(
        country_name="Mali",
        defaults={
            "country_code": "MLI",
            "ipa_full_name": "Agence pour la Promotion des Investissements au Mali",
            "ipa_acronym": "API-Mali",
            "overview": "API-Mali was the investment promotion agency of Mali. Mali is no longer an active member of IPAWAS.",
            "ipa_website": "https://www.apimali.gov.ml",
            "is_active": False,
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
        },
    )
    if created:
        print("✓ Created Mali (Former Member)")

    # Niger
    niger, created = MemberStateIPA.objects.get_or_create(
        country_name="Niger",
        defaults={
            "country_code": "NER",
            "ipa_full_name": "Agence Nigérienne de Promotion des Investissements",
            "ipa_acronym": "ANPIP",
            "overview": "ANPIP was the investment promotion agency of Niger. Niger is no longer an active member of IPAWAS.",
            "ipa_website": "https://www.anpip-niger.ne",
            "is_active": False,
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
        },
    )
    if created:
        print("✓ Created Niger (Former Member)")

    # Burkina Faso
    burkina, created = MemberStateIPA.objects.get_or_create(
        country_name="Burkina Faso",
        defaults={
            "country_code": "BFA",
            "ipa_full_name": "Agence de Promotion des Investissements du Burkina Faso",
            "ipa_acronym": "API-BF",
            "overview": "API-BF was the investment promotion agency of Burkina Faso. Burkina Faso is no longer an active member of IPAWAS.",
            "ipa_website": "https://www.investburkina.com",
            "is_active": False,
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
        },
    )
    if created:
        print("✓ Created Burkina Faso (Former Member)")

    print(f"\n✓ Member states populated successfully")
    print(f"  - Active members: {MemberStateIPA.objects.filter(is_active=True).count()}")
    print(f"  - Former members: {MemberStateIPA.objects.filter(is_active=False).count()}")


def main():
    print("Starting member states data population...\n")
    populate_sectors()
    populate_member_states()
    print("\n✓ Data population complete!")


if __name__ == "__main__":
    main()
