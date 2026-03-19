"""
Create the default admin superuser.

Usage:
    python manage.py seed_admin

Default credentials:
    Username: admin
    Password: admin
    Email:    admin@servicedesk.local
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

DEFAULT_USERNAME = 'admin'
DEFAULT_PASSWORD = 'admin'
DEFAULT_EMAIL = 'admin@servicedesk.local'


class Command(BaseCommand):
    help = 'Create the default admin superuser (admin / admin)'

    def handle(self, *args, **options):
        if User.objects.filter(username=DEFAULT_USERNAME).exists():
            self.stdout.write(self.style.WARNING(
                f'Admin user "{DEFAULT_USERNAME}" already exists — skipping. '
                f'Delete the user from the database first if you need to re-seed.'
            ))
            return

        user = User.objects.create_superuser(
            username=DEFAULT_USERNAME,
            email=DEFAULT_EMAIL,
            password=DEFAULT_PASSWORD,
            role='admin',
        )
        user.must_change_password = True
        user.save(update_fields=['must_change_password'])
        self.stdout.write(self.style.SUCCESS(
            f'Created admin superuser: {DEFAULT_USERNAME} / {DEFAULT_PASSWORD} '
            f'(password change required on first login)'
        ))
