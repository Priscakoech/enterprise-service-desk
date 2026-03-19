from django.db import models

#Models for In-app notifications,alerts and email triggers
class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('ticket_created', 'Ticket Created'),
        ('ticket_assigned', 'Ticket Assigned'),
        ('ticket_updated', 'Ticket Updated'),
        ('new_message', 'New Message'),
        ('sla_warning', 'SLA Warning'),
        ('sla_breach', 'SLA Breach'),
        ('status_changed', 'Status Changed'),
        ('priority_changed', 'Priority Changed'),
    ]
    recipient = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    description = models.TextField()
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES, default='ticket_updated')
    reference_type = models.CharField(max_length=50, blank=True)
    reference_id = models.IntegerField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} -> {self.recipient.username}"

class Alerts(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

class EmailTriggers(models.Model):
    name = models.CharField(max_length=100)
    subject = models.CharField(max_length=200)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
