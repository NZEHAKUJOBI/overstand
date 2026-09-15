"""
Test factories for IPAWAS dashboard tests.
Uses factory_boy to create realistic test data.
"""

import factory
from django.utils.text import slugify

from accounts.models import IPAUser, User
from core.models import Sector
from members.models import InvestorInquiry, MemberStateIPA
from opportunities.models import InvestmentOpportunity


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    user_type = "public"
    is_active = True
    email_verified = True

    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        obj.set_password(extracted or "testpass123")
        if create:
            obj.save(update_fields=["password"])


class IPAWASAdminFactory(UserFactory):
    user_type = "ipawas_admin"
    email = factory.Sequence(lambda n: f"hqadmin{n}@ipawas.org")


class IPAStaffUserFactory(UserFactory):
    user_type = "ipa_staff"
    email = factory.Sequence(lambda n: f"ipastaff{n}@example.com")


class MemberStateIPAFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = MemberStateIPA

    country_name = factory.Sequence(lambda n: f"Testland {n}")
    slug = factory.LazyAttribute(lambda o: slugify(o.country_name))
    country_code = factory.Sequence(lambda n: f"T{n:02d}")
    ipa_full_name = factory.LazyAttribute(lambda o: f"{o.country_name} Investment Agency")
    ipa_acronym = factory.Sequence(lambda n: f"IA{n}")
    population = 10_000_000
    gdp = "50000000000.00"
    capital_city = "Testcity"
    official_language = "English"
    currency_name = "Testcoin"
    currency_code = "TST"
    contact_email = factory.Sequence(lambda n: f"ipa{n}@testland.test")
    is_active = True


class IPAUserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = IPAUser

    user = factory.SubFactory(IPAStaffUserFactory)
    member_state = factory.SubFactory(MemberStateIPAFactory)
    # ipa_director auto-sets can_manage_users=True and all other permissions via save()
    role = "ipa_director"


class InvestorInquiryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = InvestorInquiry

    member_state = factory.SubFactory(MemberStateIPAFactory)
    inquiry_type = "general"
    reference_number = factory.Sequence(lambda n: f"INQ-2025-{n:04d}")
    full_name = factory.Faker("name")
    email = factory.Faker("email")
    subject = factory.Faker("sentence", nb_words=5)
    message = factory.Faker("paragraph")
    status = "new"
    company_country = ""


class SectorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Sector
        django_get_or_create = ("slug",)

    name = factory.Sequence(lambda n: f"Test Sector {n}")
    slug = factory.Sequence(lambda n: f"test-sector-{n}")


class InvestmentOpportunityFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = InvestmentOpportunity

    title = factory.Sequence(lambda n: f"Test Opportunity {n}")
    summary = "Brief test summary."
    description = "Detailed test description."
    opportunity_type = "greenfield"
    primary_sector = factory.SubFactory(SectorFactory)
    primary_country = factory.SubFactory(MemberStateIPAFactory)
    investment_required_min = "1000000.00"
    status = "draft"
    published = False
