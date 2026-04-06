"""
Test the SLA dashboard API endpoint directly.

Usage:
    python manage.py test_sla_dashboard
"""
from django.core.management.base import BaseCommand
import json


class Command(BaseCommand):
    help = 'Test SLA dashboard API endpoint'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\nTesting SLA Dashboard API\n'))
        self.stdout.write('=' * 70)

        try:
            from servicedesk.views import SLADashboardView
            from django.test import RequestFactory
            from accounts.models import CustomUser
            from django.contrib.auth import get_user_model

            # Create a test request
            factory = RequestFactory()
            request = factory.get('/servicedesk/sla-dashboard/')

            # Get or create a test user
            User = get_user_model()
            try:
                user = User.objects.filter(is_staff=True).first()
                if not user:
                    user = User.objects.create_user(
                        username='test_admin',
                        email='test@example.com',
                        role='admin'
                    )
            except Exception:
                # Fallback for testing
                class MockUser:
                    role = 'admin'
                    is_authenticated = True
                user = MockUser()

            request.user = user

            # Test the view
            self.stdout.write('Calling SLADashboardView...')
            view = SLADashboardView()
            response = view.get(request)

            self.stdout.write(f'Response Status: {response.status_code}')

            if response.status_code == 200:
                data = response.data
                self.stdout.write('Dashboard Data:')
                self.stdout.write(json.dumps(data, indent=2, default=str))
            else:
                self.stdout.write(self.style.ERROR(f'Error Response: {response.data}'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Exception occurred: {str(e)}'))
            import traceback
            self.stdout.write(traceback.format_exc())

        self.stdout.write('\n' + '=' * 70 + '\n')