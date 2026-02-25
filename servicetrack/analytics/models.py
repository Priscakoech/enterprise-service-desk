from django.db import models

# models for reports, ticket statistics, agent performance and SLA metrics
class Report(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class TicketStatistic(models.Model):
    date = models.DateField()
    total_tickets = models.IntegerField()
    open_tickets = models.IntegerField()
    closed_tickets = models.IntegerField()

    def __str__(self):
        return f"Ticket Statistics for {self.date}"
    
class AgentPerformance(models.Model):
    agent = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE)
    tickets_resolved = models.IntegerField()
    average_resolution_time = models.DurationField()

    def __str__(self):
        return f"Performance of {self.agent.username}"
    
class SLAMetric(models.Model):
    name = models.CharField(max_length=100)
    target_time = models.DurationField()
    actual_time = models.DurationField()

    def __str__(self):
        return self.name


