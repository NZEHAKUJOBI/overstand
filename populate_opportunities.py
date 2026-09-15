"""
IPAWAS Data Population - Opportunities App
Creates Investment Opportunities, Opportunity Documents, Inquiries, and Updates
"""

import os
from datetime import datetime, timedelta
from decimal import Decimal

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth import get_user_model

from core.models import Sector
from members.models import MemberStateIPA
from opportunities.models import (
    InvestmentOpportunity,
    OpportunityDocument,
    OpportunityInquiry,
    OpportunityUpdate,
)

User = get_user_model()


def create_investment_opportunities():
    """Create investment opportunities across member states"""
    print("\n" + "=" * 60)
    print("CREATING INVESTMENT OPPORTUNITIES")
    print("=" * 60)

    try:
        nigeria = MemberStateIPA.objects.get(slug="nigeria")
        ghana = MemberStateIPA.objects.get(slug="ghana")
        senegal = MemberStateIPA.objects.get(slug="senegal")

        agriculture = Sector.objects.get(slug="agriculture-agribusiness")
        energy = Sector.objects.get(slug="energy-power")
        manufacturing = Sector.objects.get(slug="manufacturing")
        tech = Sector.objects.get(slug="technology-ict")
        infrastructure = Sector.objects.get(slug="infrastructure")

        opportunities_data = [
            {
                "primary_country": nigeria,
                "title": "Lagos-Ibadan Inland Dry Port Development",
                "opportunity_type": "greenfield",
                "primary_sector": infrastructure,
                "description": "Development of modern inland dry port facility to support trade facilitation and reduce port congestion in Lagos",
                "summary": "A 100-hectare integrated inland dry port with container handling, warehousing, and logistics services",
                "specific_location": "Ibadan, Oyo State, Nigeria",
                "investment_required_min": Decimal("50000000"),
                "investment_required_max": Decimal("80000000"),
                "expected_roi": Decimal("18.5"),
                "payback_period": 7,
                # "key_benefits": "Strategic location on Lagos-Kano corridor, government support, high demand for logistics services, tax incentives available",
                # "investment_structure": "PPP - 60% Private, 40% Government",
                "status": "active",
                "featured": True,
                "published": True,
            },
            {
                "primary_country": nigeria,
                "title": "Cassava Processing and Ethanol Production Plant",
                "opportunity_type": "greenfield",
                "primary_sector": agriculture,
                "description": "Integrated cassava processing facility producing ethanol, starch, and cassava flour for domestic and export markets",
                "summary": "Modern processing plant with 100 tons per day capacity, targeting growing demand for industrial starch and bio-ethanol",
                "specific_location": "Benue State, Nigeria",
                "investment_required_min": Decimal("25000000"),
                "investment_required_max": Decimal("35000000"),
                "expected_roi": Decimal("22.0"),
                "payback_period": 5,
                # "key_benefits": "Abundant raw material supply, pioneer status tax holiday, export market access, strong local demand",
                # "investment_structure": "Private Investment (100% foreign ownership allowed)",
                "status": "active",
                "featured": True,
                "published": True,
            },
            {
                "primary_country": ghana,
                "title": "200MW Solar Power Plant",
                "opportunity_type": "greenfield",
                "primary_sector": energy,
                "description": "Large-scale solar photovoltaic plant to contribute to Ghana's renewable energy targets and power supply stability",
                "summary": "Grid-connected solar farm with advanced PV technology and battery storage system",
                "specific_location": "Upper West Region, Ghana",
                "investment_required_min": Decimal("180000000"),
                "investment_required_max": Decimal("220000000"),
                "expected_roi": Decimal("15.0"),
                "payback_period": 10,
                # "key_benefits": "Guaranteed Power Purchase Agreement, World Bank backing, tax incentives, excellent solar irradiation",
                # "investment_structure": "IPP Model with 20-year PPA",
                "status": "active",
                "featured": True,
                "published": True,
            },
            {
                "primary_country": ghana,
                "title": "Cocoa Processing and Chocolate Manufacturing Facility",
                "opportunity_type": "expansion",
                "primary_sector": agriculture,
                "description": "Expansion of existing cocoa processing capacity and addition of finished chocolate products line",
                "summary": "Upgrade facility to process 50,000 MT of cocoa beans annually and produce premium chocolate for export",
                "specific_location": "Takoradi, Western Region, Ghana",
                "investment_required_min": Decimal("15000000"),
                "investment_required_max": Decimal("20000000"),
                "expected_roi": Decimal("20.0"),
                "payback_period": 6,
                # "key_benefits": "Access to high-quality cocoa, GIPC incentives, export processing zone benefits, growing chocolate market",
                # "investment_structure": "Joint Venture or Private Investment",
                "status": "active",
                "featured": False,
                "published": True,
            },
            {
                "primary_country": senegal,
                "title": "Dakar Technology and Innovation Hub",
                "opportunity_type": "greenfield",
                "primary_sector": tech,
                "description": "Modern technology park providing office space, incubation services, and infrastructure for tech startups and companies",
                "summary": "Smart building complex with co-working spaces, data center, training facilities, and startup accelerator programs",
                "specific_location": "Diamniadio, Dakar, Senegal",
                "investment_required_min": Decimal("40000000"),
                "investment_required_max": Decimal("60000000"),
                "expected_roi": Decimal("16.0"),
                "payback_period": 8,
                # "key_benefits": "Government support, growing tech ecosystem, strategic location, French-speaking market access, tax holidays",
                # "investment_structure": "Private Development with Government Support",
                "status": "active",
                "featured": True,
                "published": True,
            },
            {
                "primary_country": senegal,
                "title": "Fish Processing and Cold Chain Infrastructure",
                "opportunity_type": "greenfield",
                "primary_sector": agriculture,
                "description": "Integrated fish processing facility with modern cold storage and cold chain logistics for domestic and export markets",
                "summary": "Processing capacity of 200 tons per day with freezing, packaging, and storage facilities",
                "specific_location": "Saint-Louis, Senegal",
                "investment_required_min": Decimal("20000000"),
                "investment_required_max": Decimal("30000000"),
                "expected_roi": Decimal("19.0"),
                "payback_period": 6,
                # "key_benefits": "Rich fishing grounds, export market access, APIX incentives, growing regional demand",
                # "investment_structure": "Private Investment or Joint Venture",
                "status": "active",
                "featured": False,
                "published": True,
            },
            {
                "primary_country": nigeria,
                "title": "Pharmaceutical Manufacturing Plant",
                "opportunity_type": "greenfield",
                "primary_sector": manufacturing,
                "description": "WHO-GMP certified pharmaceutical manufacturing facility producing essential medicines for West African market",
                "summary": "Integrated plant producing tablets, capsules, and injectables with capacity for export",
                "specific_location": "Lagos State, Nigeria",
                "investment_required_min": Decimal("30000000"),
                "investment_required_max": Decimal("45000000"),
                "expected_roi": Decimal("21.0"),
                "payback_period": 5,
                # "key_benefits": "Large population, import substitution, ECOWAS market access, pioneer status available, high margins",
                # "investment_structure": "Private Investment",
                "status": "active",
                "featured": False,
                "published": True,
            },
        ]

        for data in opportunities_data:
            opp, created = InvestmentOpportunity.objects.get_or_create(
                primary_country=data["primary_country"],
                slug=data["title"].lower().replace(" ", "-")[:50],
                defaults=data,
            )
            status = "✓ Created" if created else "- Exists"
            print(f"{status}: {opp.title} - {opp.primary_country.country_name}")

    except Exception as e:
        print(f"⚠ Error creating opportunities: {e}")


