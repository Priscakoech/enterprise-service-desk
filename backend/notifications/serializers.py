from rest_framework import serializers
from .models import Notifications, Alerts, EmailTriggers


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notifications
        fields = ['id', 'title', 'description', 'created_at', 'is_read']


class AlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alerts
        fields = ['id', 'title', 'description', 'created_at', 'is_active']


class EmailTriggerSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailTriggers
        fields = ['id', 'name', 'subject', 'body', 'created_at']