from rest_framework import serializers
from .models import Category, SLA, ServiceTicket, TicketResponse, Attachment


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description']


class SLASerializer(serializers.ModelSerializer):
    class Meta:
        model = SLA
        fields = ['id', 'name', 'target_resolution_time', 'created_at']


class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = ['id', 'file', 'uploaded_at']


class TicketResponseSerializer(serializers.ModelSerializer):
    responder_name = serializers.ReadOnlyField(source='responder.username')

    class Meta:
        model = TicketResponse
        fields = ['id', 'ticket', 'responder', 'responder_name', 'message', 'created_at']


class ServiceTicketSerializer(serializers.ModelSerializer):
    requester_name = serializers.ReadOnlyField(source='requester.username')
    agent_name = serializers.ReadOnlyField(source='agent.username')
    responses = TicketResponseSerializer(many=True, read_only=True)
    attachments = AttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = ServiceTicket
        fields = [
            'id', 'title', 'description',
            'status', 'priority', 'category',
            'requester', 'requester_name',
            'agent', 'agent_name',
            'created_at', 'updated_at',
            'responses', 'attachments',
        ]