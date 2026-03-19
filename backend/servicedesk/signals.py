from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from .models import ServiceTicket, TicketResponse


@receiver(pre_save, sender=ServiceTicket)
def capture_ticket_previous_state(sender, instance, **kwargs):
    """Capture the previous status and priority before save for comparison."""
    if instance.pk:
        try:
            old = ServiceTicket.objects.get(pk=instance.pk)
            instance._old_status = old.status
            instance._old_priority = old.priority
            instance._old_agent = old.agent_id
        except ServiceTicket.DoesNotExist:
            instance._old_status = None
            instance._old_priority = None
            instance._old_agent = None
    else:
        instance._old_status = None
        instance._old_priority = None
        instance._old_agent = None


@receiver(post_save, sender=ServiceTicket)
def handle_ticket_save(sender, instance, created, **kwargs):
    """Handle ticket creation and updates for notifications."""
    try:
        from notifications.services import (
            notify_ticket_created, notify_ticket_assigned, notify_status_changed
        )

        if created:
            notify_ticket_created(instance)
        else:
            old_status = getattr(instance, '_old_status', None)
            old_agent = getattr(instance, '_old_agent', None)

            # Notify on status change
            if old_status and old_status != instance.status:
                notify_status_changed(instance, old_status, instance.status, instance.requester)

            # Notify on agent assignment
            if instance.agent_id and instance.agent_id != old_agent:
                notify_ticket_assigned(instance, instance.agent)
    except Exception:
        pass  # Don't break ticket operations if notification fails


@receiver(post_save, sender=TicketResponse)
def handle_response_save(sender, instance, created, **kwargs):
    """Notify participants when a new message is posted."""
    if created:
        try:
            from notifications.services import notify_new_message
            notify_new_message(instance.ticket, instance.responder)
        except Exception:
            pass


def _sync_config_to_file(**kwargs):
    """Write DB state back to org_config.py when teams or departments change."""
    try:
        from org_config_sync import write_config_from_db
        write_config_from_db()
    except Exception:
        pass


# Team changes → write back to org_config.py
def _connect_team_signals():
    """Connect signals for Team model to sync org_config.py."""
    from teams.models import Team
    post_save.connect(_sync_config_to_file, sender=Team)
    post_delete.connect(_sync_config_to_file, sender=Team)


def _connect_department_signals():
    """Deferred connection for Department signals to avoid circular imports."""
    from teams.models import Department
    post_save.connect(_sync_config_to_file, sender=Department)
    post_delete.connect(_sync_config_to_file, sender=Department)


# Use AppConfig.ready() timing — this file is imported from ready()
# so Team and Department models are available at this point
try:
    _connect_team_signals()
    _connect_department_signals()
except Exception:
    pass
