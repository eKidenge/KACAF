from django.contrib.auth import get_user_model
from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from .models import CustomUser, MemberProfile, ExecutiveCommittee
from .serializers import (
    UserSerializer, UserRegistrationSerializer, 
    MemberProfileSerializer, ExecutiveCommitteeSerializer,
    ChangePasswordSerializer, UserUpdateSerializer
)
from .permissions import IsOwnerOrReadOnly, IsExecutiveMember, IsChairperson


User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action == 'create':
            permission_classes = [permissions.AllowAny]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def executives(self, request):
        executives = User.objects.filter(user_type='executive')
        serializer = self.get_serializer(executives, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def members(self, request):
        members = User.objects.filter(user_type='member')
        serializer = self.get_serializer(members, many=True)
        return Response(serializer.data)


class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = UserRegistrationSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Create member profile
        MemberProfile.objects.create(user=user)
        
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user, context=self.get_serializer_context()).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'message': 'User registered successfully. Awaiting verification.'
        }, status=status.HTTP_201_CREATED)


class MemberProfileViewSet(viewsets.ModelViewSet):
    queryset = MemberProfile.objects.all()
    serializer_class = MemberProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return MemberProfile.objects.all()
        return MemberProfile.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ExecutiveCommitteeViewSet(viewsets.ModelViewSet):
    queryset = ExecutiveCommittee.objects.filter(is_active=True)
    serializer_class = ExecutiveCommitteeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsChairperson]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    @action(detail=False, methods=['get'])
    def current(self, request):
        committee = ExecutiveCommittee.objects.filter(is_active=True).order_by('order')
        serializer = self.get_serializer(committee, many=True)
        return Response(serializer.data)


class ChangePasswordView(generics.UpdateAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return Response({'old_password': ['Wrong password.']}, status=status.HTTP_400_BAD_REQUEST)
        
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response({'message': 'Password updated successfully.'}, status=status.HTTP_200_OK)


# Add these at the END of your accounts/views.py file:

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth import get_user_model

# Traditional Django views for HTML templates
@login_required
def dashboard(request):
    """Traditional dashboard view"""
    # Determine which dashboard to show based on user role
    if request.user.user_type == 'admin' or request.user.is_staff:
        return render(request, 'dashboard/admin_dashboard.html')
    elif request.user.user_type == 'executive':
        return render(request, 'dashboard/executive_dashboard.html')
    elif request.user.user_type == 'member':
        return render(request, 'dashboard/member_dashboard.html')
    else:
        # Default dashboard for other user types
        return render(request, 'accounts/user/dashboard.html')

@login_required
def profile(request):
    """Traditional profile view"""
    return render(request, 'accounts/user/profile.html')

@login_required
def profile_edit(request):
    """Traditional profile edit view"""
    return render(request, 'accounts/user/profile_edit.html')

@login_required
def settings(request):
    """Traditional settings view"""
    return redirect('accounts:profile_edit')  # Redirect to profile edit for now

@login_required
@permission_required('accounts.view_customuser', raise_exception=True)
def user_list(request):
    """Traditional user list view for admins"""
    User = get_user_model()
    users = User.objects.all()
    return render(request, 'accounts/admin/user_list.html', {'users': users})