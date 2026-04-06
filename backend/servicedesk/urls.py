from django.urls import path
from .views import (
    SLAListView,
    SLADetailView,
    ServiceTicketListView,
    ServiceTicketDetailView,
    TicketResponseListView,
    AttachmentListView,
    BusinessScheduleListView,
    BusinessScheduleDetailView,
    SLAPolicyListView,
    SLAPolicyDetailView,
    SLAPolicyReorderView,
    SLAPolicyResetFactoryView,
    SLAEnsureDefaultView,
    SLATargetListView,
    SLATargetDetailView,
    TicketSLAInstanceListView,
    SLAAuditLogListView,
    SLADashboardView,
    SLAAnalyticsDashboardView,
    AutoAssignView,
)

urlpatterns = [
    # SLA
    path('sla/', SLAListView.as_view(), name='sla-list'),
    path('sla/<int:pk>/', SLADetailView.as_view(), name='sla-detail'),

    # Tickets
    path('tickets/', ServiceTicketListView.as_view(), name='ticket-list'),
    path('tickets/<int:pk>/', ServiceTicketDetailView.as_view(), name='ticket-detail'),

    # Ticket Responses (nested under ticket)
    path('tickets/<int:ticket_id>/responses/', TicketResponseListView.as_view(), name='ticket-responses'),

    # Attachments (nested under ticket)
    path('tickets/<int:ticket_id>/attachments/', AttachmentListView.as_view(), name='ticket-attachments'),

    # Business Schedules
    path('business-schedules/', BusinessScheduleListView.as_view(), name='business-schedule-list'),
    path('business-schedules/<int:pk>/', BusinessScheduleDetailView.as_view(), name='business-schedule-detail'),

    # SLA Policies (new engine)
    path('sla-policies/', SLAPolicyListView.as_view(), name='sla-policy-list'),
    path('sla-policies/<int:pk>/', SLAPolicyDetailView.as_view(), name='sla-policy-detail'),
    path('sla-policies/<int:pk>/reset-factory/', SLAPolicyResetFactoryView.as_view(), name='sla-policy-reset-factory'),
    path('sla-policies/reorder/', SLAPolicyReorderView.as_view(), name='sla-policy-reorder'),
    path('sla-policies/ensure-default/', SLAEnsureDefaultView.as_view(), name='sla-policy-ensure-default'),

    # SLA Targets
    path('sla-policies/<int:policy_id>/targets/', SLATargetListView.as_view(), name='sla-target-list'),
    path('sla-targets/<int:pk>/', SLATargetDetailView.as_view(), name='sla-target-detail'),

    # Ticket SLA instances
    path('tickets/<int:ticket_id>/sla/', TicketSLAInstanceListView.as_view(), name='ticket-sla-instances'),
    path('tickets/<int:ticket_id>/sla-audit/', SLAAuditLogListView.as_view(), name='ticket-sla-audit'),

    # SLA Dashboard
    path('sla-dashboard/', SLADashboardView.as_view(), name='sla-dashboard'),

    # SLA Analytics (server-side aggregated, role-scoped)
    path('sla-analytics/', SLAAnalyticsDashboardView.as_view(), name='sla-analytics'),

    # Auto-assign unassigned tickets
    path('auto-assign/', AutoAssignView.as_view(), name='auto-assign'),
]
