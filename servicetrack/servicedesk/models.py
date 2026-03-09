from django.db import models

#models for the service ticket, ticket response, attachments,SLA and category
class ServiceTicket(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    requester = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='requested_tickets')
    agent = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets')
    category = models.CharField(max_length=100)
    priority = models.CharField(max_length=20)
    status = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    
class TicketResponse(models.Model):
    ticket = models.ForeignKey(ServiceTicket, on_delete=models.CASCADE, related_name='responses')
    responder = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Response by {self.responder.username} on {self.created_at}"
    
class Attachment(models.Model):
    ticket = models.ForeignKey(ServiceTicket, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='attachments/')
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

    def __str__(self):
        return self.name

