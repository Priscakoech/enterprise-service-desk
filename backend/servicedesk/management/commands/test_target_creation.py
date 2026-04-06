"""
Management command to test SLA target creation.

Usage:
    python manage.py test_target_creation --policy-id 3 --metric first_reply_time --priority urgent --minutes 30
"""
from django.core.management.base import BaseCommand
from servicedesk.models import SLAPolicy, SLATarget


class Command(BaseCommand):
    help = 'Test SLA target creation'

    def add_arguments(self, parser):
        parser.add_argument('--policy-id', type=int, required=True, help='Policy ID')
        parser.add_argument('--metric', type=str, required=True, help='Metric name')
        parser.add_argument('--priority', type=str, required=True, help='Priority')
        parser.add_argument('--minutes', type=int, required=True, help='Target minutes')

    def handle(self, *args, **options):
        policy_id = options['policy_id']
        metric = options['metric']
        priority = options['priority']
        minutes = options['minutes']

        self.stdout.write(self.style.SUCCESS('\n🧪 Testing SLA Target Creation\n'))
        self.stdout.write('=' * 70)

        # Check if policy exists
        try:
            policy = SLAPolicy.objects.get(pk=policy_id)
            self.stdout.write(self.style.SUCCESS(f'\n✅ Found policy: {policy.name} (ID: {policy.id})'))
            self.stdout.write(f'   Active: {policy.is_active}')
            self.stdout.write(f'   Team: {policy.team.name if policy.team else "None"}')
            self.stdout.write(f'   Department: {policy.department.name if policy.department else "None"}')
        except SLAPolicy.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'\n❌ Policy {policy_id} not found!'))
            return

        # Check if target already exists
        existing = SLATarget.objects.filter(
            policy=policy,
            metric=metric,
            priority=priority,
        ).first()

        if existing:
            self.stdout.write(self.style.WARNING(f'\n⚠️  Target already exists:'))
            self.stdout.write(f'   Metric: {existing.metric}')
            self.stdout.write(f'   Priority: {existing.priority}')
            self.stdout.write(f'   Current minutes: {existing.target_minutes}')

            confirm = input(f'\n❓ Update to {minutes} minutes? (yes/no): ')
            if confirm.lower() in ('yes', 'y'):
                existing.target_minutes = minutes
                existing.save()
                self.stdout.write(self.style.SUCCESS(f'\n✅ Updated target to {minutes} minutes'))
            else:
                self.stdout.write(self.style.ERROR('\n❌ Cancelled'))
            return

        # Create the target
        try:
            target = SLATarget.objects.create(
                policy=policy,
                metric=metric,
                priority=priority,
                target_minutes=minutes,
            )
            self.stdout.write(self.style.SUCCESS(f'\n✅ Created target successfully!'))
            self.stdout.write(f'   ID: {target.id}')
            self.stdout.write(f'   Policy: {target.policy.name}')
            self.stdout.write(f'   Metric: {target.metric} ({target.get_metric_display()})')
            self.stdout.write(f'   Priority: {target.priority} ({target.get_priority_display()})')
            self.stdout.write(f'   Target: {target.target_minutes} minutes')

            # Verify it was saved
            count = policy.targets.count()
            self.stdout.write(self.style.SUCCESS(f'\n✅ Policy now has {count} target(s)'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Failed to create target: {str(e)}'))
            import traceback
            self.stdout.write(traceback.format_exc())

        self.stdout.write('\n' + '=' * 70 + '\n')
