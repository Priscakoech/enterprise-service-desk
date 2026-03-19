from django.urls import path
from .views import (
    CategoryListView,
    CategoryDetailView,
    SLAListView,
    SLADetailView,
    ServiceTicketListView,
    ServiceTicketDetailView,
    TicketResponseListView,
    AttachmentListView,
)

urlpatterns = [
    # Categories
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('categories/<int:pk>/', CategoryDetailView.as_view(), name='category-detail'),

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
]