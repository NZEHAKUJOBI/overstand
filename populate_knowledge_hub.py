"""
IPAWAS Data Population - Knowledge Hub App
Creates Topics, Tags, News Articles, Press Releases, Media Categories, Resources, Media Kit Items
"""

import os
from datetime import datetime, timedelta

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth import get_user_model

from core.models import Sector
from knowledge_hub.models import (
    MediaCategory,
    MediaKitItem,
    NewsArticle,
    PressRelease,
    Resource,
    Tag,
    Topic,
)
from members.models import MemberStateIPA

User = get_user_model()


def create_topics():
    """Create knowledge hub topics"""
    print("\n" + "=" * 60)
    print("CREATING TOPICS")
    print("=" * 60)

    topics_data = [
        {
            "name": "Investment Climate",
            "description": "Analysis and updates on investment environments, policies, and business climate across West Africa",
            # 'is_active': True,
            # 'display_order': 10
        },
        {
            "name": "Sector Analysis",
            "description": "In-depth analysis of key investment sectors including agriculture, energy, manufacturing, and technology",
            # 'is_active': True,
            # 'display_order': 20
        },
        {
            "name": "Policy & Regulation",
            "description": "Updates on investment policies, regulations, and reforms across member states",
            # 'is_active': True,
            # 'display_order': 30
        },
        {
            "name": "Success Stories",
            "description": "Investor success stories and case studies from across West Africa",
            # 'is_active': True,
            # 'display_order': 40
        },
        {
            "name": "Regional Integration",
            "description": "Updates on ECOWAS integration, AfCFTA implementation, and regional cooperation",
            # 'is_active': True,
            # 'display_order': 50
        },
        {
            "name": "Best Practices",
            "description": "Investment promotion best practices, strategies, and lessons learned",
            # 'is_active': True,
            # 'display_order': 60
        },
    ]

    for data in topics_data:
        topic, created = Topic.objects.get_or_create(
            slug=data["name"].lower().replace(" ", "-").replace("&", "and"), defaults=data
        )
        status = "✓ Created" if created else "- Exists"
        print(f"{status}: {topic.name}")


def create_tags():
    """Create content tags"""
    print("\n" + "=" * 60)
    print("CREATING TAGS")
    print("=" * 60)

    tags_list = [
        "Investment Opportunities",
        "FDI",
        "PPP",
        "Infrastructure",
        "Agriculture",
        "Technology",
        "Renewable Energy",
        "Manufacturing",
        "Trade",
        "Finance",
        "Tourism",
        "Mining",
        "Real Estate",
        "SME Development",
        "Industrial Parks",
        "Free Zones",
        "Policy Reform",
        "Business Environment",
        "Capacity Building",
        "Partnership",
        "Innovation",
        "Digital Economy",
        "Green Investment",
        "Sustainable Development",
        "Economic Growth",
    ]

    for tag_name in tags_list:
        tag, created = Tag.objects.get_or_create(
            slug=tag_name.lower().replace(" ", "-"), defaults={"name": tag_name}
        )
        status = "✓ Created" if created else "- Exists"
        print(f"{status}: {tag.name}")


