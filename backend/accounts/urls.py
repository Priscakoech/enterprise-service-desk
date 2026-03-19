from django.urls import path
from .views import RegisterView, LoginView, UserListView, UserDetailView, UserBlacklistView, UserWhitelistView, UserDeactivateView, ChangePasswordView, ProfileView, SignupCodeView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('signup-code/', SignupCodeView.as_view(), name='signup-code'),
    path('users/', UserListView.as_view(), name='user-list'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('users/<int:pk>/blacklist/', UserBlacklistView.as_view(), name='user-blacklist'),
    path('users/<int:pk>/whitelist/', UserWhitelistView.as_view(), name='user-whitelist'),
    path('users/<int:pk>/deactivate/', UserDeactivateView.as_view(), name='user-deactivate'),
]
