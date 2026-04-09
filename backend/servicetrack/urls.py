"""
URL configuration for servicetrack project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/servicedesk/', include('servicedesk.urls')),
    path('api/accounts/', include('accounts.urls')),
    path('api/teams/', include('teams.urls')),
    path('api/notifications/', include('notifications.urls')),
    path('api/analytics/', include('analytics.urls')),
]

