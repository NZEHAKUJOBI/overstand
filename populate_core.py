"""
IPAWAS Data Population - Core App
Creates Sectors, Partners, Publications, Events, Event Registrations
"""

import os
from datetime import datetime, timedelta
from decimal import Decimal

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth import get_user_model
from django.utils.text import slugify

from core.models import Event, EventRegistration, Partner, Publication, Sector

User = get_user_model()


def create_sectors():
    """Create investment sectors"""
    print("\n" + "=" * 60)
    print("CREATING SECTORS")
    print("=" * 60)

    sectors_data = [
        {
            "name": "Agriculture & Agribusiness",
            "description": "Food production, processing, and export including crops, livestock, fisheries, and value chains",
            # 'icon': 'agriculture'
        },
        {
            "name": "Manufacturing",
            "description": "Industrial production, processing industries, consumer goods, and industrial parks",
            # 'icon': 'industry'
        },
        {
            "name": "Energy & Power",
            "description": "Oil & gas, renewable energy, solar, wind, hydropower, and power generation infrastructure",
            # 'icon': 'energy'
        },
        {
            "name": "Infrastructure",
            "description": "Transport, roads, railways, ports, airports, and logistics facilities",
            # 'icon': 'construction'
        },
        {
            "name": "Technology & ICT",
            "description": "Information technology, telecommunications, fintech, e-commerce, and digital services",
            # 'icon': 'computer'
        },
        {
            "name": "Tourism & Hospitality",
            "description": "Hotels, resorts, eco-tourism, cultural heritage sites, and tourism infrastructure",
            # 'icon': 'hotel'
        },
        {
            "name": "Real Estate & Construction",
            "description": "Residential and commercial real estate development, urban planning, and construction",
            # 'icon': 'building'
        },
        {
            "name": "Healthcare & Pharmaceuticals",
            "description": "Hospitals, clinics, pharmaceutical manufacturing, medical equipment, and health services",
            # 'icon': 'health'
        },
        {
            "name": "Mining & Natural Resources",
            "description": "Mineral extraction, mining operations, solid minerals, and resource processing",
            # 'icon': 'mining'
        },
        {
            "name": "Financial Services",
            "description": "Banking, insurance, microfinance, investment services, and capital markets",
            # 'icon': 'finance'
        },
        {
            "name": "Education & Training",
            "description": "Educational institutions, vocational training, skills development, and e-learning",
            # 'icon': 'education'
        },
        {
            "name": "Retail & Trade",
            "description": "Retail chains, wholesale, distribution networks, and commercial trade",
            # 'icon': 'shopping'
        },
    ]

    for idx, data in enumerate(sectors_data, 1):
        sector, created = Sector.objects.get_or_create(
            slug=slugify(data["name"]),
            defaults={
                "name": data["name"],
                "description": data["description"],
                # 'icon': data['icon'],
                "is_active": True,
                "display_order": idx * 10,
            },
        )
        status = "✓ Created" if created else "- Exists"
        print(f"{status}: {sector.name}")


def create_partners():
    """Create strategic partners"""
    print("\n" + "=" * 60)
    print("CREATING PARTNERS")
    print("=" * 60)

    partners_data = [
        {
            "name": "Economic Community of West African States (ECOWAS)",
            "partner_type": "regional",
            "description": "Regional political and economic union of fifteen West African countries, promoting economic integration and cooperation",
            "website": "https://www.ecowas.int",
            # "country": "Regional",
            "featured": True,
        },
        {
            "name": "World Association of Investment Promotion Agencies (WAIPA)",
            "partner_type": "international",
            "description": "Global network of investment promotion agencies promoting best practices and knowledge sharing",
            "website": "https://www.waipa.org",
            # "country": "Switzerland",
            "featured": True,
        },
        {
            "name": "African Development Bank (AfDB)",
            "partner_type": "development",
            "description": "Multilateral development finance institution promoting economic and social development across Africa",
            "website": "https://www.afdb.org",
            # "country": "Regional",
            "featured": True,
        },
        {
            "name": "United Nations Industrial Development Organization (UNIDO)",
            "partner_type": "international",
            "description": "UN specialized agency promoting industrial development and international cooperation",
            "website": "https://www.unido.org",
            # "country": "Austria",
            "featured": False,
        },
        {
            "name": "International Finance Corporation (IFC)",
            "partner_type": "financial",
            "description": "World Bank Group member focused on private sector development in emerging markets",
            "website": "https://www.ifc.org",
            # "country": "USA",
            "featured": True,
        },
        {
            "name": "African Union",
            "partner_type": "regional",
            "description": "Continental body promoting unity, solidarity, cohesion and cooperation among African peoples and states",
            "website": "https://au.int",
            # "country": "Ethiopia",
            "featured": False,
        },
        {
            "name": "European Union",
            "partner_type": "international",
            "description": "Political and economic union supporting development and trade partnerships with Africa",
            "website": "https://europa.eu",
            # "country": "Belgium",
            "featured": False,
        },
        {
            "name": "United Nations Conference on Trade and Development (UNCTAD)",
            "partner_type": "international",
            "description": "UN body dealing with trade, investment, and development issues",
            "website": "https://unctad.org",
            # "country": "Switzerland",
            "featured": False,
        },
    ]

    for data in partners_data:
        partner, created = Partner.objects.get_or_create(
            slug=slugify(data["name"]),
            defaults={
                "name": data["name"],
                "partner_type": data["partner_type"],
                "description": data["description"],
                "website": data["website"],
                # "country": data["country"],
                "featured": data["featured"],
                "is_active": True,
            },
        )
        status = "✓ Created" if created else "- Exists"
        print(f"{status}: {partner.name}")


