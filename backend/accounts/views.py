from django.shortcuts import render
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status as http_status
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from .models import CustomUser, SignupSecret
from .serializers import RegisterSerializer, UserSerializer, LoginSerializer, ChangePasswordSerializer, ProfileSerializer
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser


# Register a new user
class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


# Login - returns token
class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)

        if user is not None:
            if user.is_blacklisted or user.account_status == 'blacklisted':
                return Response({'error': 'Your account has been suspended. Contact an administrator.'}, status=403)
            if user.account_status == 'deactivated':
                return Response({'error': 'Your account has been deactivated. Contact an administrator.'}, status=403)
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user': UserSerializer(user, context={'request': request}).data
            })
        return Response({'error': 'Invalid credentials'}, status=400)


# Get all users (admin/manager only)
class UserListView(generics.ListAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


# Get, update, or delete a single user
class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        if request.user.role != 'admin':
            return Response({'error': 'Only admins can delete users'}, status=403)
        user = self.get_object()
        if user.id == request.user.id:
            return Response({'error': 'Cannot delete your own account'}, status=400)
        user.delete()
        return Response(status=204)


class UserBlacklistView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        if request.user.role != 'admin':
            return Response({'error': 'Only admins can blacklist users'}, status=403)
        try:
            user = CustomUser.objects.get(pk=pk)
            if user.id == request.user.id:
                return Response({'error': 'Cannot blacklist yourself'}, status=400)
            user.is_blacklisted = True
            user.account_status = 'blacklisted'
            user.save()
            # Delete their auth token to force logout
            Token.objects.filter(user=user).delete()
            return Response({'message': f'User {user.username} has been blacklisted'})
        except CustomUser.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)

class UserWhitelistView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        if request.user.role != 'admin':
            return Response({'error': 'Only admins can whitelist users'}, status=403)
        try:
            user = CustomUser.objects.get(pk=pk)
            user.is_blacklisted = False
            user.account_status = 'active'
            user.save()
            return Response({'message': f'User {user.username} has been whitelisted'})
        except CustomUser.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)

class UserDeactivateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        if request.user.role != 'admin':
            return Response({'error': 'Only admins can deactivate users'}, status=403)
        try:
            user = CustomUser.objects.get(pk=pk)
            if user.id == request.user.id:
                return Response({'error': 'Cannot deactivate yourself'}, status=400)
            user.account_status = 'deactivated'
            user.save()
            Token.objects.filter(user=user).delete()
            return Response({'message': f'User {user.username} has been deactivated'})
        except CustomUser.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not request.user.check_password(serializer.validated_data['current_password']):
            return Response({'error': 'Current password is incorrect'}, status=http_status.HTTP_400_BAD_REQUEST)

        request.user.set_password(serializer.validated_data['new_password'])
        request.user.must_change_password = False
        request.user.save(update_fields=['password', 'must_change_password'])

        # Re-create token so the user stays logged in
        Token.objects.filter(user=request.user).delete()
        token = Token.objects.create(user=request.user)

        return Response({
            'message': 'Password changed successfully',
            'token': token.key,
        })


class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        serializer = ProfileSerializer(request.user, context={'request': request})
        return Response(serializer.data)

    def patch(self, request):
        user = request.user
        # Handle profile picture upload via Cloudinary
        if 'profile_picture' in request.FILES:
            try:
                from servicedesk.cloudinary_utils import upload_profile_picture
                url = upload_profile_picture(request.FILES['profile_picture'])
                user.profile_picture_url = url
                user.save(update_fields=['profile_picture_url'])
            except (ValueError, RuntimeError) as e:
                return Response({'error': str(e)}, status=400)
        serializer = ProfileSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ProfileSerializer(user).data)


class SignupCodeView(APIView):
    """Admin-only endpoint to view the current time-based signup auth code."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role != 'admin':
            return Response({'error': 'Admin access required'}, status=403)
        return Response({
            'code': SignupSecret.get_current_code(),
            'seconds_remaining': SignupSecret.seconds_remaining(),
        })
