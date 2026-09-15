"""
IPAWAS Data Population - Members App (Part 3 of 3)
Creates Member State Sectors, Investment Incentives, Success Stories,
Investor Inquiries, FDI Data Points, and IPA Staff
"""

import os
from datetime import datetime, timedelta
from decimal import Decimal

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth import get_user_model

from core.models import Sector
from members.models import (
    FDIDataPoint,
    InvestmentIncentive,
    InvestorInquiry,
    IPAStaff,
    MemberStateIPA,
    MemberStateSector,
    SuccessStory,
)

User = get_user_model()


def create_member_state_sectors():
    """Link sectors to member states with priority"""
    print("\n" + "=" * 60)
    print("CREATING MEMBER STATE SECTORS")
    print("=" * 60)

    # Nigeria sectors
    try:
        nigeria = MemberStateIPA.objects.get(slug="nigeria")
        agriculture = Sector.objects.get(slug="agriculture-agribusiness")
        manufacturing = Sector.objects.get(slug="manufacturing")
        energy = Sector.objects.get(slug="energy-power")
        tech = Sector.objects.get(slug="technology-ict")
        infrastructure = Sector.objects.get(slug="infrastructure")

        nigeria_sectors = [
            (agriculture, True, 10),
            (energy, True, 20),
            (manufacturing, True, 30),
            (tech, True, 40),
            (infrastructure, False, 50),
        ]

        for sector, is_priority, order in nigeria_sectors:
            mss, created = MemberStateSector.objects.get_or_create(
                member_state=nigeria,
                sector=sector,
                defaults={"is_priority": is_priority, "display_order": order},
            )
            status = "✓ Created" if created else "- Exists"
            print(f"{status}: {nigeria.country_name} - {sector.name}")

    except Exception as e:
        print(f"⚠ Error creating Nigeria sectors: {e}")

    # Ghana sectors
    try:
        ghana = MemberStateIPA.objects.get(slug="ghana")
        mining = Sector.objects.get(slug="mining-natural-resources")

        ghana_sectors = [
            (agriculture, True, 10),
            (mining, True, 20),
            (energy, True, 30),
            (manufacturing, False, 40),
            (tech, False, 50),
        ]

        for sector, is_priority, order in ghana_sectors:
            mss, created = MemberStateSector.objects.get_or_create(
                member_state=ghana,
                sector=sector,
                defaults={"is_priority_sector": is_priority, "display_order": order},
            )
            status = "✓ Created" if created else "- Exists"
            print(f"{status}: {ghana.country_name} - {sector.name}")

    except Exception as e:
        print(f"⚠ Error creating Ghana sectors: {e}")


def create_investment_incentives():
    """Create investment incentives for member states"""
    print("\n" + "=" * 60)
    print("CREATING INVESTMENT INCENTIVES")
    print("=" * 60)

    try:
        nigeria = MemberStateIPA.objects.get(slug="nigeria")

        nigeria_incentives = [
            {
                "title": "Pioneer Status Incentive",
                "incentive_type": "tax",
                "description": "Tax holiday for companies in pioneer industries or producing pioneer products",
                # 'benefits': 'Income tax exemption for initial period of 3 years, extendable up to 5 years',
                "eligibility_criteria": "Industries or products listed in Pioneer Status Incentive Order",
                "duration": "5 years",
                "is_active": True,
            },
            {
                "title": "Export Expansion Grant",
                "incentive_type": "grant",
                "description": "Grant to companies that export non-oil products",
                # 'benefits': 'Cash grant based on percentage of export value',
                "eligibility_criteria": "Exporters of non-oil products",
                "duration": "15 years",
                "is_active": True,
            },
            {
                "title": "Free Trade Zone Benefits",
                "incentive_type": "zone",
                "description": "Complete package of incentives for FTZ enterprises",
                # 'benefits': '100% foreign ownership, duty-free imports, tax exemptions for 10 years renewable',
                "eligibility_criteria": "Companies operating within designated Free Trade Zones",
                "duration": "10 years",
                "is_active": True,
            },
        ]

        for inc_data in nigeria_incentives:
            inc, created = InvestmentIncentive.objects.get_or_create(
                member_state=nigeria, title=inc_data["title"], defaults=inc_data
            )
            status = "✓ Created" if created else "- Exists"
            print(f"{status}: {nigeria.country_name} - {inc.title}")

    except Exception as e:
        print(f"⚠ Error creating incentives: {e}")


