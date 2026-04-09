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


class IsAdminRole(permissions.BasePermission):
    message = 'Only admins can perform this action.'

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and getattr(user, 'role', None) == 'admin')


class IsAdminOrReadOnly(permissions.BasePermission):
    message = 'Only admins can modify SLA policy settings.'

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return getattr(user, 'role', None) == 'admin'


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

        # Trigger SLA evaluation - reload ticket with relationships for proper policy matching
        try:
            from .sla_engine import on_ticket_created
            # Reload ticket with team and department relationships
            ticket_with_rels = ServiceTicket.objects.select_related(
                'team', 'team__department'
            ).get(pk=ticket.pk)
            on_ticket_created(ticket_with_rels)
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
        old_description = self.get_object().description
        ticket = serializer.save()

        # Reload ticket with relationships for proper SLA policy matching
        try:
            from .sla_engine import on_status_changed, on_priority_changed, check_breaches_for_ticket
            ticket_with_rels = ServiceTicket.objects.select_related(
                'team', 'team__department'
            ).get(pk=ticket.pk)

            # Check for any SLA breaches first
            check_breaches_for_ticket(ticket_with_rels)

            if ticket.status != old_status:
                on_status_changed(ticket_with_rels, old_status, ticket.status)
            if ticket.priority != old_priority:
                on_priority_changed(ticket_with_rels, old_priority, ticket.priority)
        except Exception:
            pass

        # Broadcast ticket update via WebSocket
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            channel_layer = get_channel_layer()
            if channel_layer:
                group = f'ticket_{ticket.id}'
                now_iso = timezone.now().isoformat()

                # Determine what changed
                status_changed = ticket.status != old_status
                priority_changed = ticket.priority != old_priority
                is_closing = status_changed and ticket.status in ('solved', 'closed')

                # Build SLA snapshot for the payload
                sla_snapshot = [
                    {
                        'id': sla.id,
                        'metric': sla.metric,
                        'state': sla.state,
                        'due_at': sla.due_at.isoformat() if sla.due_at else None,
                        'target_minutes': sla.target_minutes,
                    }
                    for sla in ticket.sla_instances.all()
                ]

                change_type = 'status' if status_changed else (
                    'priority' if priority_changed else (
                        'description' if ticket.description != old_description else 'general'
                    )
                )

                # 1. Always send the general ticket_updated event
                async_to_sync(channel_layer.group_send)(
                    group,
                    {
                        'type': 'ticket_updated',
                        'event': 'STATUS_CHANGED' if status_changed else (
                            'PRIORITY_CHANGED' if priority_changed else 'TICKET_UPDATED'
                        ),
                        'data': {
                            'id': ticket.id,
                            'status': ticket.status,
                            'priority': ticket.priority,
                            'description': ticket.description,
                            'agent': ticket.agent_id,
                            'updated_at': ticket.updated_at.isoformat() if ticket.updated_at else None,
                            'is_conversation_closed': ticket.status in ('solved', 'closed'),
                            'sla_instances': sla_snapshot,
                            'change_type': change_type,
                        },
                    }
                )

                # 2. If the ticket was just closed, send a dedicated close event
                if is_closing:
                    async_to_sync(channel_layer.group_send)(
                        group,
                        {
                            'type': 'ticket_closed',
                            'ticket_id': ticket.id,
                            'closed_by': self.request.user.username,
                            'new_status': ticket.status,
                            'timestamp': now_iso,
                        }
                    )

                # 3. Send system messages for status/priority changes (appear in chat)
                if status_changed:
                    async_to_sync(channel_layer.group_send)(
                        group,
                        {
                            'type': 'system_message',
                            'event': 'STATUS_CHANGED',
                            'message': f'Status changed from {old_status} to {ticket.status}',
                            'timestamp': now_iso,
                        }
                    )

                if priority_changed:
                    async_to_sync(channel_layer.group_send)(
                        group,
                        {
                            'type': 'system_message',
                            'event': 'PRIORITY_CHANGED',
                            'message': f'Priority changed from {old_priority} to {ticket.priority}',
                            'timestamp': now_iso,
                        }
                    )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to broadcast ticket update for ticket #{ticket.id}: {str(e)}")


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

        if not uploaded_file:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'file': 'No file was uploaded.'})

        # Validate and upload to Cloudinary
        try:
            from .cloudinary_utils import validate_file, upload_to_cloudinary
            ext, file_type = validate_file(uploaded_file)
            file_url = upload_to_cloudinary(uploaded_file, folder='servicedesk/attachments')
        except ValueError as e:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'file': str(e)})
        except RuntimeError as e:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'file': str(e)})

        original_filename = uploaded_file.name

        serializer.save(
            ticket_id=ticket_id,
            file_url=file_url,
            file_type=file_type,
            original_filename=original_filename,
        )


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
    permission_classes = [IsAdminOrReadOnly]

    def perform_create(self, serializer):
        # Ensure newly created policies are not system defaults
        serializer.save(is_system_default=False)


class SLAPolicyDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = SLAPolicy.objects.prefetch_related('targets').all()
    serializer_class = SLAPolicySerializer
    permission_classes = [IsAdminOrReadOnly]

    def perform_destroy(self, instance):
        # Prevent deletion of system default policy
        if instance.is_system_default:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'error': 'Cannot delete the system default SLA policy. Use "Reset to Factory" instead.'})
        instance.delete()


class SLAPolicyResetFactoryView(APIView):
    """Reset the system default SLA policy to factory settings."""
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]

    def post(self, request, pk=None):
        try:
            policy = SLAPolicy.objects.get(pk=pk)
        except SLAPolicy.DoesNotExist:
            return Response({'error': 'Policy not found'}, status=status.HTTP_404_NOT_FOUND)

        if not policy.is_system_default:
            return Response(
                {'error': 'Only the system default policy can be reset to factory settings'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            from org_config_sync import reset_sla_to_factory
            success = reset_sla_to_factory()
            if success:
                # Reload the policy
                policy.refresh_from_db()
                return Response({
                    'status': 'success',
                    'message': 'SLA policy has been reset to factory defaults',
                    'policy': SLAPolicySerializer(policy).data,
                })
            else:
                return Response(
                    {'error': 'Failed to reset SLA policy - factory defaults not found in org_config.py'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        except Exception as e:
            return Response(
                {'error': f'Failed to reset SLA policy: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SLAEnsureDefaultView(APIView):
    """Ensure the system default SLA policy exists (creates if missing)."""
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]

    def post(self, request):
        try:
            from org_config_sync import sync_default_sla_policy
            created = sync_default_sla_policy(force=True)
            policy = SLAPolicy.objects.filter(is_system_default=True).first()
            if policy:
                return Response({
                    'status': 'success',
                    'created': created,
                    'policy': SLAPolicySerializer(policy).data,
                })
            else:
                return Response(
                    {'error': 'Failed to create default SLA policy'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        except Exception as e:
            return Response(
                {'error': f'Failed to ensure default SLA policy: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# SLA Policy Reorder
class SLAPolicyReorderView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]

    def post(self, request):
        order = request.data.get('order')
        if order is None:
            order = request.data.get('ordered_ids', [])
        for position, policy_id in enumerate(order):
            SLAPolicy.objects.filter(id=policy_id).update(position=position)
        return Response({'status': 'reordered'})


# SLA Target CRUD
class SLATargetListView(generics.ListCreateAPIView):
    serializer_class = SLATargetSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        policy_id = self.kwargs.get('policy_id')
        if policy_id:
            return SLATarget.objects.filter(policy_id=policy_id)
        return SLATarget.objects.all()

    def create(self, request, *args, **kwargs):
        """Override create to inject policy_id from URL into request data."""
        import logging
        logger = logging.getLogger(__name__)

        policy_id = self.kwargs.get('policy_id')
        logger.info(f"🔵 Creating SLA target for policy_id={policy_id}")
        logger.info(f"📥 Original request data: {request.data}")

        if policy_id:
            # Verify the policy exists first
            try:
                policy = SLAPolicy.objects.get(pk=policy_id)
                logger.info(f"✅ Found policy: {policy.name}")
            except SLAPolicy.DoesNotExist:
                logger.error(f"❌ Policy {policy_id} not found!")
                return Response(
                    {'error': f'Policy {policy_id} not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Create a mutable copy of request.data and add policy
            data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
            data['policy'] = policy_id
            logger.info(f"📤 Modified data with policy: {data}")

            # Create serializer with modified data
            serializer = self.get_serializer(data=data)
            try:
                serializer.is_valid(raise_exception=True)
                logger.info(f"✅ Serializer validation passed")
            except Exception as e:
                logger.error(f"❌ Serializer validation failed: {str(e)}")
                logger.error(f"   Errors: {serializer.errors if hasattr(serializer, 'errors') else 'N/A'}")
                raise

            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            logger.info(f"✅ Target created successfully: {serializer.data}")
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

        # If no policy_id in URL, use default behavior
        logger.warning("⚠️  No policy_id in URL")
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        """Save the target."""
        import logging
        logger = logging.getLogger(__name__)

        target = serializer.save()
        logger.info(f"💾 Saved target: {target.metric}/{target.priority} = {target.target_minutes}min for policy '{target.policy.name}'")


class SLATargetDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = SLATarget.objects.all()
    serializer_class = SLATargetSerializer
    permission_classes = [IsAdminOrReadOnly]


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
        from django.db.models import Count, Q, Exists, OuterRef
        from django.utils import timezone
        import logging

        # First, check for any real-time breaches before showing dashboard
        try:
            from .sla_engine import check_all_active_breaches
            newly_breached = check_all_active_breaches()
            if newly_breached > 0:
                logger = logging.getLogger(__name__)
                logger.warning(f"🚨 Dashboard detected {newly_breached} new SLA breaches")
        except Exception:
            pass

        now = timezone.now()
        twenty_four_hours_ago = now - timezone.timedelta(hours=24)
        seven_days_ago = now - timezone.timedelta(days=7)

        # TICKET-BASED METRICS (not instance-based)

        # 1. Tickets currently being tracked by SLA
        tickets_with_active_sla = ServiceTicket.objects.filter(
            sla_instances__state__in=['active', 'paused']
        ).distinct().count()

        # 2. Tickets with current SLA breaches (any breached instance)
        tickets_with_breaches = ServiceTicket.objects.filter(
            sla_instances__state='breached'
        ).distinct().count()

        # 3. Tickets at immediate risk (overdue but not yet breached)
        tickets_overdue = ServiceTicket.objects.filter(
            sla_instances__state='active',
            sla_instances__due_at__lte=now,
            sla_instances__due_at__isnull=False
        ).distinct().count()

        # 4. Recently resolved tickets with good SLA performance (last 7 days)
        tickets_resolved_on_time = ServiceTicket.objects.filter(
            status__in=['solved', 'closed'],
            updated_at__gte=seven_days_ago
        ).filter(
            # Has SLA instances but none are breached
            Exists(TicketSLAInstance.objects.filter(ticket=OuterRef('pk')))
        ).exclude(
            sla_instances__state='breached'
        ).distinct().count()

        # 5. Recently resolved tickets with SLA breaches (last 7 days)
        tickets_resolved_with_breaches = ServiceTicket.objects.filter(
            status__in=['solved', 'closed'],
            updated_at__gte=seven_days_ago,
            sla_instances__state='breached'
        ).distinct().count()

        # 6. New tickets created in last 24 hours
        new_tickets_24h = ServiceTicket.objects.filter(
            created_at__gte=twenty_four_hours_ago
        ).count()

        # 7. Active SLA policies (high-level policy count)
        active_policies = SLAPolicy.objects.filter(is_active=True).count()

        # DETAILED BREAKDOWN BY SLA METRIC TYPE (for advanced users)
        instance_breakdown = {}
        metric_choices = dict(SLATarget.METRIC_CHOICES)

        for metric_key, metric_label in metric_choices.items():
            active_count = TicketSLAInstance.objects.filter(
                metric=metric_key,
                state='active'
            ).count()
            breached_count = TicketSLAInstance.objects.filter(
                metric=metric_key,
                state='breached'
            ).count()

            if active_count > 0 or breached_count > 0:
                instance_breakdown[metric_key] = {
                    'label': metric_label,
                    'active': active_count,
                    'breached': breached_count,
                }

        # RECENT BREACH DETAILS (last 24 hours, ticket-focused)
        tickets_with_recent_breaches = ServiceTicket.objects.filter(
            sla_instances__state='breached',
            sla_instances__breached_at__gte=twenty_four_hours_ago
        ).distinct().select_related('agent', 'team', 'team__department')[:10]

        breach_details = []
        for ticket in tickets_with_recent_breaches:
            # Get the most recent breach for this ticket
            recent_breach = ticket.sla_instances.filter(
                state='breached',
                breached_at__gte=twenty_four_hours_ago
            ).order_by('-breached_at').first()

            if recent_breach:
                breach_details.append({
                    'ticket_id': ticket.id,
                    'ticket_title': ticket.title,
                    'ticket_status': ticket.status,
                    'agent_name': ticket.agent.username if ticket.agent else 'Unassigned',
                    'team_name': ticket.team.name if ticket.team else 'No Team',
                    'metric': recent_breach.metric,
                    'metric_display': metric_choices.get(recent_breach.metric, recent_breach.metric),
                    'breached_at': recent_breach.breached_at.isoformat() if recent_breach.breached_at else None,
                    'hours_overdue': round((now - recent_breach.due_at).total_seconds() / 3600, 1) if recent_breach.due_at else 0,
                })

        # PERFORMANCE METRICS
        total_resolved_7d = tickets_resolved_on_time + tickets_resolved_with_breaches
        sla_compliance_rate = round((tickets_resolved_on_time / total_resolved_7d * 100), 1) if total_resolved_7d > 0 else 0

        return Response({
            # OLD FORMAT (backward compatibility - what frontend expects)
            'total_instances': TicketSLAInstance.objects.count(),
            'fulfilled': TicketSLAInstance.objects.filter(state='fulfilled').count(),
            'breached': TicketSLAInstance.objects.filter(state='breached').count(),
            'active': TicketSLAInstance.objects.filter(state='active').count(),
            'paused': TicketSLAInstance.objects.filter(state='paused').count(),
            'compliance_rate': sla_compliance_rate,

            # HIGH-LEVEL COUNTS (card-friendly numbers)
            'active_count': active_policies,
            'active_policy_count': active_policies,
            'breached_count': tickets_with_breaches,
            'breached_ticket_count': tickets_with_breaches,

            # ENHANCED DATA (ticket-focused metrics)
            'tickets_being_tracked': tickets_with_active_sla,
            'tickets_with_issues': tickets_with_breaches,
            'tickets_at_risk': tickets_overdue,
            'recent_breaches': breach_details,
            'overdue': tickets_overdue,
            'breach_rate': round((TicketSLAInstance.objects.filter(state='breached').count() / max(TicketSLAInstance.objects.count(), 1) * 100), 1),

            # PERFORMANCE METRICS
            'performance_7d': sla_compliance_rate,
            'resolved_tickets_7d': total_resolved_7d,
            'health_status': 'good' if sla_compliance_rate >= 90 else 'warning' if sla_compliance_rate >= 75 else 'critical',

            # EXPLANATORY DATA (to help understand the numbers)
            '_explanation': {
                'message': f'Showing {tickets_with_active_sla} tickets being tracked with SLAs. {tickets_with_breaches} tickets have SLA issues.',
                'instances_vs_tickets': f'{TicketSLAInstance.objects.filter(state="active").count()} active SLA instances across {tickets_with_active_sla} tickets',
                'breach_details': f'{TicketSLAInstance.objects.filter(state="breached").count()} total breached instances affecting {tickets_with_breaches} tickets'
            }
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
        from django.db.models import F, Exists, OuterRef, Max
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
                'profile_picture': agent.profile_picture_url or None,
                'total_tickets': total,
                'resolved_tickets': resolved,
                'resolution_rate': round(resolved / total * 100, 1) if total > 0 else 0,
            })

        # 6. SLA summary
        total_sla = sla_qs.count()
        fulfilled = sla_qs.filter(state='fulfilled').count()
        breached = sla_qs.filter(state='breached').count()
        active = sla_qs.filter(state='active').count()

        # High-level analytics numbers (policy and ticket focused)
        if user.role == 'manager' and user.department_id:
            active_policies = SLAPolicy.objects.filter(
                is_active=True,
            ).filter(
                Q(department_id=user.department_id)
                | Q(team__department_id=user.department_id)
                | Q(is_default=True)
                | Q(is_system_default=True)
            ).distinct().count()
        else:
            active_policies = SLAPolicy.objects.filter(is_active=True).count()

        breached_tickets = ticket_qs.filter(sla_instances__state='breached').distinct().count()

        fulfilled_tickets = ticket_qs.filter(
            status__in=['solved', 'closed'],
        ).filter(
            Exists(TicketSLAInstance.objects.filter(ticket=OuterRef('pk')))
        ).exclude(
            sla_instances__state='breached'
        ).distinct().count()

        tracked_tickets = ticket_qs.filter(sla_instances__isnull=False).distinct().count()

        # 7. Agent SLA drill-down data (for clickable analytics cards)
        metric_labels = dict(SLATarget.METRIC_CHOICES)

        per_agent_counts = list(
            sla_qs.filter(ticket__agent__isnull=False)
            .values('ticket__agent_id')
            .annotate(
                active_instances=Count('id', filter=Q(state='active')),
                breached_instances=Count('id', filter=Q(state='breached')),
                active_tickets=Count('ticket_id', filter=Q(state='active'), distinct=True),
                breached_tickets=Count('ticket_id', filter=Q(state='breached'), distinct=True),
                latest_breached_at=Max('breached_at', filter=Q(state='breached')),
            )
        )

        per_agent_metric_counts = list(
            sla_qs.filter(ticket__agent__isnull=False, state__in=['active', 'breached'])
            .values('ticket__agent_id', 'metric', 'state')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        metric_map = {}
        for row in per_agent_metric_counts:
            agent_id = row['ticket__agent_id']
            if not agent_id:
                continue
            state = row['state']
            metric_label = metric_labels.get(row['metric'], row['metric'])
            metric_map.setdefault(agent_id, {'active': [], 'breached': []})
            metric_map[agent_id][state].append({
                'metric': row['metric'],
                'metric_label': metric_label,
                'count': row['count'],
            })

        agent_ids = [row['ticket__agent_id'] for row in per_agent_counts if row.get('ticket__agent_id')]
        agent_info_map = {}
        if agent_ids:
            for agent in CustomUser.objects.filter(id__in=agent_ids).select_related('department'):
                agent_info_map[agent.id] = {
                    'id': agent.id,
                    'name': f"{agent.first_name} {agent.last_name}".strip() or agent.username,
                    'email': agent.email,
                    'department': agent.department.name if agent.department else '',
                    'profile_picture': agent.profile_picture_url or None,
                }

        active_agent_details = []
        breached_agent_details = []

        for row in per_agent_counts:
            agent_id = row['ticket__agent_id']
            if not agent_id:
                continue
            info = agent_info_map.get(agent_id)
            if not info:
                continue

            active_metrics = metric_map.get(agent_id, {}).get('active', [])
            breached_metrics = metric_map.get(agent_id, {}).get('breached', [])

            if row['active_instances'] > 0:
                active_agent_details.append({
                    **info,
                    'active_instances': row['active_instances'],
                    'active_tickets': row['active_tickets'],
                    'metric_breakdown': active_metrics[:4],
                })

            if row['breached_instances'] > 0:
                breached_agent_details.append({
                    **info,
                    'breached_instances': row['breached_instances'],
                    'breached_tickets': row['breached_tickets'],
                    'metric_breakdown': breached_metrics[:4],
                    'latest_breached_at': row['latest_breached_at'].isoformat() if row['latest_breached_at'] else None,
                })

        active_agent_details.sort(key=lambda a: (-a['active_instances'], -a['active_tickets'], a['name']))
        breached_agent_details.sort(key=lambda a: (-a['breached_instances'], -a['breached_tickets'], a['name']))

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
                'active_policies': active_policies,
                'breached_tickets': breached_tickets,
                'fulfilled_tickets': fulfilled_tickets,
                'tracked_tickets': tracked_tickets,
            },
            'sla_agent_drilldown': {
                'active': active_agent_details,
                'breached': breached_agent_details,
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
