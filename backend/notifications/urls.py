from django.urls import path
from .views import (
    NotificationListView,
    NotificationDetailView,
    MarkNotificationReadView,
    MarkAllReadView,
    UnreadCountView,
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
    path('mark-all-read/', MarkAllReadView.as_view(), name='mark-all-read'),
    path('unread-count/', UnreadCountView.as_view(), name='unread-count'),

    # Alerts
    path('alerts/', AlertListView.as_view(), name='alert-list'),
    path('alerts/<int:pk>/', AlertDetailView.as_view(), name='alert-detail'),

    # Email Triggers
    path('email-triggers/', EmailTriggerListView.as_view(), name='email-trigger-list'),
    path('email-triggers/<int:pk>/', EmailTriggerDetailView.as_view(), name='email-trigger-detail'),
]
