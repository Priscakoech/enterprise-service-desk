"""
SLA Background Worker
Runs as a persistent background process to:
1. Check for SLA breaches (active instances past due)
2. Re-evaluate SLA policies for unresolved tickets when new policies are created
3. Auto-assign unassigned tickets to available agents
4. Send SLA warning notifications when approaching breach

Usage: python manage.py sla_worker
"""
import time
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Count, Q

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Run the SLA background worker for breach detection and auto-assignment'

    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=60,
            help='Check interval in seconds (default: 60)',
        )
        parser.add_argument(
            '--once',
            action='store_true',
            help='Run once and exit (useful for cron)',
        )

    def handle(self, *args, **options):
        interval = options['interval']
        run_once = options['once']

        self.stdout.write(self.style.SUCCESS(
            f'SLA Worker started (interval: {interval}s, once: {run_once})'
        ))

        while True:
            try:
                self._check_breaches()
                self._check_warnings()
                self._auto_assign_tickets()
                self._check_new_policies()
            except Exception as e:
                logger.error(f'SLA Worker error: {e}', exc_info=True)
                self.stderr.write(self.style.ERROR(f'Error: {e}'))

            if run_once:
                break

            time.sleep(interval)

    def _check_breaches(self):
        """Find and mark active SLA instances that have passed their due date."""
        from servicedesk.models import TicketSLAInstance
        from servicedesk.sla_engine import breach_instance, log_sla_event
        from notifications.services import notify_sla_breach

        now = timezone.now()
        overdue = TicketSLAInstance.objects.filter(
            state='active',
            due_at__lte=now,
            due_at__isnull=False,
        ).select_related('ticket', 'policy')

        count = 0
        for instance in overdue:
            breach_instance(instance, now=now)
            log_sla_event(
                instance.ticket, instance, 'breach_detected',
                old_state='active', new_state='breached',
                details={'detected_by': 'sla_worker'}
            )
            try:
                notify_sla_breach(instance)
            except Exception:
                pass
            count += 1

        if count:
            self.stdout.write(f'  Breached {count} SLA instance(s)')

    def _check_warnings(self):
        """Send warnings for SLA instances approaching breach (75% of target time elapsed)."""
        from servicedesk.models import TicketSLAInstance
        from servicedesk.sla_engine import calculate_business_minutes, _get_instance_schedule
        from notifications.services import notify_sla_warning

        now = timezone.now()
        active = TicketSLAInstance.objects.filter(
            state='active',
            due_at__isnull=False,
        ).select_related('ticket', 'policy', 'policy__schedule')

        for instance in active:
            if instance.target_minutes <= 0:
                continue

            try:
                schedule = _get_instance_schedule(instance)
                elapsed = calculate_business_minutes(instance.started_at, now, schedule)
                threshold = instance.target_minutes * 0.75

                if elapsed >= threshold:
                    # Check if we already warned (look at audit log)
                    from servicedesk.models import SLAAuditLog
                    already_warned = SLAAuditLog.objects.filter(
                        sla_instance=instance,
                        event_type='sla_warning_sent',
                    ).exists()

                    if not already_warned:
                        notify_sla_warning(instance)
                        SLAAuditLog.objects.create(
                            ticket=instance.ticket,
                            sla_instance=instance,
                            event_type='sla_warning_sent',
                            details={'elapsed_minutes': elapsed, 'threshold_minutes': threshold},
                        )
            except Exception:
                pass

    def _auto_assign_tickets(self):
        """Find unassigned tickets and assign them to available agents."""
        from servicedesk.models import ServiceTicket
        from servicedesk.views import auto_assign_agent

        unassigned = ServiceTicket.objects.filter(
            agent__isnull=True,
            status__in=['new', 'open'],
        ).select_related('team', 'team__department')

        count = 0
        for ticket in unassigned:
            agent = auto_assign_agent(ticket.team)
            if agent:
                ticket.agent = agent
                ticket.save(update_fields=['agent'])
                try:
                    from notifications.services import notify_ticket_assigned
                    notify_ticket_assigned(ticket, agent)
                except Exception:
                    pass
                count += 1

        if count:
            self.stdout.write(f'  Auto-assigned {count} ticket(s)')

    def _check_new_policies(self):
        """Re-evaluate SLA for tickets that don't have SLA instances yet."""
        from servicedesk.models import ServiceTicket, TicketSLAInstance
        from servicedesk.sla_engine import on_ticket_created

        # Find open tickets without any SLA instances
        tickets_without_sla = ServiceTicket.objects.filter(
            status__in=['new', 'open', 'pending', 'on_hold'],
        ).exclude(
            id__in=TicketSLAInstance.objects.values_list('ticket_id', flat=True)
        )

        count = 0
        for ticket in tickets_without_sla:
            try:
                on_ticket_created(ticket)
                count += 1
            except Exception:
                pass

        if count:
            self.stdout.write(f'  Applied SLA to {count} ticket(s)')
