"""
Django Signals for Accounts App
apps/accounts/signals.py

Automated actions triggered by model events:
- Log user activities
- Send notifications
- Update related records
- Clean up data
"""

from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from accounts.models import IPAUser, User

# ── Permission fields used across multiple signal handlers ────────────────────
_IPA_PERMISSION_FIELDS = [
    "can_publish_opportunities",
    "can_approve_data",
    "can_manage_users",
    "can_edit_profile",
    "can_manage_sectors",
    "can_create_opportunities",
    "can_edit_incentives",
    "can_manage_success_stories",
    "can_view_inquiries",
    "can_respond_to_inquiries",
    "can_view_analytics",
    "can_export_data",
]


# ── pre_save: capture old state BEFORE the DB write ──────────────────────────

@receiver(pre_save, sender=User)
def capture_user_old_state(sender, instance, **kwargs):
    """Attach old DB values to the instance so post_save handlers can diff."""
    if instance.pk:
        try:
            old = User.objects.get(pk=instance.pk)
            instance._pre_save_is_active = old.is_active
            instance._pre_save_email_verified = old.email_verified
            instance._pre_save_accepted_invitation_at = old.accepted_invitation_at
        except User.DoesNotExist:
            instance._pre_save_is_active = None
            instance._pre_save_email_verified = None
            instance._pre_save_accepted_invitation_at = None


@receiver(pre_save, sender=IPAUser)
def capture_ipa_user_old_state(sender, instance, **kwargs):
    """Attach old permission/role values to the instance so post_save can diff."""
    if instance.pk:
        try:
            old = IPAUser.objects.get(pk=instance.pk)
            instance._pre_save_permissions = {f: getattr(old, f) for f in _IPA_PERMISSION_FIELDS}
            instance._pre_save_role = old.role
        except IPAUser.DoesNotExist:
            instance._pre_save_permissions = {}
            instance._pre_save_role = None


@receiver(post_save, sender=User)
def create_activity_log_on_user_creation(sender, instance, created, **kwargs):
    """
    Log activity when a new user is created.
    """
    if created:
        from dashboard.models import IPADashboardActivity

        # Log user creation
        IPADashboardActivity.objects.log_activity(
            user=instance.invited_by if instance.invited_by else instance,
            action_type="user_create",
            description=f"New user account created: {instance.get_full_name()} ({instance.email})",
            member_state=getattr(instance, "ipa_profile", None)
            and instance.ipa_profile.member_state,
            content_object=instance,
        )


@receiver(post_save, sender=User)
def log_user_activation_change(sender, instance, created, **kwargs):
    """
    Log when user is activated or deactivated.
    """
    if not created:
        old_is_active = getattr(instance, "_pre_save_is_active", None)
        if old_is_active is not None and old_is_active != instance.is_active:
            from dashboard.models import IPADashboardActivity

            action_type = "user_create" if instance.is_active else "user_deactivate"
            description = (
                f"User {instance.get_full_name()} was "
                f"{'activated' if instance.is_active else 'deactivated'}"
            )

            IPADashboardActivity.objects.log_activity(
                user=instance,
                action_type=action_type,
                description=description,
                member_state=getattr(instance, "ipa_profile", None)
                and instance.ipa_profile.member_state,
            )


@receiver(post_save, sender=IPAUser)
def log_permission_changes(sender, instance, created, **kwargs):
    """
    Log when user permissions are changed.
    Uses _pre_save_permissions captured by capture_ipa_user_old_state.
    """
    if not created:
        from dashboard.models import IPADashboardActivity

        old_perms = getattr(instance, "_pre_save_permissions", {})
        old_role = getattr(instance, "_pre_save_role", None)
        changes = {}

        for field in _IPA_PERMISSION_FIELDS:
            if field in old_perms and old_perms[field] != getattr(instance, field):
                changes[field] = {"old": old_perms[field], "new": getattr(instance, field)}

        if old_role is not None and old_role != instance.role:
            changes["role"] = {
                "old": instance._meta.get_field("role").flatchoices and old_role,
                "new": instance.get_role_display(),
            }

        if changes:
            IPADashboardActivity.objects.log_activity(
                user=instance.user,
                action_type="permission_change",
                description=f"Permissions updated for {instance.user.get_full_name()}",
                member_state=instance.member_state,
                content_object=instance,
                changes=changes,
            )


