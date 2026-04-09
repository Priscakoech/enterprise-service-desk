from django.contrib import admin
from .models import SLA, ServiceTicket, TicketResponse, Attachment


@admin.register(SLA)
class SLAAdmin(admin.ModelAdmin):
    list_display = ['name', 'target_resolution_time', 'created_at']


@admin.register(ServiceTicket)
class ServiceTicketAdmin(admin.ModelAdmin):
    list_display = ['title', 'status', 'priority', 'team', 'requester', 'agent', 'created_at']
    list_filter = ['status', 'priority', 'team']
    search_fields = ['title', 'description']


@admin.register(TicketResponse)
class TicketResponseAdmin(admin.ModelAdmin):
    list_display = ['ticket', 'responder', 'created_at']


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ['ticket', 'original_filename', 'file_type', 'uploaded_at']
    readonly_fields = ['file_url']