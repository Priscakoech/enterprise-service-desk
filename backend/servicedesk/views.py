from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Count, Q
from django.utils import timezone
from .models import (SLA, ServiceTicket, TicketResponse, Attachment,
                     BusinessSchedule, SLAPolicy, SLATarget, TicketSLAInstance, SLAAuditLog)
from .serializers import (
    SLASerializer,
    ServiceTicketSerializer,
    TicketResponseSerializer,
    AttachmentSerializer,
    BusinessScheduleSerializer,
    SLAPolicySerializer,
    SLATargetSerializer,
    TicketSLAInstanceSerializer,
    SLAAuditLogSerializer,
)


# SLA
class SLAListView(generics.ListCreateAPIView):
    queryset = SLA.objects.all()
    serializer_class = SLASerializer
    permission_classes = [permissions.IsAuthenticated]


class SLADetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = SLA.objects.all()
    serializer_class = SLASerializer
    permission_classes = [permissions.IsAuthenticated]


def auto_assign_agent(team):
    """Find least-busy agent in the team's department."""
    if not team or not team.department:
        return None

    department = team.department
    agents = department.staff.filter(role='agent')
    if not agents.exists():
        return None

    # Annotate with count of open tickets (not resolved/closed)
    agents = agents.annotate(
        open_tickets=Count(
            'assigned_tickets',
            filter=Q(assigned_tickets__status__in=['new', 'open', 'pending', 'on_hold']),
        )
    ).order_by('open_tickets')

    return agents.first()


# Service Tickets
class ServiceTicketListView(generics.ListCreateAPIView):
    serializer_class = ServiceTicketSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = ServiceTicket.objects.select_related('team', 'team__department', 'requester', 'agent')
        if user.role == 'admin':
            return qs.all().order_by('-created_at')
        if user.role == 'manager':
            return qs.filter(
                Q(team__department=user.department) | Q(requester=user)
            ).distinct().order_by('-created_at')
        if user.role == 'agent':
            return qs.filter(Q(agent=user) | Q(requester=user)).distinct().order_by('-created_at')
        # requester
        return qs.filter(requester=user).order_by('-created_at')

    def perform_create(self, serializer):
        team = serializer.validated_data.get('team')
        agent = auto_assign_agent(team)
        ticket = serializer.save(
            requester=self.request.user,
            agent=agent,
            status='new',
        )

        # Generate reference_id: {DEPT_ABBREV}TKTREQ{NUM}{DDMMYY}
        try:
            dept_abbrev = ''
            if team and team.department:
                dept_abbrev = team.department.abbreviation or ''
            if not dept_abbrev:
                dept_abbrev = 'GEN'
            num_padded = str(ticket.pk).zfill(3)
            date_str = timezone.now().strftime('%d%m%y')
            ticket.reference_id = f'{dept_abbrev}TKTREQ{num_padded}{date_str}'
            ticket.save(update_fields=['reference_id'])
        except Exception:
            pass

        # Trigger SLA evaluation
        try:
            from .sla_engine import on_ticket_created
            on_ticket_created(ticket)
        except Exception:
            pass  # Don't fail ticket creation if SLA engine errors


class ServiceTicketDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ServiceTicketSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = ServiceTicket.objects.select_related('team', 'team__department', 'requester', 'agent')
        if user.role == 'admin':
            return qs.all()
        if user.role == 'manager':
            return qs.filter(
                Q(team__department=user.department) | Q(requester=user)
            ).distinct()
        if user.role == 'agent':
            return qs.filter(Q(agent=user) | Q(requester=user)).distinct()
        return qs.filter(requester=user)

    def get_serializer(self, *args, **kwargs):
        serializer = super().get_serializer(*args, **kwargs)
        if self.request.method in ('PUT', 'PATCH'):
            user = self.request.user
            if user.role == 'admin':
                # Admins can edit everything
                if 'agent' in serializer.fields:
                    serializer.fields['agent'].read_only = False
            elif user.role == 'manager':
                # Managers can only reassign agent
                if 'agent' in serializer.fields:
                    serializer.fields['agent'].read_only = False
                if 'status' in serializer.fields:
                    serializer.fields['status'].read_only = True
                if 'priority' in serializer.fields:
                    serializer.fields['priority'].read_only = True
            elif user.role == 'agent':
                # Agents can only change status
                if 'priority' in serializer.fields:
                    serializer.fields['priority'].read_only = True
        return serializer

    def perform_update(self, serializer):
        old_status = self.get_object().status
        old_priority = self.get_object().priority
        ticket = serializer.save()

        try:
            from .sla_engine import on_status_changed, on_priority_changed
            if ticket.status != old_status:
                on_status_changed(ticket, old_status, ticket.status)
            if ticket.priority != old_priority:
                on_priority_changed(ticket, old_priority, ticket.priority)
        except Exception:
            pass


