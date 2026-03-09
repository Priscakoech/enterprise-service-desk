from django.shortcuts import render
from rest_framework import generics, permissions
from .models import Report, TicketStatistic, AgentPerformance, SLAMetric
from .serializers import (
    ReportSerializer,
    TicketStatisticSerializer,
    AgentPerformanceSerializer,
    SLAMetricSerializer,
)


# Reports
class ReportListView(generics.ListCreateAPIView):
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]


class ReportDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]


# Ticket Statistics
class TicketStatisticListView(generics.ListCreateAPIView):
    queryset = TicketStatistic.objects.all()
    serializer_class = TicketStatisticSerializer
    permission_classes = [permissions.IsAuthenticated]


class TicketStatisticDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = TicketStatistic.objects.all()
    serializer_class = TicketStatisticSerializer
    permission_classes = [permissions.IsAuthenticated]


# Agent Performance
class AgentPerformanceListView(generics.ListCreateAPIView):
    queryset = AgentPerformance.objects.all()
    serializer_class = AgentPerformanceSerializer
    permission_classes = [permissions.IsAuthenticated]


class AgentPerformanceDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = AgentPerformance.objects.all()
    serializer_class = AgentPerformanceSerializer
    permission_classes = [permissions.IsAuthenticated]


# SLA Metrics
class SLAMetricListView(generics.ListCreateAPIView):
    queryset = SLAMetric.objects.all()
    serializer_class = SLAMetricSerializer
    permission_classes = [permissions.IsAuthenticated]


class SLAMetricDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = SLAMetric.objects.all()
    serializer_class = SLAMetricSerializer
    permission_classes = [permissions.IsAuthenticated]