def create_publications():
    """Create publications and reports"""
    print("\n" + "=" * 60)
    print("CREATING PUBLICATIONS")
    print("=" * 60)

    publications_data = [
        {
            "title": "West Africa Investment Climate Report 2024",
            "publication_type": "report",
            "description": "Comprehensive analysis of investment trends, opportunities, and challenges across West African economies",
            # "summary": "This report examines investment flows, policy reforms, and sector performance across ECOWAS member states, providing insights for investors and policymakers.",
            "publication_date": datetime(2024, 6, 15),
            "featured": True,
        },
        {
            "title": "IPAWAS Annual Report 2023",
            "publication_type": "report",
            "description": "Annual review of IPAWAS activities, achievements, and strategic initiatives",
            # "summary": "Highlights of regional investment promotion activities, capacity building programs, and member state collaboration in 2023.",
            "publication_date": datetime(2024, 3, 1),
            "featured": True,
        },
        {
            "title": "Doing Business in West Africa: A Guide for Investors",
            "publication_type": "guide",
            "description": "Practical guide covering legal, regulatory, and operational aspects of investing in West Africa",
            # "summary": "Step-by-step guide on business registration, taxation, labor laws, and investment incentives across the region.",
            "publication_date": datetime(2024, 1, 20),
            "featured": True,
        },
        {
            "title": "Agricultural Investment Opportunities in ECOWAS",
            "publication_type": "research",
            "description": "Sector study on agriculture and agribusiness investment potential in West Africa",
            # "summary": "Analysis of value chains, market access, infrastructure, and investment opportunities in the agricultural sector.",
            "publication_date": datetime(2023, 11, 10),
            "featured": False,
        },
        {
            "title": "Renewable Energy Investment Guide",
            "publication_type": "guide",
            "description": "Guide to renewable energy investment policies, incentives, and projects in West Africa",
            # "summary": "Overview of solar, wind, and hydropower opportunities, regulatory frameworks, and financing options.",
            "publication_date": datetime(2023, 9, 5),
            "featured": False,
        },
        {
            "title": "IPAWAS Quarterly Newsletter Q4 2024",
            "publication_type": "newsletter",
            "description": "Latest news, events, and investment updates from across the region",
            # "summary": "Member state highlights, upcoming events, policy updates, and success stories.",
            "publication_date": datetime(2024, 12, 1),
            "featured": False,
        },
    ]

    for data in publications_data:
        pub, created = Publication.objects.get_or_create(
            slug=slugify(data["title"]),
            defaults={
                "title": data["title"],
                "publication_type": data["publication_type"],
                "description": data["description"],
                # "summary": data["summary"],
                "publication_date": data["publication_date"],
                "featured": data["featured"],
                "published": True,
            },
        )
        status = "✓ Created" if created else "- Exists"
        print(f"{status}: {pub.title}")


