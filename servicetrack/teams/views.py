from rest_framework import generics, permissions
from .models import Team, BusinessUnit, SupportGroup
from .serializers import TeamSerializer, BusinessUnitSerializer, SupportGroupSerializer


# Teams
class TeamListView(generics.ListCreateAPIView):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    permission_classes = [permissions.IsAuthenticated]


class TeamDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Team.objects.all()
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