def create_news_articles():
    """Create news articles"""
    print("\n" + "=" * 60)
    print("CREATING NEWS ARTICLES")
    print("=" * 60)

    now = datetime.now()

    articles_data = [
        {
            "title": "West Africa Attracts Record $12.5 Billion in FDI in 2024",
            "excerpt": "Foreign Direct Investment flows to West Africa reached unprecedented levels in 2024, driven by infrastructure projects, renewable energy investments, and manufacturing sector growth.",
            "content": """West Africa has achieved a significant milestone in 2024, attracting a record $12.5 billion in Foreign Direct Investment (FDI), marking a 15% increase from 2023. This growth reflects the region's improving business environment, political stability, and strategic economic reforms.

The manufacturing sector led with $4.2 billion in investments, followed by renewable energy at $3.8 billion, and infrastructure development at $2.5 billion. Nigeria, Ghana, and Côte d'Ivoire were the top recipients, accounting for 70% of total inflows.

Key drivers include the African Continental Free Trade Area (AfCFTA) implementation, improved ease of doing business rankings, and targeted investment promotion campaigns by member IPAs through IPAWAS coordination.""",
            "publication_date": now - timedelta(days=5),
            "featured": True,
            "published": True,
        },
        {
            "title": "IPAWAS Launches Regional Investment Intelligence Platform",
            "excerpt": "New digital platform to provide real-time investment data, opportunities, and analytics across all 12 ECOWAS member states.",
            "content": """IPAWAS has officially launched the West Africa Investment Intelligence System (WAIIS), a comprehensive digital platform designed to provide investors, policymakers, and stakeholders with real-time access to investment data and opportunities across the region.

The platform features interactive dashboards, sector analyses, project pipelines, and comparative investment climate assessments. It consolidates data from all 12 member state IPAs, offering unprecedented transparency and accessibility.

"This platform represents a quantum leap in our ability to serve investors and promote West Africa as a unified investment destination," said the IPAWAS President. The system will be continuously updated and enhanced based on user feedback.""",
            "publication_date": now - timedelta(days=15),
            "featured": True,
            "published": True,
        },
        {
            "title": "Renewable Energy Investments Surge Across West Africa",
            "excerpt": "Solar and wind projects worth over $5 billion announced across multiple member states as region accelerates green energy transition.",
            "content": """The renewable energy sector is experiencing explosive growth across West Africa, with new projects worth over $5 billion announced in recent months. Solar farms, wind installations, and hybrid renewable systems are being developed across multiple countries.

Senegal leads with a 300MW solar project, while Ghana is advancing with offshore wind development. Nigeria's renewable energy sector has attracted significant interest from international developers, with multiple projects in various stages of implementation.

This surge aligns with regional climate commitments and growing electricity demand. IPAWAS member IPAs are coordinating efforts to streamline regulatory processes and attract quality investments in the clean energy sector.""",
            "publication_date": now - timedelta(days=30),
            "featured": False,
            "published": True,
        },
    ]

    investment_topic = Topic.objects.get(slug="investment-climate")
    sector_topic = Topic.objects.get(slug="sector-analysis")

    fdi_tag = Tag.objects.get(slug="fdi")
    renewable_tag = Tag.objects.get(slug="renewable-energy")

    for data in articles_data:
        article, created = NewsArticle.objects.get_or_create(
            slug=data["title"].lower().replace(" ", "-")[:50],
            defaults={
                "title": data["title"],
                "excerpt": data["excerpt"],
                "content": data["content"],
                "publication_date": data["publication_date"],
                "featured": data["featured"],
                "published": data["published"],
            },
        )

        if created:
            article.topics.add(investment_topic)
            article.tags.add(fdi_tag)

        status = "✓ Created" if created else "- Exists"
        print(f"{status}: {article.title}")


def create_press_releases():
    """Create press releases"""
    print("\n" + "=" * 60)
    print("CREATING PRESS RELEASES")
    print("=" * 60)

    now = datetime.now()

    releases_data = [
        {
            "title": "IPAWAS Announces 2025 West Africa Investment Forum",
            "content": """FOR IMMEDIATE RELEASE

Abuja, Nigeria - The Investment Promotion Agencies of West African States (IPAWAS) is pleased to announce the 2025 West Africa Investment Forum, scheduled for April 15-17, 2025, in Abuja, Nigeria.

The forum will bring together over 500 investors, policymakers, and business leaders to explore investment opportunities across the ECOWAS region. The three-day event will feature panel discussions, country presentations, B2B matchmaking sessions, and site visits.

"This forum represents a unique opportunity to showcase West Africa's immense investment potential," said the IPAWAS President. "We've seen tremendous progress in improving our business environments, and this event will demonstrate our collective commitment to attracting and facilitating quality investments."

Key highlights include sector-specific roundtables on agriculture, energy, technology, and manufacturing, as well as sessions on navigating the AfCFTA and accessing regional markets.

Registration is now open at www.ipawas.org/forum2025

For media inquiries, contact: communications@ipawas.org""",
            "release_date": now - timedelta(days=10),
            "published": True,
        },
        {
            "title": "IPAWAS and WAIPA Sign Strategic Partnership Agreement",
            "content": """FOR IMMEDIATE RELEASE

Geneva, Switzerland / Abuja, Nigeria - IPAWAS and the World Association of Investment Promotion Agencies (WAIPA) have signed a strategic partnership agreement to enhance investment promotion capacity across West Africa.

The agreement facilitates knowledge exchange, technical assistance, and access to global best practices in investment promotion. Under this partnership, IPAWAS member IPAs will benefit from WAIPA's training programs, research resources, and international networks.

"This partnership strengthens our ability to serve investors and support our member IPAs," noted the IPAWAS leadership. "Access to WAIPA's global network and expertise will accelerate our efforts to position West Africa as a premier investment destination."

The collaboration includes joint research initiatives, capacity building workshops, and participation in global investment forums.

Contact: info@ipawas.org""",
            "release_date": now - timedelta(days=45),
            "published": True,
        },
    ]

    for data in releases_data:
        release, created = PressRelease.objects.get_or_create(
            slug=data["title"].lower().replace(" ", "-")[:50],
            defaults={
                "title": data["title"],
                "content": data["content"],
                "release_date": data["release_date"],
                "published": data["published"],
            },
        )
        status = "✓ Created" if created else "- Exists"
        print(f"{status}: {release.title}")


