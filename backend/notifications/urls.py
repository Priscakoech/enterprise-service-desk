from django.urls import path
from .views import (
    NotificationListView,
    NotificationDetailView,
    MarkNotificationReadView,
    AlertListView,
    AlertDetailView,
    EmailTriggerListView,
    EmailTriggerDetailView,
)

urlpatterns = [
    # Notifications
    path('', NotificationListView.as_view(), name='notification-list'),
    path('<int:pk>/', NotificationDetailView.as_view(), name='notification-detail'),
    path('<int:pk>/mark-read/', MarkNotificationReadView.as_view(), name='notification-mark-read'),

    # Alerts
    path('alerts/', AlertListView.as_view(), name='alert-list'),
    path('alerts/<int:pk>/', AlertDetailView.as_view(), name='alert-detail'),

    # Email Triggers
    path('email-triggers/', EmailTriggerListView.as_view(), name='email-trigger-list'),
    path('email-triggers/<int:pk>/', EmailTriggerDetailView.as_view(), name='email-trigger-detail'),
]