# Ticket Responses (chat)
class TicketResponseListView(generics.ListCreateAPIView):
    serializer_class = TicketResponseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        ticket_id = self.kwargs.get('ticket_id')
        return TicketResponse.objects.filter(ticket_id=ticket_id).order_by('created_at')

    def create(self, request, *args, **kwargs):
        ticket_id = self.kwargs.get('ticket_id')
        try:
            ticket = ServiceTicket.objects.get(pk=ticket_id)
        except ServiceTicket.DoesNotExist:
            return Response({'error': 'Ticket not found'}, status=status.HTTP_404_NOT_FOUND)

        if not ticket.agent:
            return Response({'error': 'Ticket has not been assigned yet'}, status=status.HTTP_400_BAD_REQUEST)
        if ticket.status in ('resolved', 'closed'):
            return Response({'error': 'Ticket is closed, chat is disabled'}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        if user.role not in ('admin', 'manager') and user != ticket.requester and user != ticket.agent:
            return Response({'error': 'You are not part of this conversation'}, status=status.HTTP_403_FORBIDDEN)

        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        ticket_id = self.kwargs.get('ticket_id')
        ticket = ServiceTicket.objects.get(pk=ticket_id)
        user = self.request.user
        is_agent = user.role in ('agent', 'manager', 'admin')

        response = serializer.save(
            responder=user,
            ticket_id=ticket_id,
            is_from_agent=is_agent,
        )

        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'ticket_{ticket_id}',
                {
                    'type': 'chat_message',
                    'message': response.message,
                    'sender_id': user.id,
                    'sender_name': user.username,
                    'sender_role': user.role,
                    'timestamp': timezone.now().isoformat(),
                }
            )
        except Exception:
            pass

        try:
            if is_agent and response.message_type == 'public_reply':
                from .sla_engine import on_public_agent_reply
                on_public_agent_reply(ticket, response)
            elif not is_agent and response.message_type == 'public_reply':
                from .sla_engine import on_requester_reply
                on_requester_reply(ticket, response)
        except Exception:
            pass


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
        uploaded_file = self.request.FILES.get('file')
        file_type = ''
        original_filename = ''

        if uploaded_file:
            original_filename = uploaded_file.name
            ext = original_filename.rsplit('.', 1)[-1].lower() if '.' in original_filename else ''
            image_exts = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp'}
            doc_exts = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt', 'csv', 'ppt', 'pptx'}

            if ext in image_exts:
                file_type = 'image'
            elif ext in doc_exts:
                file_type = 'document'
            else:
                from rest_framework.exceptions import ValidationError
                raise ValidationError({'file': f'File type .{ext} is not allowed. Only images and documents are accepted.'})

        serializer.save(ticket_id=ticket_id, file_type=file_type, original_filename=original_filename)


class AttachmentDetailView(generics.RetrieveDestroyAPIView):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer
    permission_classes = [permissions.IsAuthenticated]


# Business Schedule
class BusinessScheduleListView(generics.ListCreateAPIView):
    queryset = BusinessSchedule.objects.all()
    serializer_class = BusinessScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]


class BusinessScheduleDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = BusinessSchedule.objects.all()
    serializer_class = BusinessScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]


# SLA Policy
class SLAPolicyListView(generics.ListCreateAPIView):
    queryset = SLAPolicy.objects.prefetch_related('targets').all()
    serializer_class = SLAPolicySerializer
    permission_classes = [permissions.IsAuthenticated]


class SLAPolicyDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = SLAPolicy.objects.prefetch_related('targets').all()
    serializer_class = SLAPolicySerializer
    permission_classes = [permissions.IsAuthenticated]


# SLA Policy Reorder
class SLAPolicyReorderView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        order = request.data.get('order', [])
        for position, policy_id in enumerate(order):
            SLAPolicy.objects.filter(id=policy_id).update(position=position)
        return Response({'status': 'reordered'})


# SLA Target CRUD
class SLATargetListView(generics.ListCreateAPIView):
    serializer_class = SLATargetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        policy_id = self.kwargs.get('policy_id')
        if policy_id:
            return SLATarget.objects.filter(policy_id=policy_id)
        return SLATarget.objects.all()


class SLATargetDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = SLATarget.objects.all()
    serializer_class = SLATargetSerializer
    permission_classes = [permissions.IsAuthenticated]


# Ticket SLA Instances
class TicketSLAInstanceListView(generics.ListAPIView):
    serializer_class = TicketSLAInstanceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        ticket_id = self.kwargs.get('ticket_id')
        return TicketSLAInstance.objects.filter(ticket_id=ticket_id)


# SLA Audit Log
class SLAAuditLogListView(generics.ListAPIView):
    serializer_class = SLAAuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        ticket_id = self.kwargs.get('ticket_id')
        if ticket_id:
            return SLAAuditLog.objects.filter(ticket_id=ticket_id)
        return SLAAuditLog.objects.all()


