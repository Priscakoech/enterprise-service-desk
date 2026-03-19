from rest_framework import generics, permissions
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Category, SLA, ServiceTicket, TicketResponse, Attachment
from .serializers import (
    CategorySerializer,
    SLASerializer,
    ServiceTicketSerializer,
    TicketResponseSerializer,
    AttachmentSerializer,
)


# Category
class CategoryListView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]


# SLA
class SLAListView(generics.ListCreateAPIView):
    queryset = SLA.objects.all()
    serializer_class = SLASerializer
    permission_classes = [permissions.IsAuthenticated]


class SLADetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = SLA.objects.all()
    serializer_class = SLASerializer
    permission_classes = [permissions.IsAuthenticated]


# Service Tickets
class ServiceTicketListView(generics.ListCreateAPIView):
    serializer_class = ServiceTicketSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # admin and manager see all tickets
        if user.role in ['admin', 'manager']:
            return ServiceTicket.objects.all().order_by('-created_at')
        # agent sees tickets assigned to them
        if user.role == 'agent':
            return ServiceTicket.objects.filter(agent=user).order_by('-created_at')
        # requester sees only their own tickets
        return ServiceTicket.objects.filter(requester=user).order_by('-created_at')

    def perform_create(self, serializer):
        # automatically set requester to the logged in user
        serializer.save(requester=self.request.user)


class ServiceTicketDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ServiceTicketSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role in ['admin', 'manager']:
            return ServiceTicket.objects.all()
        if user.role == 'agent':
            return ServiceTicket.objects.filter(agent=user)
        return ServiceTicket.objects.filter(requester=user)


# Ticket Responses
class TicketResponseListView(generics.ListCreateAPIView):
    serializer_class = TicketResponseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        ticket_id = self.kwargs.get('ticket_id')
        return TicketResponse.objects.filter(ticket_id=ticket_id)

    def perform_create(self, serializer):
        # automatically set responder to the logged in user
        serializer.save(responder=self.request.user)


class TicketResponseDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = TicketResponse.objects.all()
    serializer_class = TicketResponseSerializer
    permission_classes = [permissions.IsAuthenticated]


# Attachments
class AttachmentListView(generics.ListCreateAPIView):
    serializer_class = AttachmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        ticket_id = self.kwargs.get('ticket_id')
        return Attachment.objects.filter(ticket_id=ticket_id)

    def perform_create(self, serializer):
        ticket_id = self.kwargs.get('ticket_id')
        serializer.save(ticket_id=ticket_id)


class AttachmentDetailView(generics.RetrieveDestroyAPIView):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer
    permission_classes = [permissions.IsAuthenticated]
