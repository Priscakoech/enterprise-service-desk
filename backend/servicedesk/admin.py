from django.contrib import admin
from .models import Category, SLA, ServiceTicket, TicketResponse, Attachment


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']


@admin.register(SLA)
class SLAAdmin(admin.ModelAdmin):
    list_display = ['name', 'target_resolution_time', 'created_at']


@admin.register(ServiceTicket)
class ServiceTicketAdmin(admin.ModelAdmin):
    list_display = ['title', 'status', 'priority', 'category', 'requester', 'agent', 'created_at']
    list_filter = ['status', 'priority', 'category']
    search_fields = ['title', 'description']


@admin.register(TicketResponse)
class TicketResponseAdmin(admin.ModelAdmin):
    list_display = ['ticket', 'responder', 'created_at']


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ['ticket', 'uploaded_at']