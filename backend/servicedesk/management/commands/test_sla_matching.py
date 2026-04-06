"""
Management command to test SLA policy matching for tickets.

Usage:
    python manage.py test_sla_matching
    python manage.py test_sla_matching --ticket-id 123
"""
from django.core.management.base import BaseCommand
from servicedesk.models import ServiceTicket, SLAPolicy
from servicedesk.sla_engine import match_policy


class Command(BaseCommand):
    help = 'Test SLA policy matching for tickets'

    def add_arguments(self, parser):
        parser.add_argument(
            '--ticket-id',
            type=int,
            help='Test SLA matching for a specific ticket ID',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n🔍 SLA Policy Matching Test Tool\n'))
        self.stdout.write('=' * 70)

        # List all active SLA policies
        self.stdout.write(self.style.WARNING('\n📊 Active SLA Policies:'))
        policies = SLAPolicy.objects.filter(is_active=True).select_related('team', 'department')

        if not policies.exists():
            self.stdout.write(self.style.ERROR('   ❌ No active SLA policies found!'))
            return

        for policy in policies:
            self.stdout.write(f'\n   Policy: {policy.name} (ID: {policy.id})')
            self.stdout.write(f'   - Team: {policy.team.name if policy.team else "None"} (ID: {policy.team_id})')
            self.stdout.write(f'   - Department: {policy.department.name if policy.department else "None"} (ID: {policy.department_id})')
            self.stdout.write(f'   - Is Default: {policy.is_default}')
            self.stdout.write(f'   - Is System Default: {policy.is_system_default}')
            self.stdout.write(f'   - Target Count: {policy.targets.count()}')

        # Test specific ticket if provided
        ticket_id = options.get('ticket_id')
        if ticket_id:
            self.stdout.write(self.style.WARNING(f'\n\n🎫 Testing ticket #{ticket_id}:'))
            try:
                ticket = ServiceTicket.objects.select_related(
                    'team', 'team__department'
                ).get(pk=ticket_id)

                self.stdout.write(f'   Title: {ticket.title}')
                self.stdout.write(f'   Team: {ticket.team.name if ticket.team else "None"} (ID: {ticket.team_id})')
                if ticket.team and ticket.team.department:
                    self.stdout.write(f'   Department: {ticket.team.department.name} (ID: {ticket.team.department_id})')
                else:
                    self.stdout.write(f'   Department: None')

                self.stdout.write(self.style.WARNING('\n   Running match_policy()...'))
                matched = match_policy(ticket)

                if matched:
                    self.stdout.write(self.style.SUCCESS(f'\n   ✅ Matched Policy: {matched.name}'))
                else:
                    self.stdout.write(self.style.ERROR('\n   ❌ No policy matched!'))

            except ServiceTicket.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'   ❌ Ticket #{ticket_id} not found!'))
        else:
            # Test all tickets
            self.stdout.write(self.style.WARNING(f'\n\n🎫 Testing all tickets:'))
            tickets = ServiceTicket.objects.select_related(
                'team', 'team__department'
            ).all()[:10]  # Limit to first 10

            if not tickets.exists():
                self.stdout.write(self.style.ERROR('   ❌ No tickets found!'))
                return

            for ticket in tickets:
                self.stdout.write(f'\n   Ticket #{ticket.id}: {ticket.title}')
                self.stdout.write(f'   - Team: {ticket.team.name if ticket.team else "None"}')
                if ticket.team and ticket.team.department:
                    self.stdout.write(f'   - Department: {ticket.team.department.name}')

                matched = match_policy(ticket)
                if matched:
                    self.stdout.write(self.style.SUCCESS(f'   - Matched: {matched.name}'))
                else:
                    self.stdout.write(self.style.ERROR(f'   - Matched: None'))

        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(self.style.SUCCESS('\n✅ Test complete!\n'))
