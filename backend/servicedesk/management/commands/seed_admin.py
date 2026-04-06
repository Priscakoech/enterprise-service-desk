"""
Create the default admin superuser.

Usage:
    python manage.py seed_admin

Credentials are read from environment variables (recommended for production):
    ADMIN_USERNAME  (default: admin)
    ADMIN_PASSWORD  (default: admin)
    ADMIN_EMAIL     (default: admin@servicedesk.local)

This command is IDEMPOTENT — it will NOT create duplicates.
If the admin user already exists, it is silently skipped.
This makes it safe to run on every deploy.
"""

import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Create the default admin superuser (idempotent — safe to run on every deploy)'

    def handle(self, *args, **options):
        username = os.environ.get('ADMIN_USERNAME', 'admin')
        password = os.environ.get('ADMIN_PASSWORD', 'admin')
        email = os.environ.get('ADMIN_EMAIL', 'admin@servicedesk.local')

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(
                f'Admin user "{username}" already exists — skipping.'
            ))
            return

        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            role='admin',
        )
        user.must_change_password = True
        user.save(update_fields=['must_change_password'])
        self.stdout.write(self.style.SUCCESS(
            f'Created admin superuser: {username} (password change required on first login)'
        ))
