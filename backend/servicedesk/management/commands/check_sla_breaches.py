"""
Management command to manually check for SLA breaches.

Usage:
    python manage.py check_sla_breaches
    python manage.py check_sla_breaches --ticket-id 123
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from servicedesk.models import ServiceTicket, TicketSLAInstance


class Command(BaseCommand):
    help = 'Manually check for SLA breaches'

    def add_arguments(self, parser):
        parser.add_argument(
            '--ticket-id',
            type=int,
            help='Check breaches for a specific ticket ID',
        )

    def handle(self, *args, **options):
        from servicedesk.sla_engine import check_breaches_for_ticket, check_all_active_breaches

        self.stdout.write(self.style.SUCCESS('\n🚨 Manual SLA Breach Check\n'))
        self.stdout.write('=' * 70)

        ticket_id = options.get('ticket_id')
        now = timezone.now()

        if ticket_id:
            # Check specific ticket
            try:
                ticket = ServiceTicket.objects.get(pk=ticket_id)
                self.stdout.write(self.style.WARNING(f'\n🎫 Checking ticket #{ticket_id}: {ticket.title}'))

                # Show current SLA instances
                instances = TicketSLAInstance.objects.filter(ticket=ticket)
                self.stdout.write(f'\n📊 Current SLA instances for ticket #{ticket_id}:')

                for instance in instances:
                    overdue = ""
                    if instance.state == 'active' and instance.due_at and instance.due_at <= now:
                        overdue = " ⚠️ OVERDUE"
                    elif instance.state == 'breached':
                        overdue = " 🚨 BREACHED"
                    elif instance.state == 'fulfilled':
                        overdue = " ✅ FULFILLED"

                    self.stdout.write(f'   - {instance.metric} ({instance.state}): due {instance.due_at}{overdue}')

                # Run breach check
                self.stdout.write(self.style.WARNING('\n🔍 Running breach check...'))
                breached_count = check_breaches_for_ticket(ticket)

                if breached_count > 0:
                    self.stdout.write(self.style.ERROR(f'\n🚨 Found and breached {breached_count} overdue instance(s)!'))
                else:
                    self.stdout.write(self.style.SUCCESS(f'\n✅ No breaches found for ticket #{ticket_id}'))

                # Show updated instances
                updated_instances = TicketSLAInstance.objects.filter(ticket=ticket)
                if updated_instances.count() != instances.count() or breached_count > 0:
                    self.stdout.write(f'\n📊 Updated SLA instances:')
                    for instance in updated_instances:
                        status_icon = {
                            'active': '🟡',
                            'paused': '⏸️',
                            'fulfilled': '✅',
                            'breached': '🚨'
                        }.get(instance.state, '❓')

                        self.stdout.write(f'   {status_icon} {instance.metric} ({instance.state})')

            except ServiceTicket.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'\n❌ Ticket #{ticket_id} not found!'))

        else:
            # Check all tickets
            self.stdout.write(self.style.WARNING('\n🔍 Checking ALL active SLA instances for breaches...'))

            # Show current overdue count
            overdue_count = TicketSLAInstance.objects.filter(
                state='active',
                due_at__lte=now,
                due_at__isnull=False,
            ).count()

            self.stdout.write(f'   Found {overdue_count} overdue instances')

            # Run global breach check
            breached_count = check_all_active_breaches()

            if breached_count > 0:
                self.stdout.write(self.style.ERROR(f'\n🚨 BREACHED {breached_count} overdue SLA instance(s)!'))

                # Show recently breached instances
                recent_breaches = TicketSLAInstance.objects.filter(
                    state='breached',
                    breached_at__gte=now - timezone.timedelta(minutes=5)  # Last 5 minutes
                ).select_related('ticket')[:10]

                if recent_breaches:
                    self.stdout.write(f'\n🔍 Recently breached instances:')
                    for breach in recent_breaches:
                        self.stdout.write(f'   🚨 Ticket #{breach.ticket.id}: {breach.metric} (due: {breach.due_at})')
            else:
                self.stdout.write(self.style.SUCCESS(f'\n✅ No SLA breaches found'))

            # Show current SLA status summary
            total = TicketSLAInstance.objects.count()
            breached = TicketSLAInstance.objects.filter(state='breached').count()
            active = TicketSLAInstance.objects.filter(state='active').count()
            fulfilled = TicketSLAInstance.objects.filter(state='fulfilled').count()

            self.stdout.write(f'\n📈 SLA Summary:')
            self.stdout.write(f'   Total instances: {total}')
            self.stdout.write(f'   Active: {active}')
            self.stdout.write(f'   Fulfilled: {fulfilled}')
            self.stdout.write(f'   Breached: {breached}')
            if total > 0:
                compliance_rate = round((fulfilled / total * 100), 1)
                breach_rate = round((breached / total * 100), 1)
                self.stdout.write(f'   Compliance rate: {compliance_rate}%')
                self.stdout.write(f'   Breach rate: {breach_rate}%')

        self.stdout.write('\n' + '=' * 70 + '\n')