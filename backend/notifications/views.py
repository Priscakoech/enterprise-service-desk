from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Notifications, Alerts, EmailTriggers
from .serializers import NotificationSerializer, AlertSerializer, EmailTriggerSerializer


# Notifications
class NotificationListView(generics.ListCreateAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # only return notifications for the logged in user
        return Notifications.objects.all().order_by('-created_at')


class NotificationDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Notifications.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]


# Mark notification as read
class MarkNotificationReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            notification = Notifications.objects.get(pk=pk)
            notification.is_read = True
            notification.save()
            return Response({'message': 'Notification marked as read'})
        except Notifications.DoesNotExist:
            return Response({'error': 'Notification not found'}, status=404)


# Alerts
class AlertListView(generics.ListCreateAPIView):
    queryset = Alerts.objects.all()
    serializer_class = AlertSerializer
    permission_classes = [permissions.IsAuthenticated]


class AlertDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Alerts.objects.all()
    serializer_class = AlertSerializer
    permission_classes = [permissions.IsAuthenticated]


# Email Triggers
class EmailTriggerListView(generics.ListCreateAPIView):
    queryset = EmailTriggers.objects.all()
    serializer_class = EmailTriggerSerializer
    permission_classes = [permissions.IsAuthenticated]


class EmailTriggerDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = EmailTriggers.objects.all()
    serializer_class = EmailTriggerSerializer
    permission_classes = [permissions.IsAuthenticated]
