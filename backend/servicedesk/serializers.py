from rest_framework import serializers
from .models import (SLA, ServiceTicket, TicketResponse, Attachment,
                     BusinessSchedule, SLAPolicy, SLATarget, TicketSLAInstance, SLAAuditLog)


class SLASerializer(serializers.ModelSerializer):
    class Meta:
        model = SLA
        fields = ['id', 'name', 'target_resolution_time', 'created_at']


class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = ['id', 'file_url', 'response', 'file_type', 'original_filename', 'uploaded_at']
        read_only_fields = ['file_url']


class TicketResponseSerializer(serializers.ModelSerializer):
    responder_name = serializers.SerializerMethodField()
    responder_role = serializers.ReadOnlyField(source='responder.role')

    class Meta:
        model = TicketResponse
        fields = ['id', 'ticket', 'responder', 'responder_name', 'responder_role', 'message', 'message_type', 'is_from_agent', 'created_at']
        read_only_fields = ['ticket', 'responder']

    def get_responder_name(self, obj):
        u = obj.responder
        if u and u.first_name and u.last_name:
            return f"{u.first_name} {u.last_name}"
        return u.username if u else None


class BusinessScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessSchedule
        fields = ['id', 'name', 'timezone', 'hours', 'holidays', 'created_at']


class SLATargetSerializer(serializers.ModelSerializer):
    metric_display = serializers.CharField(source='get_metric_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    # Make policy optional in input - it will be set by the view from URL
    policy = serializers.PrimaryKeyRelatedField(
        queryset=SLAPolicy.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = SLATarget
        fields = ['id', 'policy', 'metric', 'metric_display', 'priority', 'priority_display', 'target_minutes']


class SLAPolicySerializer(serializers.ModelSerializer):
    targets = serializers.SerializerMethodField()
    schedule_name = serializers.ReadOnlyField(source='schedule.name')
    team_name = serializers.ReadOnlyField(source='team.name')
    department_name = serializers.ReadOnlyField(source='department.name')

    class Meta:
        model = SLAPolicy
        fields = ['id', 'name', 'description', 'position', 'is_active', 'is_default', 'is_system_default',
                  'team', 'team_name', 'department', 'department_name',
                  'schedule', 'schedule_name', 'conditions', 'targets', 'created_at', 'updated_at']
        read_only_fields = ['is_system_default']

    def get_targets(self, obj):
        targets = obj.targets.all()
        return SLATargetSerializer(targets, many=True).data


class TicketSLAInstanceSerializer(serializers.ModelSerializer):
    policy_name = serializers.ReadOnlyField(source='policy.name')
    schedule_name = serializers.SerializerMethodField()
    metric_display = serializers.SerializerMethodField()

    class Meta:
        model = TicketSLAInstance
        fields = ['id', 'ticket', 'policy', 'policy_name', 'schedule_name',
                  'metric', 'metric_display', 'target_minutes',
                  'started_at', 'due_at', 'achieved_at', 'breached_at', 'paused_at',
                  'accumulated_pause_minutes', 'active_business_minutes', 'state', 'last_event_at']

    def get_schedule_name(self, obj):
        if obj.policy and obj.policy.schedule:
            return obj.policy.schedule.name
        return None

    def get_metric_display(self, obj):
        metric_labels = dict(SLATarget.METRIC_CHOICES)
        return metric_labels.get(obj.metric, obj.metric)


class SLAAuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SLAAuditLog
        fields = ['id', 'ticket', 'sla_instance', 'event_type', 'old_state', 'new_state', 'details', 'timestamp']


class ServiceTicketSerializer(serializers.ModelSerializer):
    requester_name = serializers.SerializerMethodField()
    agent_name = serializers.SerializerMethodField()
    team_name = serializers.ReadOnlyField(source='team.name')
    department_id = serializers.ReadOnlyField(source='team.department.id')
    department_name = serializers.ReadOnlyField(source='team.department.name')
    responses = TicketResponseSerializer(many=True, read_only=True)
    attachments = AttachmentSerializer(many=True, read_only=True)
    sla_instances = TicketSLAInstanceSerializer(many=True, read_only=True)

    class Meta:
        model = ServiceTicket
        fields = [
            'id', 'reference_id', 'title', 'description',
            'status', 'priority', 'team', 'team_name', 'department_id', 'department_name',
            'requester', 'requester_name',
            'agent', 'agent_name',
            'created_at', 'updated_at',
            'responses', 'attachments', 'sla_instances',
        ]
        read_only_fields = ['requester', 'agent']

    def _full_name(self, user):
        if user and user.first_name and user.last_name:
            return f"{user.first_name} {user.last_name}"
        return user.username if user else None

    def get_requester_name(self, obj):
        return self._full_name(obj.requester)

    def get_agent_name(self, obj):
        return self._full_name(obj.agent)
