from .models import Notification


def notify_ticket_created(ticket):
    """Notify assigned agent and department manager when a ticket is created."""
    recipients = []
    if ticket.agent:
        recipients.append(ticket.agent)
    if ticket.team and ticket.team.department and ticket.team.department.manager:
        manager = ticket.team.department.manager
        if manager not in recipients:
            recipients.append(manager)

    for recipient in recipients:
        Notification.objects.create(
            recipient=recipient,
            title=f'New ticket: {ticket.title}',
            description=f'Ticket #{ticket.id} has been created by {ticket.requester.username}',
            notification_type='ticket_created',
            reference_type='ticket',
            reference_id=ticket.id,
        )


def notify_ticket_assigned(ticket, agent):
    """Notify the agent when assigned to a ticket."""
    Notification.objects.create(
        recipient=agent,
        title=f'Ticket assigned: {ticket.title}',
        description=f'You have been assigned to ticket #{ticket.id}',
        notification_type='ticket_assigned',
        reference_type='ticket',
        reference_id=ticket.id,
    )


def notify_new_message(ticket, sender):
    """Notify ticket participants (except sender) about a new message."""
    recipients = set()
    if ticket.requester and ticket.requester != sender:
        recipients.add(ticket.requester)
    if ticket.agent and ticket.agent != sender:
        recipients.add(ticket.agent)

    for recipient in recipients:
        Notification.objects.create(
            recipient=recipient,
            title=f'New message on: {ticket.title}',
            description=f'{sender.username} sent a message on ticket #{ticket.id}',
            notification_type='new_message',
            reference_type='ticket',
            reference_id=ticket.id,
        )


def notify_status_changed(ticket, old_status, new_status, changed_by):
    """Notify relevant parties when ticket status changes."""
    recipients = set()
    if ticket.requester and ticket.requester != changed_by:
        recipients.add(ticket.requester)
    if ticket.agent and ticket.agent != changed_by:
        recipients.add(ticket.agent)

    for recipient in recipients:
        Notification.objects.create(
            recipient=recipient,
            title=f'Status changed: {ticket.title}',
            description=f'Ticket #{ticket.id} status changed from {old_status} to {new_status}',
            notification_type='status_changed',
            reference_type='ticket',
            reference_id=ticket.id,
        )


def notify_sla_breach(sla_instance):
    """Notify agent and manager when SLA is breached."""
    ticket = sla_instance.ticket
    recipients = []
    if ticket.agent:
        recipients.append(ticket.agent)
    if ticket.team and ticket.team.department and ticket.team.department.manager:
        manager = ticket.team.department.manager
        if manager not in recipients:
            recipients.append(manager)

    for recipient in recipients:
        Notification.objects.create(
            recipient=recipient,
            title=f'SLA Breached: {ticket.title}',
            description=f'SLA metric {sla_instance.metric} has been breached on ticket #{ticket.id}',
            notification_type='sla_breach',
            reference_type='ticket',
            reference_id=ticket.id,
        )


def notify_sla_warning(sla_instance):
    """Notify agent when SLA is approaching breach (75% of target time elapsed)."""
    ticket = sla_instance.ticket
    if ticket.agent:
        Notification.objects.create(
            recipient=ticket.agent,
            title=f'SLA Warning: {ticket.title}',
            description=f'SLA metric {sla_instance.metric} is approaching breach on ticket #{ticket.id}',
            notification_type='sla_warning',
            reference_type='ticket',
            reference_id=ticket.id,
        )
