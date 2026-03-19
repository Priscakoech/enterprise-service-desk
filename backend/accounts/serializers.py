from rest_framework import serializers
from .models import CustomUser, SignupSecret


def _get_profile_picture_url(user):
    if user.profile_picture:
        return user.profile_picture.url
    return None


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    signup_code = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'password', 'role', 'team', 'department', 'first_name', 'last_name', 'signup_code']

    def validate(self, data):
        role = data.get('role', 'requester')
        if role in ('agent', 'manager'):
            code = data.get('signup_code', '')
            if not code:
                raise serializers.ValidationError({'signup_code': 'Auth code is required for agent/manager signup.'})
            if not SignupSecret.verify_code(code):
                raise serializers.ValidationError({'signup_code': 'Invalid or expired auth code.'})
        data.pop('signup_code', None)
        return data

    def create(self, validated_data):
        user = CustomUser.objects.create_user(**validated_data)
        if user.team:
            user.team.members.add(user)
        return user


class UserSerializer(serializers.ModelSerializer):
    department_name = serializers.ReadOnlyField(source='department.name')
    team_name = serializers.ReadOnlyField(source='team.name')
    profile_picture = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'profile_picture', 'role', 'team', 'team_name', 'department', 'department_name', 'is_blacklisted', 'account_status', 'must_change_password']

    def get_profile_picture(self, obj):
        return _get_profile_picture_url(obj)

    def update(self, instance, validated_data):
        old_team_id = instance.team_id
        user = super().update(instance, validated_data)
        new_team_id = user.team_id
        if old_team_id != new_team_id:
            if old_team_id:
                from teams.models import Team
                try:
                    old_team = Team.objects.get(pk=old_team_id)
                    old_team.members.remove(user)
                except Team.DoesNotExist:
                    pass
            if new_team_id and user.team:
                user.team.members.add(user)
        return user


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=4)


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class ProfileSerializer(serializers.ModelSerializer):
    department_name = serializers.ReadOnlyField(source='department.name')
    team_name = serializers.ReadOnlyField(source='team.name')
    profile_picture = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'profile_picture', 'role', 'team_name', 'department_name']
        read_only_fields = ['id', 'role', 'team_name', 'department_name']

    def get_profile_picture(self, obj):
        return _get_profile_picture_url(obj)
