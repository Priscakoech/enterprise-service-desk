from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Notification, Alerts, EmailTriggers
from .serializers import NotificationSerializer, AlertSerializer, EmailTriggerSerializer


class NotificationListView(generics.ListCreateAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(recipient=self.request.user)


class NotificationDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)


class MarkNotificationReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            notification = Notification.objects.get(pk=pk, recipient=request.user)
            notification.is_read = True
            notification.save()
            return Response({'message': 'Notification marked as read'})
        except Notification.DoesNotExist:
            return Response({'error': 'Notification not found'}, status=404)


class MarkAllReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        return Response({'message': 'All notifications marked as read'})


class UnreadCountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        return Response({'unread_count': count})


# Keep existing Alert and EmailTrigger views unchanged
class AlertListView(generics.ListCreateAPIView):
    queryset = Alerts.objects.all()
    serializer_class = AlertSerializer
    permission_classes = [permissions.IsAuthenticated]

class AlertDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Alerts.objects.all()
    serializer_class = AlertSerializer
    permission_classes = [permissions.IsAuthenticated]

class EmailTriggerListView(generics.ListCreateAPIView):
    queryset = EmailTriggers.objects.all()
    serializer_class = EmailTriggerSerializer
    permission_classes = [permissions.IsAuthenticated]

class EmailTriggerDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = EmailTriggers.objects.all()
    serializer_class = EmailTriggerSerializer
    permission_classes = [permissions.IsAuthenticated]
