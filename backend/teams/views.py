from rest_framework import generics, permissions
from .models import Department, Team, BusinessUnit, SupportGroup
from .serializers import DepartmentSerializer, TeamSerializer, BusinessUnitSerializer, SupportGroupSerializer


# Public departments list (for registration page)
class PublicDepartmentListView(generics.ListAPIView):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.AllowAny]


# Public teams list (for registration page, filtered by department)
class PublicTeamListView(generics.ListAPIView):
    serializer_class = TeamSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = Team.objects.select_related('department').all()
        dept = self.request.query_params.get('department')
        if dept:
            qs = qs.filter(department_id=dept)
        return qs


# Departments
class DepartmentListView(generics.ListCreateAPIView):
    queryset = Department.objects.select_related('manager').all()
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAuthenticated]


class DepartmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Department.objects.select_related('manager').all()
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAuthenticated]


# Teams
class TeamListView(generics.ListCreateAPIView):
    serializer_class = TeamSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Team.objects.select_related('department').prefetch_related('members').all()
        dept = self.request.query_params.get('department')
        if dept:
            qs = qs.filter(department_id=dept)
        # Managers only see their department's teams unless ?all=true (e.g. ticket creation)
        user = self.request.user
        if self.request.query_params.get('all') != 'true':
            if getattr(user, 'role', None) == 'manager' and getattr(user, 'department_id', None):
                qs = qs.filter(department_id=user.department_id)
        return qs


class TeamDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Team.objects.select_related('department').prefetch_related('members').all()
    serializer_class = TeamSerializer
    permission_classes = [permissions.IsAuthenticated]


# Business Units
class BusinessUnitListView(generics.ListCreateAPIView):
    queryset = BusinessUnit.objects.all()
    serializer_class = BusinessUnitSerializer
    permission_classes = [permissions.IsAuthenticated]


class BusinessUnitDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = BusinessUnit.objects.all()
    serializer_class = BusinessUnitSerializer
    permission_classes = [permissions.IsAuthenticated]


# Support Groups
class SupportGroupListView(generics.ListCreateAPIView):
    queryset = SupportGroup.objects.all()
    serializer_class = SupportGroupSerializer
    permission_classes = [permissions.IsAuthenticated]


class SupportGroupDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = SupportGroup.objects.all()
    serializer_class = SupportGroupSerializer
    permission_classes = [permissions.IsAuthenticated]
