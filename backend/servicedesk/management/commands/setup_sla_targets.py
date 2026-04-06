"""
Management command to quickly set up SLA targets for a policy.

Usage:
    python manage.py setup_sla_targets --policy-id 3
    python manage.py setup_sla_targets --policy-name "IT SLA Policy"
"""
from django.core.management.base import BaseCommand
from servicedesk.models import SLAPolicy, SLATarget


class Command(BaseCommand):
    help = 'Set up default SLA targets for a policy'

    def add_arguments(self, parser):
        parser.add_argument(
            '--policy-id',
            type=int,
            help='SLA Policy ID',
        )
        parser.add_argument(
            '--policy-name',
            type=str,
            help='SLA Policy name',
        )
        parser.add_argument(
            '--quick',
            action='store_true',
            help='Use quick preset values without prompting',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n🎯 SLA Targets Setup Tool\n'))
        self.stdout.write('=' * 70)

        # Find the policy
        policy = None
        if options.get('policy_id'):
            try:
                policy = SLAPolicy.objects.get(pk=options['policy_id'])
            except SLAPolicy.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'\n❌ Policy ID {options["policy_id"]} not found!'))
                return
        elif options.get('policy_name'):
            try:
                policy = SLAPolicy.objects.get(name=options['policy_name'])
            except SLAPolicy.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'\n❌ Policy "{options["policy_name"]}" not found!'))
                return
            except SLAPolicy.MultipleObjectsReturned:
                self.stdout.write(self.style.ERROR(f'\n❌ Multiple policies with name "{options["policy_name"]}" found!'))
                return
        else:
            # List all policies
            self.stdout.write(self.style.WARNING('\nAvailable SLA Policies:'))
            policies = SLAPolicy.objects.all()
            for p in policies:
                target_count = p.targets.count()
                self.stdout.write(f'  {p.id}: {p.name} ({target_count} targets)')

            self.stdout.write(self.style.ERROR('\n❌ Please specify --policy-id or --policy-name'))
            return

        self.stdout.write(self.style.SUCCESS(f'\n✅ Found policy: {policy.name} (ID: {policy.id})'))
        self.stdout.write(f'   Current targets: {policy.targets.count()}')

        # Define default target values (in minutes)
        default_targets = {
            'first_reply_time': {
                'urgent': 15,
                'high': 30,
                'normal': 60,
                'low': 120,
            },
            'total_resolution_time': {
                'urgent': 120,
                'high': 240,
                'normal': 480,
                'low': 960,
            },
            'requester_wait_time': {
                'urgent': 60,
                'high': 120,
                'normal': 240,
                'low': 480,
            },
            'agent_work_time': {
                'urgent': 60,
                'high': 120,
                'normal': 240,
                'low': 480,
            },
        }

        if not options.get('quick'):
            self.stdout.write(self.style.WARNING('\n📝 This will create the following targets:'))
            for metric, priorities in default_targets.items():
                self.stdout.write(f'\n  {metric}:')
                for priority, minutes in priorities.items():
                    self.stdout.write(f'    - {priority}: {minutes} minutes')

            confirm = input('\n❓ Continue? (yes/no): ')
            if confirm.lower() not in ('yes', 'y'):
                self.stdout.write(self.style.ERROR('\n❌ Cancelled'))
                return

        self.stdout.write(self.style.WARNING('\n🔧 Creating targets...'))
        created_count = 0
        skipped_count = 0

        for metric, priorities in default_targets.items():
            for priority, minutes in priorities.items():
                # Check if target already exists
                existing = SLATarget.objects.filter(
                    policy=policy,
                    metric=metric,
                    priority=priority,
                ).first()

                if existing:
                    self.stdout.write(f'   ⏭️  Skipped {metric} / {priority} (already exists)')
                    skipped_count += 1
                else:
                    SLATarget.objects.create(
                        policy=policy,
                        metric=metric,
                        priority=priority,
                        target_minutes=minutes,
                    )
                    self.stdout.write(self.style.SUCCESS(f'   ✅ Created {metric} / {priority}: {minutes} min'))
                    created_count += 1

        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(self.style.SUCCESS(f'\n✅ Complete! Created {created_count} targets, skipped {skipped_count}'))
        self.stdout.write(f'   Total targets for "{policy.name}": {policy.targets.count()}\n')
