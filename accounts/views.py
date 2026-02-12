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
from .forms import UserRegistrationForm

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
    - Staff/Admin -> admin dashboard
    - Executive -> executive dashboard
    - Member -> member dashboard
    """
    if request.user.is_staff or request.user.is_superuser:
        return redirect('accounts:admin_dashboard')
    elif request.user.user_type == 'executive':
        return redirect('accounts:executive_dashboard')
    else:  # member or any other type
        return redirect('accounts:member_dashboard')


@login_required
def admin_dashboard(request):
    # Add context data for admin dashboard
    context = {
        "total_users": User.objects.count(),
        "verified_users": User.objects.filter(is_verified=True).count(),
        "regular_members": User.objects.filter(user_type='member').count(),
        "total_income": 0,
        "total_expenses": 0,
        "net_balance": 0,
        "total_programs": 0,
        "active_projects": 0,
        "total_trees": 0,
        "total_logins_today": 0,
        "storage_used": "0 MB",
        "error_logs_count": 0,
        "recent_activities": [],
        "pending_approvals": [],
        "system_alerts": [],
        "recent_users": User.objects.order_by('-date_joined')[:5],
        "today_income": 0,
        "weekly_income": 0,
        "monthly_income": 0,
        "financial_labels": [],
        "income_data": [],
        "expense_data": [],
        "server_health": {
            "status": "healthy",
            "cpu": 45,
            "memory": 60
        },
        "db_health": {
            "status": "healthy",
            "size": 1024 * 1024 * 10,
            "connections": 5,
            "tables": 15
        },
        "backup_health": {
            "last_successful": True,
            "last_backup": None,
            "next_backup": None
        },
        "security_health": {
            "ssl_enabled": False,
            "failed_logins": 0
        },
        "system_uptime": "24h 30m",
        "last_backup_time": None,
    }
    return render(request, "dashboard/admin_dashboard.html", context)


@login_required
def executive_dashboard(request):
    context = {
        "executive_members": ExecutiveCommittee.objects.filter(is_active=True),
        "pending_decisions": [],
        "upcoming_meetings": [],
        "reports": [],
    }
    return render(request, "dashboard/executive_dashboard.html", context)


@login_required
def member_dashboard(request):
    # Get member profile
    try:
        profile = request.user.memberprofile
    except MemberProfile.DoesNotExist:
        profile = None
    
    context = {
        "profile": profile,
        "membership_status": "Active" if request.user.is_active else "Inactive",
        "joined_date": request.user.date_joined,
        "contributions": 0,
        "programs_enrolled": [],
        "certificates": [],
    }
    return render(request, "dashboard/member_dashboard.html", context)


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
        pass

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
        temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        user = form.save(commit=False)
        user.set_password(temp_password)
        user.save()
        if user.user_type in ['member', 'executive']:
            MemberProfile.objects.create(user=user)
        messages.success(self.request, f'User {user.email} created successfully. Temporary password: {temp_password}')
        return super().form_valid(form)


class UserDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = User
    template_name = 'accounts/user_detail.html'
    context_object_name = 'user_obj'
    
    def test_func(self):
        user_obj = self.get_object()
        return self.request.user.is_staff or self.request.user.id == user_obj.id


class UserListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
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


# ---------------------------
# Registration view
# ---------------------------
def register_view(request):
    """
    Registration view for new members - uses Django Form for HTML template
    """
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            # Create the user
            user = form.save()
            
            # Create MemberProfile with all form data
            MemberProfile.objects.create(
                user=user,
                phone=form.cleaned_data.get('phone'),
                id_number=form.cleaned_data.get('id_number'),
                date_of_birth=form.cleaned_data.get('date_of_birth'),
                gender=form.cleaned_data.get('gender'),
                occupation=form.cleaned_data.get('occupation'),
                education_level=form.cleaned_data.get('education_level'),
                profile_picture=form.cleaned_data.get('profile_picture'),
                county=form.cleaned_data.get('county'),
                sub_county=form.cleaned_data.get('sub_county'),
                ward=form.cleaned_data.get('ward'),
                village=form.cleaned_data.get('village'),
                postal_address=form.cleaned_data.get('postal_address'),
                postal_code=form.cleaned_data.get('postal_code'),
                organization_name=form.cleaned_data.get('organization_name'),
                referral_source=form.cleaned_data.get('referral_source'),
                interests=form.cleaned_data.get('interests'),
                skills=form.cleaned_data.get('skills'),
                newsletter_subscription=form.cleaned_data.get('newsletter_subscription', False),
                terms_accepted=form.cleaned_data.get('terms_accepted', False),
                data_consent=form.cleaned_data.get('data_consent', False)
            )
            
            messages.success(request, "Registration successful! Please login.")
            return redirect('accounts:login')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserRegistrationForm()
    
    return render(request, "accounts/auth/register.html", {"form": form})


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

        return Response({"message": "Password updated successfully."}, status=status.HTTP_200_OK)
    

def about_view(request):
    return render(request, "base/about.html")


def donate(request):
    return render(request, "accounts/donate.html")


def terms_view(request):
    """Render the Terms and Conditions page"""
    return render(request, 'accounts/terms.html')

def privacy_view(request):
    """Render the Privacy Policy page"""
    return render(request, 'accounts/privacy.html')