# SLA Dashboard
class SLADashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from django.db.models import Count, Q
        total = TicketSLAInstance.objects.count()
        fulfilled = TicketSLAInstance.objects.filter(state='fulfilled').count()
        breached = TicketSLAInstance.objects.filter(state='breached').count()
        active = TicketSLAInstance.objects.filter(state='active').count()
        paused = TicketSLAInstance.objects.filter(state='paused').count()

        compliance_rate = round((fulfilled / total * 100), 1) if total > 0 else 0

        return Response({
            'total_instances': total,
            'fulfilled': fulfilled,
            'breached': breached,
            'active': active,
            'paused': paused,
            'compliance_rate': compliance_rate,
        })


class SLAAnalyticsDashboardView(APIView):
    """Server-side aggregated analytics, role-scoped (admin=all, manager=department)."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role not in ('admin', 'manager'):
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

        # Base querysets scoped by role
        ticket_qs = ServiceTicket.objects.select_related('team', 'team__department', 'agent')
        sla_qs = TicketSLAInstance.objects.select_related('ticket__team', 'ticket__team__department')

        if user.role == 'manager' and user.department_id:
            ticket_qs = ticket_qs.filter(team__department_id=user.department_id)
            sla_qs = sla_qs.filter(ticket__team__department_id=user.department_id)

        # 1. Status distribution
        status_distribution = list(
            ticket_qs.values('status').annotate(count=Count('id')).order_by('status')
        )

        # 2. Priority distribution
        priority_distribution = list(
            ticket_qs.values('priority').annotate(count=Count('id')).order_by('priority')
        )

        # 3. Team SLA compliance
        from django.db.models import F
        team_sla = list(
            sla_qs.filter(ticket__team__isnull=False)
            .values(team_name=F('ticket__team__name'))
            .annotate(
                fulfilled=Count('id', filter=Q(state='fulfilled')),
                breached=Count('id', filter=Q(state='breached')),
                active=Count('id', filter=Q(state='active')),
                total=Count('id'),
            )
            .order_by('team_name')
        )

        # 4. Department SLA compliance
        dept_sla = list(
            sla_qs.filter(ticket__team__department__isnull=False)
            .values(department_name=F('ticket__team__department__name'))
            .annotate(
                fulfilled=Count('id', filter=Q(state='fulfilled')),
                breached=Count('id', filter=Q(state='breached')),
                active=Count('id', filter=Q(state='active')),
                total=Count('id'),
            )
            .order_by('department_name')
        )

        # 5. Agent performance
        from accounts.models import CustomUser
        agent_qs = CustomUser.objects.filter(role='agent')
        if user.role == 'manager' and user.department_id:
            agent_qs = agent_qs.filter(department_id=user.department_id)

        agent_performance = []
        for agent in agent_qs.select_related('department'):
            agent_tickets = ticket_qs.filter(agent=agent)
            total = agent_tickets.count()
            resolved = agent_tickets.filter(status__in=['solved', 'closed']).count()
            agent_performance.append({
                'id': agent.id,
                'name': f"{agent.first_name} {agent.last_name}".strip() or agent.username,
                'email': agent.email,
                'department': agent.department.name if agent.department else '',
                'profile_picture': agent.profile_picture.url if agent.profile_picture else None,
                'total_tickets': total,
                'resolved_tickets': resolved,
                'resolution_rate': round(resolved / total * 100, 1) if total > 0 else 0,
            })

        # 6. SLA summary
        total_sla = sla_qs.count()
        fulfilled = sla_qs.filter(state='fulfilled').count()
        breached = sla_qs.filter(state='breached').count()
        active = sla_qs.filter(state='active').count()

        return Response({
            'status_distribution': status_distribution,
            'priority_distribution': priority_distribution,
            'team_sla_compliance': team_sla,
            'department_sla_compliance': dept_sla,
            'agent_performance': agent_performance,
            'sla_summary': {
                'total': total_sla,
                'fulfilled': fulfilled,
                'breached': breached,
                'active': active,
                'compliance_rate': round(fulfilled / total_sla * 100, 1) if total_sla > 0 else 0,
            },
            'total_tickets': ticket_qs.count(),
        })


class AutoAssignView(APIView):
    """Scan for unassigned tickets and assign them to available agents."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            from org_config_sync import sync_org_config
            sync_org_config()
        except Exception:
            pass

        unassigned = ServiceTicket.objects.filter(
            agent__isnull=True,
            status__in=['new', 'open', 'pending', 'on_hold'],
        ).select_related('team', 'team__department')

        assigned_count = 0
        for ticket in unassigned:
            agent = auto_assign_agent(ticket.team)
            if agent:
                ticket.agent = agent
                ticket.save(update_fields=['agent'])
                assigned_count += 1
                try:
                    from notifications.services import notify_ticket_assigned
                    notify_ticket_assigned(ticket, agent)
                except Exception:
                    pass

        return Response({'assigned': assigned_count, 'remaining_unassigned': unassigned.count() - assigned_count})
