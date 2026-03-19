from django.urls import path
from .views import (
    PublicDepartmentListView,
    PublicTeamListView,
    DepartmentListView,
    DepartmentDetailView,
    TeamListView,
    TeamDetailView,
    BusinessUnitListView,
    BusinessUnitDetailView,
    SupportGroupListView,
    SupportGroupDetailView,
)

urlpatterns = [
    # Public endpoints (no auth required, for registration)
    path('departments/public/', PublicDepartmentListView.as_view(), name='public-department-list'),
    path('public/', PublicTeamListView.as_view(), name='public-team-list'),

    # Departments
    path('departments/', DepartmentListView.as_view(), name='department-list'),
    path('departments/<int:pk>/', DepartmentDetailView.as_view(), name='department-detail'),

    # Teams
    path('', TeamListView.as_view(), name='team-list'),
    path('<int:pk>/', TeamDetailView.as_view(), name='team-detail'),

    # Business Units
    path('business-units/', BusinessUnitListView.as_view(), name='business-unit-list'),
    path('business-units/<int:pk>/', BusinessUnitDetailView.as_view(), name='business-unit-detail'),

    # Support Groups
    path('support-groups/', SupportGroupListView.as_view(), name='support-group-list'),
    path('support-groups/<int:pk>/', SupportGroupDetailView.as_view(), name='support-group-detail'),
]
