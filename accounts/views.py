from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from rest_framework import viewsets, generics, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.decorators import login_required
from django.views.generic import CreateView, DetailView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib import messages
import random
import string

from .models import MemberProfile, ExecutiveCommittee
from .serializers import (
    UserSerializer,
    UserRegistrationSerializer,
    MemberProfileSerializer,
    ExecutiveCommitteeSerializer,
    ChangePasswordSerializer,
)
from .permissions import IsOwnerOrReadOnly, IsChairperson

User = get_user_model()


# ---------------------------
# Public & role dashboards
# ---------------------------
def public_dashboard(request):
    context = {
        "total_trees_planted": 12345,
        "total_members": 6789,
        "total_area_coverage": 1500,
        "total_beneficiaries": 2345,
        "carbon_sequestered": 987,
        "featured_programs": [],
        "upcoming_events": [],
        "testimonials": [],
        "partners": [],
    }
    return render(request, "dashboard/public_dashboard.html", context)


@login_required
def dashboard_redirect(request):
    """
    Redirect users to their appropriate dashboard based on role
    """
    if request.user.is_staff:
        return redirect('accounts:admin_dashboard')
    elif request.user.groups.filter(name='Executive Committee').exists():
        return redirect('accounts:executive_dashboard')
    else:
        return redirect('accounts:member_dashboard')


@login_required
def admin_dashboard(request):
    # Add context data for admin dashboard
    context = {
        "total_users": User.objects.count(),
        "verified_users": User.objects.filter(is_verified=True).count(),
        "regular_members": User.objects.filter(user_type='member').count(),
        "total_income": 0,  # Placeholder - replace with actual data
        "total_expenses": 0,  # Placeholder - replace with actual data
        "net_balance": 0,  # Placeholder - replace with actual data
        "total_programs": 0,  # Placeholder - replace with actual data
        "active_projects": 0,  # Placeholder - replace with actual data
        "total_trees": 0,  # Placeholder - replace with actual data
        "total_logins_today": 0,  # Placeholder - replace with actual data
        "storage_used": "0 MB",  # Placeholder - replace with actual data
        "error_logs_count": 0,  # Placeholder - replace with actual data
        "recent_activities": [],  # Placeholder - replace with actual data
        "pending_approvals": [],  # Placeholder - replace with actual data
        "system_alerts": [],  # Placeholder - replace with actual data
        "recent_users": User.objects.order_by('-date_joined')[:5],
        "today_income": 0,  # Placeholder - replace with actual data
        "weekly_income": 0,  # Placeholder - replace with actual data
        "monthly_income": 0,  # Placeholder - replace with actual data
        "financial_labels": [],  # Placeholder - replace with actual data
        "income_data": [],  # Placeholder - replace with actual data
        "expense_data": [],  # Placeholder - replace with actual data
        "server_health": {  # Placeholder - replace with actual data
            "status": "healthy",
            "cpu": 45,
            "memory": 60
        },
        "db_health": {  # Placeholder - replace with actual data
            "status": "healthy",
            "size": 1024 * 1024 * 10,  # 10 MB
            "connections": 5,
            "tables": 15
        },
        "backup_health": {  # Placeholder - replace with actual data
            "last_successful": True,
            "last_backup": None,
            "next_backup": None
        },
        "security_health": {  # Placeholder - replace with actual data
            "ssl_enabled": False,
            "failed_logins": 0
        },
        "system_uptime": "24h 30m",  # Placeholder - replace with actual data
        "last_backup_time": None,  # Placeholder - replace with actual data
    }
    return render(request, "dashboard/admin_dashboard.html", context)


@login_required
def executive_dashboard(request):
    return render(request, "dashboard/executive_dashboard.html")


@login_required
def member_dashboard(request):
    return render(request, "dashboard/member_dashboard.html")


# ---------------------------
# User profile
# ---------------------------
@login_required
def profile(request):
    """
    Renders the user's profile page.
    """
    user_profile = None
    try:
        user_profile = request.user.memberprofile
    except MemberProfile.DoesNotExist:
        pass  # user may not have a MemberProfile yet

    context = {
        "user": request.user,
        "profile": user_profile,
    }
    return render(request, "accounts/profile.html", context)


# ---------------------------
# Class-based views for web interface
# ---------------------------
class UserCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """View for creating new users (staff only)"""
    model = User
    template_name = 'accounts/user_form.html'
    fields = ['email', 'first_name', 'last_name', 'user_type', 'is_active']
    success_url = reverse_lazy('accounts:admin_dashboard')
    
    def test_func(self):
        return self.request.user.is_staff
    
    def form_valid(self, form):
        # Generate a temporary password
        temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        user = form.save(commit=False)
        user.set_password(temp_password)
        user.save()
        
        # Create member profile for certain user types
        if user.user_type in ['member', 'executive']:
            MemberProfile.objects.create(user=user)
        
        messages.success(
            self.request, 
            f'User {user.email} created successfully. Temporary password: {temp_password}'
        )
        return super().form_valid(form)


class UserDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """View for viewing user details"""
    model = User
    template_name = 'accounts/user_detail.html'
    context_object_name = 'user_obj'
    
    def test_func(self):
        # Allow staff to view any user, or users to view their own profile
        user_obj = self.get_object()
        return self.request.user.is_staff or self.request.user.id == user_obj.id


class UserListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """View for listing all users (staff only)"""
    model = User
    template_name = 'accounts/user_list.html'
    context_object_name = 'users'
    paginate_by = 20
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get_queryset(self):
        return User.objects.all().order_by('-date_joined')


# ---------------------------
# User API
# ---------------------------
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action == "create":
            permission_classes = [permissions.AllowAny]
        elif self.action in ["update", "partial_update", "destroy"]:
            permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [p() for p in permission_classes]

    @action(detail=False)
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = UserRegistrationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        MemberProfile.objects.create(user=user)

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "user": UserSerializer(user).data,
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "message": "User registered successfully. Awaiting verification.",
            },
            status=status.HTTP_201_CREATED,
        )


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

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            permission_classes = [permissions.IsAuthenticated, IsChairperson]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [p() for p in permission_classes]

    @action(detail=False)
    def current(self, request):
        qs = ExecutiveCommittee.objects.filter(is_active=True).order_by("order")
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


class ChangePasswordView(generics.UpdateAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        if not user.check_password(serializer.validated_data["old_password"]):
            return Response(
                {"old_password": ["Wrong password."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(serializer.validated_data["new_password"])
        user.save()

        return Response(
            {"message": "Password updated successfully."},
            status=status.HTTP_200_OK,
        )
    
def about_view(request):
    return render(request, "base/about.html")

def donate(request):
    """Render a donation page."""
    return render(request, "accounts/donate.html")
