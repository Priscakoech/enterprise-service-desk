from django.db import models


class ServiceTicket(models.Model):
    STATUS_CHOICES = [
        ('new', 'New'),
        ('open', 'Open'),
        ('pending', 'Pending'),
        ('on_hold', 'On Hold'),
        ('solved', 'Solved'),
        ('closed', 'Closed'),
    ]
    PRIORITY_CHOICES = [
        ('urgent', 'Urgent'),
        ('high', 'High'),
        ('normal', 'Normal'),
        ('low', 'Low'),
    ]

    title = models.CharField(max_length=200)
    reference_id = models.CharField(max_length=30, unique=True, blank=True, help_text='Auto-generated e.g. HRTKTREQ001150326')
    description = models.TextField()
    requester = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='requested_tickets')
    agent = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets')
    team = models.ForeignKey('teams.Team', on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class TicketResponse(models.Model):
    ticket = models.ForeignKey(ServiceTicket, on_delete=models.CASCADE, related_name='responses')
    responder = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE)
    message = models.TextField()
    message_type = models.CharField(max_length=20, choices=[('public_reply', 'Public Reply'), ('internal_note', 'Internal Note')], default='public_reply')
    is_from_agent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Response by {self.responder.username} on {self.created_at}"


class Attachment(models.Model):
    ticket = models.ForeignKey(ServiceTicket, on_delete=models.CASCADE, related_name='attachments')
    response = models.ForeignKey('TicketResponse', on_delete=models.SET_NULL, null=True, blank=True, related_name='attachments')
    file = models.FileField(upload_to='attachments/')
    file_type = models.CharField(max_length=20, blank=True)
    original_filename = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attachment for {self.ticket.title}"


class SLA(models.Model):
    name = models.CharField(max_length=100)
    target_resolution_time = models.DurationField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    department = models.ForeignKey(
        'teams.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='categories',
    )

    class Meta:
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name


class BusinessSchedule(models.Model):
    name = models.CharField(max_length=100)
    timezone = models.CharField(max_length=50, default='UTC')
    hours = models.JSONField(default=list, help_text='Business hours per day')
    holidays = models.JSONField(default=list, help_text='Holiday dates as ISO strings')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class SLAPolicy(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    position = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False, help_text='Default fallback policy when no specific match')
    is_system_default = models.BooleanField(default=False, help_text='System factory default policy from org_config.py')
    team = models.ForeignKey('teams.Team', on_delete=models.SET_NULL, null=True, blank=True, related_name='sla_policies', help_text='When set, this policy applies to tickets in this team')
    department = models.ForeignKey('teams.Department', on_delete=models.SET_NULL, null=True, blank=True, related_name='sla_policies', help_text='When set, this policy applies to tickets in this department')
    schedule = models.ForeignKey(BusinessSchedule, on_delete=models.SET_NULL, null=True, blank=True)
    conditions = models.JSONField(default=dict, help_text='Policy matching conditions')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['position']
        verbose_name_plural = 'SLA Policies'

    def __str__(self):
        return self.name


class SLATarget(models.Model):
    METRIC_CHOICES = [
        ('first_reply_time', 'First Reply Time'),
        ('next_reply_time', 'Next Reply Time'),
        ('pausable_update_time', 'Pausable Update Time'),
        ('requester_wait_time', 'Requester Wait Time'),
        ('agent_work_time', 'Agent Work Time'),
        ('total_resolution_time', 'Total Resolution Time'),
    ]
    policy = models.ForeignKey(SLAPolicy, on_delete=models.CASCADE, related_name='targets')
    metric = models.CharField(max_length=50, choices=METRIC_CHOICES)
    priority = models.CharField(max_length=20, choices=ServiceTicket.PRIORITY_CHOICES)
    target_minutes = models.IntegerField(help_text='Target in business minutes')

    class Meta:
        unique_together = ['policy', 'metric', 'priority']

    def __str__(self):
        return f"{self.policy.name} - {self.get_metric_display()} ({self.get_priority_display()})"


class TicketSLAInstance(models.Model):
    STATE_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('fulfilled', 'Fulfilled'),
        ('breached', 'Breached'),
    ]
    ticket = models.ForeignKey(ServiceTicket, on_delete=models.CASCADE, related_name='sla_instances')
    policy = models.ForeignKey(SLAPolicy, on_delete=models.SET_NULL, null=True)
    metric = models.CharField(max_length=50)
    target_minutes = models.IntegerField()
    started_at = models.DateTimeField()
    due_at = models.DateTimeField(null=True, blank=True)
    achieved_at = models.DateTimeField(null=True, blank=True)
    breached_at = models.DateTimeField(null=True, blank=True)
    paused_at = models.DateTimeField(null=True, blank=True)
    accumulated_pause_minutes = models.IntegerField(default=0)
    active_business_minutes = models.IntegerField(default=0)
    state = models.CharField(max_length=20, choices=STATE_CHOICES, default='active')
    last_event_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"Ticket #{self.ticket_id} - {self.metric} ({self.state})"


class SLAAuditLog(models.Model):
    ticket = models.ForeignKey(ServiceTicket, on_delete=models.CASCADE, related_name='sla_audit_logs')
    sla_instance = models.ForeignKey(TicketSLAInstance, on_delete=models.SET_NULL, null=True, blank=True)
    event_type = models.CharField(max_length=50)
    old_state = models.CharField(max_length=20, blank=True)
    new_state = models.CharField(max_length=20, blank=True)
    details = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"Ticket #{self.ticket_id} - {self.event_type} at {self.timestamp}"
