"""
Activity Logging and Notification Services.

Provides convenience methods for creating activity logs and notifications.
"""

from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from dashboard.models import IPADashboardActivity, IPANotification


class ActivityLogService:
    """
    Service for creating activity logs.
    Centralizes activity logging logic.
    """

    @staticmethod
    def log_activity(
        user,
        action_type,
        description,
        member_state=None,
        content_object=None,
        changes=None,
        ip_address=None,
        user_agent=None,
    ):
        """
        Log a dashboard activity.

        Args:
            user: User performing the action
            action_type: Type of action
            description: Human-readable description
            member_state: Related member state (optional)
            content_object: Related object (optional)
            changes: Dict of changes (optional)
            ip_address: IP address (optional)
            user_agent: User agent string (optional)

        Returns:
            IPADashboardActivity instance
        """

        return IPADashboardActivity.objects.log_activity(
            user=user,
            action_type=action_type,
            description=description,
            member_state=member_state,
            content_object=content_object,
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    @staticmethod
    def log_login(user, ip_address=None):
        """Log user login"""
        return ActivityLogService.log_activity(
            user=user,
            action_type="login",
            description=f"{user.get_full_name()} logged in",
            ip_address=ip_address,
        )

    @staticmethod
    def log_logout(user, ip_address=None):
        """Log user logout"""
        return ActivityLogService.log_activity(
            user=user,
            action_type="logout",
            description=f"{user.get_full_name()} logged out",
            ip_address=ip_address,
        )

    @staticmethod
    def log_profile_update(user, member_state, changes=None, ip_address=None):
        """Log member state profile update"""
        return ActivityLogService.log_activity(
            user=user,
            action_type="profile_update",
            description=f"Updated {member_state.country_name} profile",
            member_state=member_state,
            content_object=member_state,
            changes=changes,
            ip_address=ip_address,
        )

    @staticmethod
    def log_opportunity_create(user, opportunity, ip_address=None):
        """Log opportunity creation"""
        return ActivityLogService.log_activity(
            user=user,
            action_type="opportunity_create",
            description=f"Created opportunity: {opportunity.title}",
            member_state=opportunity.member_state,
            content_object=opportunity,
            ip_address=ip_address,
        )

    @staticmethod
    def log_opportunity_update(user, opportunity, changes=None, ip_address=None):
        """Log opportunity update"""
        return ActivityLogService.log_activity(
            user=user,
            action_type="opportunity_update",
            description=f"Updated opportunity: {opportunity.title}",
            member_state=opportunity.member_state,
            content_object=opportunity,
            changes=changes,
            ip_address=ip_address,
        )

    @staticmethod
    def log_opportunity_publish(user, opportunity, ip_address=None):
        """Log opportunity publishing"""
        return ActivityLogService.log_activity(
            user=user,
            action_type="opportunity_publish",
            description=f"Published opportunity: {opportunity.title}",
            member_state=opportunity.member_state,
            content_object=opportunity,
            ip_address=ip_address,
        )

    @staticmethod
    def log_opportunity_delete(user, opportunity_title, member_state, ip_address=None):
        """Log opportunity deletion"""
        return ActivityLogService.log_activity(
            user=user,
            action_type="opportunity_delete",
            description=f"Deleted opportunity: {opportunity_title}",
            member_state=member_state,
            ip_address=ip_address,
        )

    @staticmethod
    def log_inquiry_view(user, inquiry, ip_address=None):
        """Log inquiry view"""
        return ActivityLogService.log_activity(
            user=user,
            action_type="inquiry_view",
            description=f"Viewed inquiry from {inquiry.full_name}",
            member_state=inquiry.member_state,
            content_object=inquiry,
            ip_address=ip_address,
        )

    @staticmethod
    def log_inquiry_respond(user, inquiry, ip_address=None):
        """Log inquiry response"""
        return ActivityLogService.log_activity(
            user=user,
            action_type="inquiry_respond",
            description=f"Responded to inquiry from {inquiry.full_name}",
            member_state=inquiry.member_state,
            content_object=inquiry,
            ip_address=ip_address,
        )

    @staticmethod
    def log_user_invite(user, invitation, ip_address=None):
        """Log user invitation"""
        if invitation.member_state:
            description = f"Invited {invitation.email} as {invitation.get_role_display()} for {invitation.member_state.ipa_acronym}"
        else:
            description = f"Invited {invitation.email} as IPAWAS HQ Admin"
        return ActivityLogService.log_activity(
            user=user,
            action_type="user_invite",
            description=description,
            member_state=invitation.member_state,
            content_object=invitation,
            ip_address=ip_address,
        )

    @staticmethod
    def log_user_create(user, created_by, ipa_user=None, ip_address=None):
        """Log user account creation.

        Args:
            user: The newly created User instance
            created_by: The User who created the account (invitation sender)
            ipa_user: IPAUser profile (None for HQ admin accounts with no member state)
            ip_address: Optional IP address
        """
        member_state = ipa_user.member_state if ipa_user is not None else None
        return ActivityLogService.log_activity(
            user=created_by,
            action_type="user_create",
            description=f"Created user account for {user.get_full_name()}",
            member_state=member_state,
            content_object=user,
            ip_address=ip_address,
        )

    @staticmethod
    def log_user_update(user, updated_user, changes=None, ip_address=None):
        """Log user update"""
        member_state = None
        if hasattr(updated_user, "ipa_profile"):
            member_state = updated_user.ipa_profile.member_state

        return ActivityLogService.log_activity(
            user=user,
            action_type="user_update",
            description=f"Updated user: {updated_user.get_full_name()}",
            member_state=member_state,
            content_object=updated_user,
            changes=changes,
            ip_address=ip_address,
        )

    @staticmethod
    def log_permission_change(user, affected_user, changes, ip_address=None):
        """Log permission changes"""
        member_state = None
        if hasattr(affected_user, "ipa_profile"):
            member_state = affected_user.ipa_profile.member_state

        return ActivityLogService.log_activity(
            user=user,
            action_type="permission_change",
            description=f"Changed permissions for {affected_user.get_full_name()}",
            member_state=member_state,
            content_object=affected_user,
            changes=changes,
            ip_address=ip_address,
        )

    @staticmethod
    def log_export(user, export_type, member_state=None, ip_address=None):
        """Log data export"""
        return ActivityLogService.log_activity(
            user=user,
            action_type="export_data",
            description=f"Exported {export_type} data",
            member_state=member_state,
            ip_address=ip_address,
        )


class NotificationService:
    """
    Service for creating notifications.
    Centralizes notification logic.
    """

    @staticmethod
    def create_notification(
        recipient,
        notification_type,
        title,
        message,
        link_url=None,
    ):
        """
        Create a notification.

        Args:
            recipient: IPAUser who will receive notification
            notification_type: Type of notification
            title: Short title
            message: Full message
            link_url: Optional link (optional)

        Returns:
            IPANotification instance
        """

        return IPANotification.objects.create_notification(
            recipient=recipient,
            notification_type=notification_type,
            title=title,
            message=message,
            link_url=link_url,
        )

    @staticmethod
    def notify_new_inquiry(inquiry, recipients):
        """
        Notify IPA staff of new investor inquiry.

        Args:
            inquiry: InvestorInquiry instance
            recipients: List of IPAUser instances
        """

        link_url = reverse("dashboard:inquiries:detail", kwargs={"pk": inquiry.pk})

        for ipa_user in recipients:
            if ipa_user.notify_on_inquiry:
                NotificationService.create_notification(
                    recipient=ipa_user,
                    notification_type="inquiry",
                    title=_("New Investor Inquiry"),
                    message=_("New inquiry from %(name)s regarding %(subject)s")
                    % {"name": inquiry.full_name, "subject": inquiry.subject},
                    link_url=link_url,
                )

    @staticmethod
    def notify_approval_needed(opportunity, recipient):
        """Notify that opportunity needs approval"""

        link_url = reverse("dashboard:opportunities:detail", kwargs={"pk": opportunity.pk})

        NotificationService.create_notification(
            recipient=recipient,
            notification_type="approval_needed",
            title=_("Approval Required"),
            message=_("Opportunity '%(title)s' is awaiting your approval")
            % {"title": opportunity.title},
            link_url=link_url,
        )

    @staticmethod
    def notify_content_approved(content, recipient, approver):
        """Notify that content was approved"""
        NotificationService.create_notification(
            recipient=recipient,
            notification_type="approved",
            title=_("Content Approved"),
            message=_("Your content has been approved by %(approver)s")
            % {"approver": approver.get_full_name()},
        )

    @staticmethod
    def notify_content_rejected(content, recipient, rejector, reason=""):
        """Notify that content was rejected"""
        message = _("Your content has been rejected by %(rejector)s") % {
            "rejector": rejector.get_full_name()
        }

        if reason:
            message += f"\nReason: {reason}"

        NotificationService.create_notification(
            recipient=recipient,
            notification_type="rejected",
            title=_("Content Rejected"),
            message=message,
        )

    @staticmethod
    def notify_opportunity_expiring(opportunity, recipients):
        """Notify that opportunity is expiring soon"""

        link_url = reverse("dashboard:opportunities:detail", kwargs={"pk": opportunity.pk})

        for ipa_user in recipients:
            if ipa_user.notify_on_opportunity_expiry:
                NotificationService.create_notification(
                    recipient=ipa_user,
                    notification_type="opportunity_expiring",
                    title=_("Opportunity Expiring Soon"),
                    message=_("Opportunity '%(title)s' will expire soon")
                    % {"title": opportunity.title},
                    link_url=link_url,
                )

    @staticmethod
    def notify_team_member_added(new_user, recipients):
        """Notify team of new member"""
        for ipa_user in recipients:
            if ipa_user.notify_on_team_changes and ipa_user.user != new_user:
                NotificationService.create_notification(
                    recipient=ipa_user,
                    notification_type="team_member_added",
                    title=_("New Team Member"),
                    message=_("%(name)s has joined your team as %(role)s")
                    % {
                        "name": new_user.get_full_name(),
                        "role": new_user.ipa_profile.get_role_display(),
                    },
                )

    @staticmethod
    def notify_team_member_removed(removed_user, recipients):
        """Notify team of member removal"""
        for ipa_user in recipients:
            if ipa_user.notify_on_team_changes:
                NotificationService.create_notification(
                    recipient=ipa_user,
                    notification_type="team_member_removed",
                    title=_("Team Member Removed"),
                    message=_("%(name)s has been removed from your team")
                    % {"name": removed_user.get_full_name()},
                )

    @staticmethod
    def notify_permission_changed(affected_user, changed_permissions):
        """Notify user their permissions changed"""
        if hasattr(affected_user, "ipa_profile"):
            NotificationService.create_notification(
                recipient=affected_user.ipa_profile,
                notification_type="permission_changed",
                title=_("Your Permissions Changed"),
                message=_("Your dashboard permissions have been updated"),
            )

    @staticmethod
    def notify_system_alert(recipients, title, message):
        """Send system alert to multiple users"""
        for ipa_user in recipients:
            NotificationService.create_notification(
                recipient=ipa_user,
                notification_type="system_alert",
                title=title,
                message=message,
            )

    @staticmethod
    def notify_announcement(recipients, title, message, link_url=None):
        """Send announcement to multiple users"""
        for ipa_user in recipients:
            NotificationService.create_notification(
                recipient=ipa_user,
                notification_type="announcement",
                title=title,
                message=message,
                link_url=link_url,
            )

    @staticmethod
    def notify_invitation_accepted(inviter, invitation, new_user):
        """Notify inviter that invitation was accepted"""
        if inviter and hasattr(inviter, "ipa_profile"):
            NotificationService.create_notification(
                recipient=inviter.ipa_profile,
                notification_type="announcement",
                title=_("Invitation Accepted"),
                message=_("%(name)s (%(email)s) has accepted your invitation and joined the team")
                % {"name": new_user.get_full_name(), "email": new_user.email},
            )


# Convenience functions
def log_activity(*args, **kwargs):
    """Shortcut to ActivityLogService.log_activity"""
    return ActivityLogService.log_activity(*args, **kwargs)


def create_notification(*args, **kwargs):
    """Shortcut to NotificationService.create_notification"""
    return NotificationService.create_notification(*args, **kwargs)