@receiver(post_save, sender=User)
def send_welcome_email_on_verification(sender, instance, created, **kwargs):
    """
    Send welcome email when user verifies their email.
    Uses _pre_save_email_verified captured by capture_user_old_state.
    """
    if not created and instance.email_verified:
        old_verified = getattr(instance, "_pre_save_email_verified", None)
        if old_verified is False:
            # Email was just verified — send welcome email
            pass  # Implement email sending here when email service is configured


@receiver(post_save, sender=IPAUser)
def notify_user_of_permission_changes(sender, instance, created, **kwargs):
    """
    Notify user when their permissions are changed.
    Uses _pre_save_* captured by capture_ipa_user_old_state.
    """
    if not created:
        from dashboard.models import IPANotification

        old_perms = getattr(instance, "_pre_save_permissions", {})
        old_role = getattr(instance, "_pre_save_role", None)
        significant_changes = []

        if old_perms.get("can_publish_opportunities") != instance.can_publish_opportunities:
            significant_changes.append(
                f"Publish permissions: {'enabled' if instance.can_publish_opportunities else 'disabled'}"
            )
        if old_perms.get("can_manage_users") != instance.can_manage_users:
            significant_changes.append(
                f"User management: {'enabled' if instance.can_manage_users else 'disabled'}"
            )
        if old_role is not None and old_role != instance.role:
            significant_changes.append(f"Role changed to: {instance.get_role_display()}")

        if significant_changes:
            IPANotification.objects.create_notification(
                recipient=instance,
                notification_type="permission_changed",
                title="Your Permissions Have Been Updated",
                message="Your account permissions have been modified:\n"
                + "\n".join(f"• {change}" for change in significant_changes),
            )


@receiver(post_save, sender=User)
def create_notification_on_invitation_acceptance(sender, instance, created, **kwargs):
    """
    Notify the person who sent the invitation when it's accepted.
    Uses _pre_save_accepted_invitation_at captured by capture_user_old_state.
    """
    if not created and instance.accepted_invitation_at and instance.invited_by:
        old_accepted = getattr(instance, "_pre_save_accepted_invitation_at", None)
        if old_accepted is None and instance.accepted_invitation_at:
            from dashboard.models import IPANotification

            if hasattr(instance.invited_by, "ipa_profile"):
                IPANotification.objects.create_notification(
                    recipient=instance.invited_by.ipa_profile,
                    notification_type="team_member_added",
                    title="Invitation Accepted",
                    message=f"{instance.get_full_name()} has accepted your invitation and joined the team.",
                )


@receiver(pre_save, sender=User)
def track_password_change(sender, instance, **kwargs):
    """
    Track when password is changed.
    """
    try:
        old_instance = User.objects.get(pk=instance.pk)
        # Check if password changed
        if old_instance.password != instance.password:
            instance.password_changed_at = timezone.now()
    except User.DoesNotExist:
        # New user, set password_changed_at
        if instance.password:
            instance.password_changed_at = timezone.now()


@receiver(post_delete, sender=User)
def log_user_deletion(sender, instance, **kwargs):
    """
    Log when user account is deleted.
    """
    from dashboard.models import IPADashboardActivity

    # Try to get member state before deletion
    member_state = None
    if hasattr(instance, "ipa_profile"):
        member_state = instance.ipa_profile.member_state

    # Log deletion
    # Note: Since user is deleted, we can't associate activity with them
    # This would need a different user (admin who deleted them) passed in
    IPADashboardActivity.objects.create(
        user=None,  # No user since they're deleted
        action_type="user_delete",
        description=f"User account deleted: {instance.get_full_name()} ({instance.email})",
        member_state=member_state,
    )


@receiver(post_save, sender=IPAUser)
def update_primary_contact_exclusivity(sender, instance, created, **kwargs):
    """
    Ensure only one user per member state is marked as primary contact.
    """
    if instance.is_primary_contact:
        # Remove primary status from other users in same member state
        IPAUser.objects.filter(
            member_state=instance.member_state,
            is_primary_contact=True,
        ).exclude(pk=instance.pk).update(is_primary_contact=False)