def create_opportunity_documents():
    """Create documents for opportunities"""
    print("\n" + "=" * 60)
    print("CREATING OPPORTUNITY DOCUMENTS")
    print("=" * 60)

    try:
        opp = InvestmentOpportunity.objects.get(slug="lagos-ibadan-inland-dry-port-development")

        documents_data = [
            {
                "opportunity": opp,
                "document_type": "feasibility",
                "title": "Feasibility Study - Inland Dry Port Development",
                "description": "Comprehensive feasibility study covering market analysis, technical specifications, and financial projections",
                "display_order": 10,
            },
            {
                "opportunity": opp,
                "document_type": "tender",
                "title": "Request for Proposal (RFP)",
                "description": "Official RFP document with project requirements, timelines, and evaluation criteria",
                "display_order": 20,
            },
            {
                "opportunity": opp,
                "document_type": "presentation",
                "title": "Investor Presentation Deck",
                "description": "Executive summary presentation highlighting project benefits and investment structure",
                "display_order": 30,
            },
        ]

        for data in documents_data:
            doc, created = OpportunityDocument.objects.get_or_create(
                opportunity=data["opportunity"], title=data["title"], defaults=data
            )
            status = "✓ Created" if created else "- Exists"
            print(f"{status}: {doc.title}")

    except Exception as e:
        print(f"⚠ Error creating documents: {e}")


