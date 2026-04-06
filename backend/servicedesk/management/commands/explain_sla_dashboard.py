"""
Management command to show SLA dashboard metrics explanation.

Usage:
    python manage.py explain_sla_dashboard
"""
from django.core.management.base import BaseCommand
from django.db.models import Count, Q, Exists, OuterRef
from django.utils import timezone
from servicedesk.models import ServiceTicket, TicketSLAInstance, SLATarget


class Command(BaseCommand):
    help = 'Explain SLA dashboard metrics to avoid confusion'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n📊 SLA Dashboard Metrics Explanation\n'))
        self.stdout.write('=' * 70)

        now = timezone.now()
        twenty_four_hours_ago = now - timezone.timedelta(hours=24)
        seven_days_ago = now - timezone.timedelta(days=7)

        # OLD WAY (misleading instance counts)
        total_instances = TicketSLAInstance.objects.count()
        breached_instances = TicketSLAInstance.objects.filter(state='breached').count()
        active_instances = TicketSLAInstance.objects.filter(state='active').count()

        self.stdout.write(self.style.WARNING('\n❌ OLD WAY (Misleading Instance Counts):'))
        self.stdout.write(f'   "Total SLA Instances: {total_instances}"')
        self.stdout.write(f'   "Breached Instances: {breached_instances}"')
        self.stdout.write(f'   "Active Instances: {active_instances}"')
        self.stdout.write(self.style.ERROR('\n   ⚠️  PROBLEM: These numbers are confusing because:'))
        self.stdout.write('      • One ticket can have multiple SLA instances')
        self.stdout.write('      • Users think "9 breaches" = 9 tickets in trouble')
        self.stdout.write('      • Actually might be 3 tickets with 3 SLA metrics each')

        # NEW WAY (ticket-focused)
        tickets_with_active_sla = ServiceTicket.objects.filter(
            sla_instances__state__in=['active', 'paused']
        ).distinct().count()

        tickets_with_breaches = ServiceTicket.objects.filter(
            sla_instances__state='breached'
        ).distinct().count()

        tickets_overdue = ServiceTicket.objects.filter(
            sla_instances__state='active',
            sla_instances__due_at__lte=now,
            sla_instances__due_at__isnull=False
        ).distinct().count()

        self.stdout.write(self.style.SUCCESS('\n✅ NEW WAY (Clear Ticket-Focused Metrics):'))
        self.stdout.write(f'   "Tickets Being Tracked: {tickets_with_active_sla}"')
        self.stdout.write(f'   "Tickets with SLA Issues: {tickets_with_breaches}"')
        self.stdout.write(f'   "Tickets at Risk (Overdue): {tickets_overdue}"')
        self.stdout.write(self.style.SUCCESS('\n   ✅ BENEFIT: Much clearer because:'))
        self.stdout.write('      • Shows actual number of tickets affected')
        self.stdout.write('      • Separates current issues from historical data')
        self.stdout.write('      • Provides actionable insights')

        # DETAILED BREAKDOWN
        self.stdout.write(self.style.WARNING('\n🔍 DETAILED BREAKDOWN:'))

        # Show sample tickets with multiple SLA instances
        sample_tickets = ServiceTicket.objects.annotate(
            sla_count=Count('sla_instances')
        ).filter(sla_count__gt=1)[:5]

        if sample_tickets:
            self.stdout.write('\n   Example tickets with multiple SLA instances:')
            for ticket in sample_tickets:
                instances = ticket.sla_instances.all()
                self.stdout.write(f'\n   📋 Ticket #{ticket.id}: "{ticket.title}"')
                for instance in instances:
                    status_icon = {'active': '🟡', 'breached': '🚨', 'fulfilled': '✅', 'paused': '⏸️'}.get(instance.state, '❓')
                    self.stdout.write(f'      {status_icon} {instance.metric} ({instance.state})')

                self.stdout.write(f'      → This ONE ticket contributes {instances.count()} to "instance count"')

        # SLA METRICS EXPLANATION
        self.stdout.write(self.style.WARNING('\n📏 SLA METRICS EXPLAINED:'))
        metric_choices = dict(SLATarget.METRIC_CHOICES)

        for metric_key, metric_label in metric_choices.items():
            active_count = TicketSLAInstance.objects.filter(metric=metric_key, state='active').count()
            breached_count = TicketSLAInstance.objects.filter(metric=metric_key, state='breached').count()

            if active_count > 0 or breached_count > 0:
                self.stdout.write(f'\n   🎯 {metric_label}:')
                self.stdout.write(f'      • Active: {active_count} instances')
                self.stdout.write(f'      • Breached: {breached_count} instances')

        # RECOMMENDATIONS
        self.stdout.write(self.style.SUCCESS('\n💡 DASHBOARD RECOMMENDATIONS:'))
        self.stdout.write('\n   1. Focus on TICKET counts, not instance counts')
        self.stdout.write('   2. Separate current issues from historical data')
        self.stdout.write('   3. Show actionable insights (which tickets need attention)')
        self.stdout.write('   4. Provide context for what numbers mean')
        self.stdout.write('   5. Use time-based filters (last 24h, 7 days, etc.)')

        # PERFORMANCE SUMMARY
        tickets_resolved_7d = ServiceTicket.objects.filter(
            status__in=['solved', 'closed'],
            updated_at__gte=seven_days_ago
        ).count()

        tickets_resolved_on_time = ServiceTicket.objects.filter(
            status__in=['solved', 'closed'],
            updated_at__gte=seven_days_ago
        ).filter(
            Exists(TicketSLAInstance.objects.filter(ticket=OuterRef('pk')))
        ).exclude(
            sla_instances__state='breached'
        ).distinct().count()

        if tickets_resolved_7d > 0:
            compliance_rate = round((tickets_resolved_on_time / tickets_resolved_7d * 100), 1)
            self.stdout.write(self.style.SUCCESS(f'\n📈 RECENT PERFORMANCE (Last 7 Days):'))
            self.stdout.write(f'   • Tickets resolved: {tickets_resolved_7d}')
            self.stdout.write(f'   • Resolved on time: {tickets_resolved_on_time}')
            self.stdout.write(f'   • SLA compliance: {compliance_rate}%')
        else:
            self.stdout.write(f'\n📈 No tickets resolved in the last 7 days')

        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(self.style.SUCCESS('\n✅ The new dashboard format is much clearer!\n'))