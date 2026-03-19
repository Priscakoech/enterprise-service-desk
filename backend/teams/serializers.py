from rest_framework import serializers
from .models import Department, Team, BusinessUnit, SupportGroup
from accounts.models import CustomUser
from accounts.serializers import UserSerializer


class DepartmentSerializer(serializers.ModelSerializer):
    manager_name = serializers.ReadOnlyField(source='manager.username')
    agent_count = serializers.SerializerMethodField()
    team_count = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = ['id', 'name', 'abbreviation', 'description', 'manager', 'manager_name', 'agent_count', 'team_count']

    def get_agent_count(self, obj):
        return obj.staff.filter(role='agent').count()

    def get_team_count(self, obj):
        return obj.teams.count()


class TeamSerializer(serializers.ModelSerializer):
    department_name = serializers.ReadOnlyField(source='department.name')
    member_ids = serializers.PrimaryKeyRelatedField(
        source='members',
        many=True,
        queryset=CustomUser.objects.filter(role='agent'),
        required=False,
    )
    member_details = UserSerializer(source='members', many=True, read_only=True)

    class Meta:
        model = Team
        fields = ['id', 'name', 'description', 'department', 'department_name', 'member_ids', 'member_details']


class BusinessUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessUnit
        fields = ['id', 'name', 'description']


class SupportGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportGroup
        fields = ['id', 'name', 'description']