def create_opportunity_inquiries():
    """Create sample inquiries for opportunities"""
    print("\n" + "=" * 60)
    print("CREATING OPPORTUNITY INQUIRIES")
    print("=" * 60)

    try:
        dry_port = InvestmentOpportunity.objects.get(
            slug="lagos-ibadan-inland-dry-port-development"
        )
        solar = InvestmentOpportunity.objects.get(slug="200mw-solar-power-plant")

        inquiries_data = [
            {
                "opportunity": dry_port,
                "full_name": "Robert Chen",
                # "last_name": "Chen",
                "email": "rchen@globallogistics.com",
                "phone": "+65 9123 4567",
                "company_name": "Global Logistics Partners",
                "company_country": "Singapore",
                "message": "Interested in the inland dry port project. Would like to schedule a site visit and discuss partnership structure. Our company has experience developing similar facilities in Southeast Asia.",
                "status": "new",
            },
            {
                "opportunity": solar,
                "full_name": "Elena Martinez",
                # "last_name": "Martinez",
                "email": "emartinez@sunpowerfund.com",
                "phone": "+34 91 123 4567",
                "company_name": "SunPower Investment Fund",
                "company_country": "Spain",
                "message": "Our fund is actively looking for solar projects in Africa. Please provide more details on PPA terms, grid connection status, and required equity participation.",
                "status": "contacted",
            },
        ]

        for data in inquiries_data:
            inquiry, created = OpportunityInquiry.objects.get_or_create(
                opportunity=data["opportunity"], email=data["email"], defaults=data
            )
            status = "✓ Created" if created else "- Exists"
            print(f"{status}: {inquiry.full_name} - {inquiry.opportunity.title}")

    except Exception as e:
        print(f"⚠ Error creating inquiries: {e}")


def create_opportunity_updates():
    """Create status updates for opportunities"""
    print("\n" + "=" * 60)
    print("CREATING OPPORTUNITY UPDATES")
    print("=" * 60)

    try:
        dry_port = InvestmentOpportunity.objects.get(
            slug="lagos-ibadan-inland-dry-port-development"
        )
        cassava = InvestmentOpportunity.objects.get(
            slug="cassava-processing-and-ethanol-production-plant"
        )

        now = datetime.now()

        updates_data = [
            {
                "opportunity": dry_port,
                "update_type": "milestone",
                "title": "Environmental Impact Assessment Completed",
                "description": "The Environmental Impact Assessment has been successfully completed and approved by regulatory authorities. This clears a major milestone for the project and potential investors can now proceed with due diligence.",
                "created_at": now - timedelta(days=10),
            },
            {
                "opportunity": dry_port,
                "update_type": "document",
                "title": "Updated Financial Model Available",
                "description": "An updated financial model reflecting recent cost adjustments and revised revenue projections is now available for qualified investors. Contact the IPA to request access.",
                "created_at": now - timedelta(days=5),
            },
            {
                "opportunity": cassava,
                "update_type": "progress",
                "title": "Land Acquisition Finalized",
                "description": "The project site acquisition has been completed. 50 hectares of land with clear title has been secured in a prime agricultural zone with excellent access to raw materials and transportation networks.",
                "created_at": now - timedelta(days=20),
            },
        ]

        for data in updates_data:
            update, created = OpportunityUpdate.objects.get_or_create(
                opportunity=data["opportunity"], title=data["title"], defaults=data
            )
            status = "✓ Created" if created else "- Exists"
            print(f"{status}: {update.title}")

    except Exception as e:
        print(f"⚠ Error creating updates: {e}")


if __name__ == "__main__":
    create_investment_opportunities()
    create_opportunity_documents()
    create_opportunity_inquiries()
    create_opportunity_updates()

    print("\n" + "=" * 60)
    print("OPPORTUNITIES DATA POPULATION COMPLETE")
    print("=" * 60)
    print(f"\nCreated:")
    print(f"- {InvestmentOpportunity.objects.count()} Investment Opportunities")
    print(f"- {OpportunityDocument.objects.count()} Opportunity Documents")
    print(f"- {OpportunityInquiry.objects.count()} Opportunity Inquiries")
    print(f"- {OpportunityUpdate.objects.count()} Opportunity Updates")
    print("=" * 60)
