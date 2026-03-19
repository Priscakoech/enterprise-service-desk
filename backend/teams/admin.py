from django.contrib import admin
from .models import Team, BusinessUnit, SupportGroup


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']


@admin.register(BusinessUnit)
class BusinessUnitAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']


@admin.register(SupportGroup)
class SupportGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
