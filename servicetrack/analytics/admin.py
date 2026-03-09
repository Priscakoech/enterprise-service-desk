from django.contrib import admin
from .models import Report, TicketStatistic, AgentPerformance, SLAMetric


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['title', 'created_at']


@admin.register(TicketStatistic)
class TicketStatisticAdmin(admin.ModelAdmin):
    list_display = ['date', 'total_tickets', 'open_tickets', 'closed_tickets']


@admin.register(AgentPerformance)
class AgentPerformanceAdmin(admin.ModelAdmin):
    list_display = ['agent', 'tickets_resolved', 'average_resolution_time']


@admin.register(SLAMetric)
class SLAMetricAdmin(admin.ModelAdmin):
    list_display = ['name', 'target_time', 'actual_time']
