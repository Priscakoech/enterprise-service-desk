from django.contrib import admin
from .models import Notification, Alerts, EmailTriggers


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'recipient', 'notification_type', 'is_read', 'created_at']
    list_filter = ['is_read', 'notification_type']


@admin.register(Alerts)
class AlertAdmin(admin.ModelAdmin):
    list_display = ['title', 'is_active', 'created_at']
    list_filter = ['is_active']


@admin.register(EmailTriggers)
class EmailTriggerAdmin(admin.ModelAdmin):
    list_display = ['name', 'subject', 'created_at']
