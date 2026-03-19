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
    agent_name = serializers.SerializerMethodField()

    class Meta:
        model = AgentPerformance
        fields = ['id', 'agent', 'agent_name', 'tickets_resolved', 'average_resolution_time']

    def get_agent_name(self, obj):
        if obj.agent and obj.agent.first_name and obj.agent.last_name:
            return f"{obj.agent.first_name} {obj.agent.last_name}"
        return obj.agent.username if obj.agent else None


class SLAMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = SLAMetric
        fields = ['id', 'name', 'target_time', 'actual_time']