from django.db import models
from django.contrib.auth.models import AbstractUser
import hashlib, hmac, struct, time, secrets, string


class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'System Administrator'),
        ('requester', 'Requester'),
        ('agent', 'Agent'),
        ('manager', 'Manager'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='requester')
    profile_picture_url = models.URLField(max_length=500, blank=True, default='', help_text='Cloudinary URL for profile picture')
    team = models.ForeignKey(
        'teams.Team',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    department = models.ForeignKey(
        'teams.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='staff',
    )
    is_blacklisted = models.BooleanField(default=False)
    must_change_password = models.BooleanField(default=False, help_text='Force password change on next login')
    account_status = models.CharField(max_length=20, choices=[
        ('active', 'Active'),
        ('blacklisted', 'Blacklisted'),
        ('deactivated', 'Deactivated'),
    ], default='active')


class SignupSecret(models.Model):
    """Singleton that stores the secret used to generate time-based signup codes."""
    secret = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    # In-memory cache to avoid DB hit on every request
    _cached_secret = None

    class Meta:
        verbose_name = 'Signup Secret'

    @classmethod
    def get_secret(cls):
        if cls._cached_secret:
            return cls._cached_secret
        obj = cls.objects.first()
        if not obj:
            obj = cls.objects.create(secret=secrets.token_hex(32))
        cls._cached_secret = obj.secret
        return cls._cached_secret

    ROTATION_SECONDS = 600  # 10 minutes

    @staticmethod
    def generate_code(secret_key):
        """Generate an 8-character alphanumeric code that rotates every 10 minutes."""
        time_step = int(time.time()) // SignupSecret.ROTATION_SECONDS
        msg = struct.pack('>Q', time_step)
        h = hmac.new(secret_key.encode(), msg, hashlib.sha256).hexdigest()
        charset = string.ascii_uppercase + string.digits
        code = ''.join(charset[int(h[i:i+2], 16) % len(charset)] for i in range(0, 16, 2))
        return code

    @classmethod
    def get_current_code(cls):
        return cls.generate_code(cls.get_secret())

    @classmethod
    def verify_code(cls, code):
        return code == cls.get_current_code()

    @staticmethod
    def seconds_remaining():
        return SignupSecret.ROTATION_SECONDS - (int(time.time()) % SignupSecret.ROTATION_SECONDS)