def create_events():
    """Create events and registrations"""
    print("\n" + "=" * 60)
    print("CREATING EVENTS")
    print("=" * 60)

    now = datetime.now()

    events_data = [
        {
            "title": "West Africa Investment Forum 2025",
            "event_type": "conference",
            "description": "Premier investment promotion platform bringing together investors, policymakers, and business leaders",
            "start_date": (now + timedelta(days=90)).date(),
            "end_date": (now + timedelta(days=92)).date(),
            # "location": "Abuja, Nigeria",
            "venue": "Transcorp Hilton",
            "max_participants": 500,
            "registration_fee": Decimal("250.00"),
            "featured": True,
            # "is_published": True,
            # "registration_open": True,
        },
        {
            "title": "IPA Capacity Building Workshop: Digital Marketing",
            "event_type": "workshop",
            "description": "Training workshop on digital marketing strategies for investment promotion",
            "start_date": (now + timedelta(days=45)).date(),
            "end_date": (now + timedelta(days=47)).date(),
            # "location": "Accra, Ghana",
            "venue": "Kempinski Gold Coast Hotel",
            "max_participants": 50,
            "registration_fee": Decimal("100.00"),
            "featured": False,
            # "is_published": True,
            # "registration_open": True,
        },
        {
            "title": "Renewable Energy Investment Roundtable",
            "event_type": "roundtable",
            "description": "High-level discussion on renewable energy investment opportunities and challenges",
            "start_date": (now + timedelta(days=60)).date(),
            "end_date": (now + timedelta(days=60)).date(),
            # "location": "Dakar, Senegal",
            "venue": "Radisson Blu Hotel",
            "max_participants": 80,
            "registration_fee": Decimal("150.00"),
            "featured": True,
            # "is_published": True,
            # "registration_open": True,
        },
        {
            "title": "Agribusiness Investment Mission to Nigeria",
            "event_type": "mission",
            "description": "Site visits and business matching for agribusiness investors",
            "start_date": (now + timedelta(days=120)).date(),
            "end_date": (now + timedelta(days=125)).date(),
            # "location": "Lagos & Kano, Nigeria",
            "venue": "Multiple locations",
            "max_participants": 30,
            "registration_fee": Decimal("500.00"),
            "featured": True,
            # "is_published": True,
            # "registration_open": True,
        },
        {
            "title": "IPAWAS Annual General Meeting 2025",
            "event_type": "meeting",
            "description": "Annual meeting of IPAWAS members to review activities and plan ahead",
            "start_date": (now + timedelta(days=180)).date(),
            "end_date": (now + timedelta(days=182)).date(),
            # "location": "Abidjan, Côte d'Ivoire",
            "venue": "Sofitel Abidjan Hotel Ivoire",
            "max_participants": 100,
            "registration_fee": Decimal("0.00"),
            "featured": False,
            # "is_published": True,
            # "registration_open": True,
        },
    ]

    for data in events_data:
        event, created = Event.objects.get_or_create(
            slug=slugify(data["title"]),
            defaults={
                "title": data["title"],
                "event_type": data["event_type"],
                "description": data["description"],
                "start_date": data["start_date"],
                "end_date": data["end_date"],
                # "location": data["location"],
                "venue": data["venue"],
                "max_participants": data["max_participants"],
                "registration_fee": data["registration_fee"],
                "featured": data["featured"],
                # # "is_published": data["is_published"],
                # "registration_open": data["registration_open"],
            },
        )
        status = "✓ Created" if created else "- Exists"
        print(f"{status}: {event.title}")


def create_event_registrations():
    """Create sample event registrations"""
    print("\n" + "=" * 60)
    print("CREATING EVENT REGISTRATIONS")
    print("=" * 60)

    try:
        event = Event.objects.get(slug="west-africa-investment-forum-2025")

        registrations_data = [
            {
                "first_name": "John",
                "last_name": "Mensah",
                "email": "john.mensah@example.com",
                "phone": "+233244567890",
                "company": "Ghana Investment Holdings",
                "position": "Managing Director",
                "country": "Ghana",
            },
            {
                "first_name": "Marie",
                "last_name": "Diop",
                "email": "marie.diop@example.com",
                "phone": "+221778901234",
                "company": "Senegal Development Partners",
                "position": "Investment Analyst",
                "country": "Senegal",
            },
            {
                "first_name": "David",
                "last_name": "Johnson",
                "email": "david.johnson@example.com",
                "phone": "+14155551234",
                "company": "Global Infrastructure Fund",
                "position": "Senior Portfolio Manager",
                "country": "United States",
            },
        ]

        for data in registrations_data:
            reg, created = EventRegistration.objects.get_or_create(
                event=event,
                email=data["email"],
                defaults={
                    "full_name": data["first_name"],
                    # "last_name": data["last_name"],
                    "phone": data["phone"],
                    # "company": data["company"],
                    # "position": data["position"],
                    "country": data["country"],
                    # "status": "confirmed",
                },
            )
            status = "✓ Created" if created else "- Exists"
            print(f"{status}: {reg.full_name} - {event.title}")
    except Event.DoesNotExist:
        print("⚠ Event not found")


if __name__ == "__main__":
    create_sectors()
    create_partners()
    create_publications()
    create_events()
    create_event_registrations()

    print("\n" + "=" * 60)
    print("CORE DATA POPULATION COMPLETE")
    print("=" * 60)
    print(f"\nCreated:")
    print(f"- {Sector.objects.count()} Sectors")
    print(f"- {Partner.objects.count()} Partners")
    print(f"- {Publication.objects.count()} Publications")
    print(f"- {Event.objects.count()} Events")
    print(f"- {EventRegistration.objects.count()} Event Registrations")
    print("=" * 60)
