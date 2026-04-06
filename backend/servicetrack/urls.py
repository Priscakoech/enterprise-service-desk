"""
URL configuration for servicetrack project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/servicedesk/', include('servicedesk.urls')),
    path('api/accounts/', include('accounts.urls')),
    path('api/teams/', include('teams.urls')),
    path('api/notifications/', include('notifications.urls')),
    path('api/analytics/', include('analytics.urls')),
]

# Media files — served by Django in dev. In prod with Railway, media is
# ephemeral (see README for notes). WhiteNoise handles static files.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