def create_media_categories():
    """Create media categories"""
    print("\n" + "=" * 60)
    print("CREATING MEDIA CATEGORIES")
    print("=" * 60)

    categories_data = [
        ("Brand Assets", "IPAWAS logos, colors, and brand guidelines", 10),
        ("Photos", "High-resolution photos from events and activities", 20),
        ("Videos", "Promotional and educational video content", 30),
        ("Publications", "Reports, brochures, and publications", 40),
        ("Infographics", "Visual data representations and infographics", 50),
    ]

    for name, desc, order in categories_data:
        cat, created = MediaCategory.objects.get_or_create(
            slug=name.lower().replace(" ", "-"),
            defaults={"name": name, "description": desc, "display_order": order},
        )
        status = "✓ Created" if created else "- Exists"
        print(f"{status}: {cat.name}")


def create_resources():
    """Create downloadable resources"""
    print("\n" + "=" * 60)
    print("CREATING RESOURCES")
    print("=" * 60)

    resources_data = [
        {
            "title": "Doing Business in West Africa - Investor Guide 2024",
            "resource_type": "guide",
            "description": "Comprehensive guide covering business establishment, regulations, incentives, and operational considerations across all 12 member states",
            "featured": True,
        },
        {
            "title": "West Africa Investment Climate Report 2024",
            "resource_type": "report",
            "description": "Annual analysis of investment trends, opportunities, and reforms across the ECOWAS region",
            "featured": True,
        },
        {
            "title": "Renewable Energy Investment Opportunities",
            "resource_type": "presentation",
            "description": "Presentation deck highlighting renewable energy projects and opportunities across West Africa",
            "featured": False,
        },
        {
            "title": "IPAWAS Membership Directory 2025",
            "resource_type": "directory",
            "description": "Contact information and profiles of all member state IPAs and key officials",
            "featured": False,
        },
    ]

    renewable_topic = Topic.objects.get(slug="sector-analysis")

    for data in resources_data:
        resource, created = Resource.objects.get_or_create(
            slug=data["title"].lower().replace(" ", "-")[:50],
            defaults={
                "title": data["title"],
                "resource_type": data["resource_type"],
                "description": data["description"],
                "featured": data["featured"],
                "published": True,
            },
        )
        status = "✓ Created" if created else "- Exists"
        print(f"{status}: {resource.title}")


# def create_media_kit_items():
#     """Create media kit items"""
#     print("\n" + "=" * 60)
#     print("CREATING MEDIA KIT ITEMS")
#     print("=" * 60)

#     brand_cat = MediaCategory.objects.get(slug="brand-assets")

#     media_items_data = [
#         {
#             "title": "IPAWAS Logo (Primary)",
#             "category": brand_cat,
#             "item_type": "logo",
#             "description": "Primary IPAWAS logo in full color for light backgrounds",
#             "display_order": 10,
#         },
#         {
#             "title": "IPAWAS Logo (White)",
#             "category": brand_cat,
#             "item_type": "logo",
#             "description": "IPAWAS logo in white for dark backgrounds",
#             "display_order": 20,
#         },
#         {
#             "title": "Brand Guidelines",
#             "category": brand_cat,
#             "item_type": "document",
#             "description": "Complete brand guidelines including logo usage, colors, typography, and style guide",
#             "display_order": 30,
#         },
#     ]

#     for data in media_items_data:
#         item, created = MediaKitItem.objects.get_or_create(title=data["title"], defaults=data)
#         status = "✓ Created" if created else "- Exists"
#         print(f"{status}: {item.title}")


if __name__ == "__main__":
    create_topics()
    create_tags()
    create_news_articles()
    create_press_releases()
    create_media_categories()
    create_resources()
    # create_media_kit_items()

    print("\n" + "=" * 60)
    print("KNOWLEDGE HUB DATA POPULATION COMPLETE")
    print("=" * 60)
    print(f"\nCreated:")
    print(f"- {Topic.objects.count()} Topics")
    print(f"- {Tag.objects.count()} Tags")
    print(f"- {NewsArticle.objects.count()} News Articles")
    print(f"- {PressRelease.objects.count()} Press Releases")
    print(f"- {MediaCategory.objects.count()} Media Categories")
    print(f"- {Resource.objects.count()} Resources")
    # print(f"- {MediaKitItem.objects.count()} Media Kit Items")
    print("=" * 60)
