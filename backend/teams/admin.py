from django.contrib import admin
from .models import Department, Team, BusinessUnit, SupportGroup


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'manager', 'description']


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'department', 'description']


@admin.register(BusinessUnit)
class BusinessUnitAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']


@admin.register(SupportGroup)
class SupportGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