def create_success_stories():
    """Create investment success stories"""
    print("\n" + "=" * 60)
    print("CREATING SUCCESS STORIES")
    print("=" * 60)

    try:
        nigeria = MemberStateIPA.objects.get(slug="nigeria")
        ghana = MemberStateIPA.objects.get(slug="ghana")

        stories_data = [
            {
                "member_state": nigeria,
                "title": "Dangote Refinery: Africa's Largest Oil Refinery",
                "company_name": "Dangote Group",
                "company_origin": "Nigeria",
                "sector": Sector.objects.get(slug="energy-power"),
                "investment_amount": Decimal("19000000000"),
                "jobs_created": 30000,
                "full_story": "The Dangote Refinery is a 650,000 barrels per day integrated refinery and petrochemical complex. It is the world's largest single-train refinery and represents one of Africa's largest industrial projects. The facility includes a fertilizer plant and will significantly reduce Nigeria's dependence on imported refined petroleum products.",
                "year": 2023,
                "featured": True,
                "published": True,
            },
            {
                "member_state": ghana,
                "title": "Nestlé Ghana Manufacturing Expansion",
                "company_name": "Nestlé S.A.",
                "company_origin": "Switzerland",
                "sector": Sector.objects.get(slug="manufacturing"),
                "investment_amount": Decimal("50000000"),
                "jobs_created": 1200,
                "full_story": "Nestlé expanded its manufacturing operations in Ghana with a new production line for Maggi cubes and beverages. The investment enhanced local production capacity, created jobs, and supported Ghana's industrialization agenda. The facility serves both domestic and regional export markets.",
                "year": 2019,
                "featured": True,
                "published": True,
            },
        ]

        for story_data in stories_data:
            story, created = SuccessStory.objects.get_or_create(
                member_state=story_data["member_state"],
                title=story_data["title"],
                defaults=story_data,
            )
            status = "✓ Created" if created else "- Exists"
            print(f"{status}: {story.title}")

    except Exception as e:
        print(f"⚠ Error creating success stories: {e}")


def create_investor_inquiries():
    """Create sample investor inquiries"""
    print("\n" + "=" * 60)
    print("CREATING INVESTOR INQUIRIES")
    print("=" * 60)

    try:
        nigeria = MemberStateIPA.objects.get(slug="nigeria")
        ghana = MemberStateIPA.objects.get(slug="ghana")

        inquiries_data = [
            {
                "member_state": nigeria,
                "inquiry_type": "general",
                "full_name": "Michael Zhang",
                "email": "mzhang@globaltech.com",
                "phone": "+86 138 0013 8000",
                "company_name": "Global Tech Ventures",
                "company_country": "China",
                "sector_of_interest": Sector.objects.get(slug="technology-ict"),
                "estimated_investment": "$5M - $10M",
                "subject": "Technology Park Investment Opportunity",
                "message": "Interested in establishing a technology park and innovation hub in Lagos. Looking for information on available land, incentives, and partnership opportunities with local tech companies.",
                "status": "new",
            },
            {
                "member_state": ghana,
                "inquiry_type": "site_visit",
                "full_name": "Sarah Williams",
                "email": "swilliams@euroagri.com",
                "phone": "+44 20 7946 0958",
                "company_name": "EuroAgri Investment Fund",
                "company_country": "United Kingdom",
                "sector_of_interest": Sector.objects.get(slug="agriculture-agribusiness"),
                "estimated_investment": "$10M - $25M",
                "subject": "Agribusiness Site Visit Request",
                "message": "Planning to visit Ghana in Q2 2025 to explore cocoa processing and export opportunities. Would appreciate assistance with site visits and meetings with potential local partners.",
                "status": "contacted",
            },
        ]

        for inq_data in inquiries_data:
            inq, created = InvestorInquiry.objects.get_or_create(
                member_state=inq_data["member_state"], email=inq_data["email"], defaults=inq_data
            )
            status = "✓ Created" if created else "- Exists"
            print(f"{status}: {inq.full_name} - {inq.member_state.country_name}")

    except Exception as e:
        print(f"⚠ Error creating inquiries: {e}")


