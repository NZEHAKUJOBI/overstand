"""
IPAWAS Data Population - Accounts App (CORRECTED)
Creates users, superuser, HQ admin, and IPA staff

IMPORTANT: Your User model uses EMAIL as USERNAME_FIELD (no username field)
"""

import os

import django
from django.contrib.auth import get_user_model

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth.models import Group, Permission

from accounts.models import IPAUser

User = get_user_model()


def create_users():
    """Create system users"""
    print("\n" + "=" * 60)
    print("CREATING USERS")
    print("=" * 60)

    # 1. Superuser (email-based, no username)
    if not User.objects.filter(email="admin@ipawas.org").exists():
        superuser = User.objects.create_superuser(
            email="admin@ipawas.org",
            # username="admin@ipawas.org",
            password="IPAWASadmin2025!",
            first_name="System",
            last_name="Administrator",
            user_type="ipawas_admin",
            is_active=True,
        )
        print(f"✓ Created Superuser: {superuser.email}")
    else:
        print(f"- Exists: Superuser (admin@ipawas.org)")

    # 2. HQ Admin
    if not User.objects.filter(email="hq@ipawas.org").exists():
        hq_admin = User.objects.create_user(
            email="hq@ipawas.org",
            # username="admin@ipawas.org",
            password="IPAWAS_HQ2025!",
            first_name="Headquarters",
            last_name="Administrator",
            user_type="ipawas_admin",
            is_staff=True,
            is_active=True,
        )
        print(f"✓ Created HQ Admin: {hq_admin.email}")
    else:
        print(f"- Exists: HQ Admin (hq@ipawas.org)")

    # 3. Nigeria IPA Staff (NIPC)
    from members.models import MemberStateIPA

    try:
        nigeria = MemberStateIPA.objects.get(slug="nigeria")

        if not User.objects.filter(email="aisha.rimi@nipc.gov.ng").exists():
            nigeria_ceo = User.objects.create_user(
                email="aisha.rimi@nipc.gov.ng",
                password="NIPC2025!",
                first_name="Aisha",
                last_name="RIMI",
                user_type="ipa_staff",
                is_staff=True,
                is_active=True,
            )

            # Create IPA Profile
            IPAUser.objects.create(
                user=nigeria_ceo,
                member_state=nigeria,
                job_title="Executive Secretary/CEO",
                phone_number="+2349032290456",
                can_edit_profile=True,
                can_create_opportunities=True,
                can_publish=True,
                can_manage_users=True,
                can_view_analytics=True,
                is_primary_contact=True,
            )
            print(f"✓ Created Nigeria CEO: {nigeria_ceo.email}")
        else:
            print(f"- Exists: Nigeria CEO (aisha.rimi@nipc.gov.ng)")

        # Additional Nigeria staff
        if not User.objects.filter(email="festus.oshadare@nipc.gov.ng").exists():
            nigeria_staff = User.objects.create_user(
                email="festus.oshadare@nipc.gov.ng",
                password="NIPC_Staff2025!",
                first_name="Festus",
                last_name="Oshadare",
                user_type="ipa_staff",
                is_staff=True,
                is_active=True,
            )

            IPAUser.objects.create(
                user=nigeria_staff,
                member_state=nigeria,
                job_title="Senior Investment Officer",
                phone_number="+2348012345678",
                can_edit_profile=True,
                can_create_opportunities=True,
                can_publish=False,
                can_manage_users=False,
                can_view_analytics=True,
                is_primary_contact=False,
            )
            print(f"✓ Created Nigeria Staff: {nigeria_staff.email}")
        else:
            print(f"- Exists: Nigeria Staff (festus.oshadare@nipc.gov.ng)")

    except MemberStateIPA.DoesNotExist:
        print("⚠ Nigeria member state not found. Run populate_members scripts first.")
    except Exception as e:
        print(f"⚠ Error creating Nigeria users: {e}")


def create_groups_and_permissions():
    """Create user groups and assign permissions"""
    print("\n" + "=" * 60)
    print("CREATING GROUPS & PERMISSIONS")
    print("=" * 60)

    # HQ Admin Group
    hq_group, created = Group.objects.get_or_create(name="HQ Administrators")
    status = "✓ Created" if created else "- Exists"
    print(f"{status}: {hq_group.name}")

    # IPA CEO Group
    ipa_ceo_group, created = Group.objects.get_or_create(name="IPA CEOs")
    status = "✓ Created" if created else "- Exists"
    print(f"{status}: {ipa_ceo_group.name}")

    # IPA Staff Group
    ipa_staff_group, created = Group.objects.get_or_create(name="IPA Staff")
    status = "✓ Created" if created else "- Exists"
    print(f"{status}: {ipa_staff_group.name}")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("IPAWAS ACCOUNTS DATA POPULATION")
    print("=" * 60)
    print("\nNote: Your User model uses EMAIL authentication (no username)")

    create_users()
    create_groups_and_permissions()

    print("\n" + "=" * 60)
    print("ACCOUNTS DATA POPULATION COMPLETE")
    print("=" * 60)
    print("\nLogin Credentials:")
    print("-" * 60)
    print("Superuser:")
    print("  Email: admin@ipawas.org")
    print("  Password: IPAWASadmin2025!")
    print("")
    print("HQ Admin:")
    print("  Email: hq@ipawas.org")
    print("  Password: IPAWAS_HQ2025!")
    print("")
    print("Nigeria CEO:")
    print("  Email: aisha.rimi@nipc.gov.ng")
    print("  Password: NIPC2025!")
    print("")
    print("Nigeria Staff:")
    print("  Email: festus.oshadare@nipc.gov.ng")
    print("  Password: NIPC_Staff2025!")
    print("=" * 60)
    print("\n⚠ IMPORTANT: Change these passwords in production!")
    print("=" * 60)
