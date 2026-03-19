from rest_framework import serializers
from .models import Notification, Alerts, EmailTriggers


class NotificationSerializer(serializers.ModelSerializer):
    recipient_name = serializers.ReadOnlyField(source='recipient.username')

    class Meta:
        model = Notification
        fields = ['id', 'recipient', 'recipient_name', 'title', 'description',
                  'notification_type', 'reference_type', 'reference_id',
                  'is_read', 'created_at']
        read_only_fields = ['recipient']


class AlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alerts
        fields = ['id', 'title', 'description', 'created_at', 'is_active']


class EmailTriggerSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailTriggers
        fields = ['id', 'name', 'subject', 'body', 'created_at']
