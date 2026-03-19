from django.urls import path
from .views import (
    ReportListView,
    ReportDetailView,
    TicketStatisticListView,
    TicketStatisticDetailView,
    AgentPerformanceListView,
    AgentPerformanceDetailView,
    SLAMetricListView,
    SLAMetricDetailView,
)

urlpatterns = [
    # Reports
    path('reports/', ReportListView.as_view(), name='report-list'),
    path('reports/<int:pk>/', ReportDetailView.as_view(), name='report-detail'),

    # Ticket Statistics
    path('ticket-statistics/', TicketStatisticListView.as_view(), name='ticket-statistic-list'),
    path('ticket-statistics/<int:pk>/', TicketStatisticDetailView.as_view(), name='ticket-statistic-detail'),

    # Agent Performance
    path('agent-performance/', AgentPerformanceListView.as_view(), name='agent-performance-list'),
    path('agent-performance/<int:pk>/', AgentPerformanceDetailView.as_view(), name='agent-performance-detail'),

    # SLA Metrics
    path('sla-metrics/', SLAMetricListView.as_view(), name='sla-metric-list'),
    path('sla-metrics/<int:pk>/', SLAMetricDetailView.as_view(), name='sla-metric-detail'),
]