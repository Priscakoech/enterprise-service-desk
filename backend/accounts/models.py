from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.
## Custom user model to include role field.
class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'System Administrator'),
        ('requester', 'Requester'),
        ('agent', 'Agent'),
        ('manager', 'Manager'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='requester')
    team = models.ForeignKey(
        'teams.Team',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
   
    
        
        
    
    