def create_fdi_data_points():
    """Create FDI statistics"""
    print("\n" + "=" * 60)
    print("CREATING FDI DATA POINTS")
    print("=" * 60)

    try:
        nigeria = MemberStateIPA.objects.get(slug="nigeria")
        ghana = MemberStateIPA.objects.get(slug="ghana")

        years = [2020, 2021, 2022, 2023, 2024]

        # Nigeria FDI data
        nigeria_values = [2300, 2400, 2450, 2480, 2500]
        for year, value in zip(years, nigeria_values):
            fdi, created = FDIDataPoint.objects.get_or_create(
                member_state=nigeria,
                year=year,
                defaults={
                    "value": Decimal(str(value)),
                    "data_source": "UNCTAD World Investment Report",
                },
            )
            status = "✓ Created" if created else "- Exists"
            print(f"{status}: {nigeria.country_name} {year}: ${value}M")

        # Ghana FDI data
        ghana_values = [1650, 1720, 1780, 1820, 1850]
        for year, value in zip(years, ghana_values):
            fdi, created = FDIDataPoint.objects.get_or_create(
                member_state=ghana,
                year=year,
                defaults={
                    "value": Decimal(str(value)),
                    "data_source": "UNCTAD World Investment Report",
                },
            )
            status = "✓ Created" if created else "- Exists"
            print(f"{status}: {ghana.country_name} {year}: ${value}M")

    except Exception as e:
        print(f"⚠ Error creating FDI data: {e}")


def create_ipa_staff():
    """Create IPA staff members"""
    print("\n" + "=" * 60)
    print("CREATING IPA STAFF")
    print("=" * 60)

    try:
        nigeria = MemberStateIPA.objects.get(slug="nigeria")

        staff_data = [
            {
                "full_name": "Aisha RIMI",
                "position_title": "Executive Secretary/CEO",
                "email": "aisha.rimi@nipc.gov.ng",
                "phone": "+2349032290456",
                # "is_leadership": True,
                "display_order": 10,
            },
            {
                "full_name": "Emeka Offor",
                "position_title": "Director, Investment Promotion",
                "email": "emeka.offor@nipc.gov.ng",
                "phone": "+2348012345678",
                # "is_leadership": True,
                "display_order": 20,
            },
            {
                "full_name": "Ngozi Okeke",
                "position_title": "Head, Aftercare Services",
                "email": "ngozi.okeke@nipc.gov.ng",
                "phone": "+2348023456789",
                # "is_leadership": False,
                "display_order": 30,
            },
        ]

        for staff in staff_data:
            staff_obj, created = IPAStaff.objects.get_or_create(
                member_state=nigeria, email=staff["email"], defaults=staff
            )
            status = "✓ Created" if created else "- Exists"
            print(f"{status}: {staff_obj.full_name} - {nigeria.country_name}")

    except Exception as e:
        print(f"⚠ Error creating IPA staff: {e}")


if __name__ == "__main__":
    create_member_state_sectors()
    create_investment_incentives()
    create_success_stories()
    create_investor_inquiries()
    create_fdi_data_points()
    create_ipa_staff()

    print("\n" + "=" * 60)
    print("MEMBERS DATA POPULATION (Part 3) COMPLETE")
    print("=" * 60)
    print(f"\nCreated:")
    print(f"- {MemberStateSector.objects.count()} Member State Sectors")
    print(f"- {InvestmentIncentive.objects.count()} Investment Incentives")
    print(f"- {SuccessStory.objects.count()} Success Stories")
    print(f"- {InvestorInquiry.objects.count()} Investor Inquiries")
    print(f"- {FDIDataPoint.objects.count()} FDI Data Points")
    print(f"- {IPAStaff.objects.count()} IPA Staff Members")
    print("=" * 60)
