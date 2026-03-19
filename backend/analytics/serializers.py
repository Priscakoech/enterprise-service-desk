from rest_framework import serializers
from .models import Report, TicketStatistic, AgentPerformance, SLAMetric


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ['id', 'title', 'description', 'created_at']


class TicketStatisticSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketStatistic
        fields = ['id', 'date', 'total_tickets', 'open_tickets', 'closed_tickets']


class AgentPerformanceSerializer(serializers.ModelSerializer):
    agent_name = serializers.ReadOnlyField(source='agent.username')

    class Meta:
        model = AgentPerformance
        fields = ['id', 'agent', 'agent_name', 'tickets_resolved', 'average_resolution_time']


class SLAMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = SLAMetric
        fields = ['id', 'name', 'target_time', 'actual_time']