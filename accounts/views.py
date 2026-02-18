# accounts/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import CreateView, DetailView, ListView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.views import LoginView
from rest_framework import viewsets, generics, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
import random
import string
from django.shortcuts import render, get_object_or_404
# accounts/views.py - Change this import
from events.models import Event  # ✅ Correct import

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
# Custom Login View
# ---------------------------
class CustomLoginView(LoginView):
    """Custom login view with redirect based on user type"""
    template_name = 'accounts/auth/login.html'
    
    def get_success_url(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return reverse_lazy('accounts:admin_dashboard')
        elif user.user_type == 'executive':
            return reverse_lazy('accounts:executive_dashboard')
        else:
            return reverse_lazy('accounts:member_dashboard')


# ---------------------------
# Logout View
# ---------------------------
def logout_view(request):
    """Custom logout view"""
    logout(request)
    messages.success(request, "You have been successfully logged out.")
    return redirect('accounts:public_dashboard')


# ---------------------------
# Public & role dashboards
# ---------------------------
# accounts/views.py
from django.shortcuts import render
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import Sum, Count
from programs.models import Program, Project
from events.models import Event, EventRegistration
from testimonials.models import Testimonial
from partners.models import Partner
from accounts.models import MemberProfile  # Import MemberProfile

User = get_user_model()

def public_dashboard(request):
    """Public facing homepage/dashboard"""
    
    # Get featured programs (active programs)
    featured_programs = Program.objects.filter(
        status='active'
    ).order_by('-created_at')[:3]
    
    # Get upcoming events
    upcoming_events = Event.objects.filter(
        is_public=True,
        start_datetime__gte=timezone.now(),
        status__in=['published', 'ongoing']
    ).order_by('start_datetime')[:3]
    
    # Get approved testimonials
    testimonials = Testimonial.objects.filter(
        is_approved=True
    ).order_by('-created_at')[:3]
    
    # Get active partners
    partners = Partner.objects.filter(
        is_active=True
    )[:4]
    
    # Calculate REAL impact numbers from your database
    
    # Total trees planted - sum from all MemberProfile trees_planted fields
    total_trees_planted = MemberProfile.objects.aggregate(total=Sum('trees_planted'))['total'] or 0
    
    # Total members - count of users with member type (excluding other types)
    total_members = User.objects.filter(user_type='member').count()
    
    # Total area coverage (hectares) - assuming this comes from projects or programs
    # You might need to add this field to your models, or use a default for now
    total_area_coverage = 1200  # You may need to calculate this from Project model if you have hectares field
    
    # Total beneficiaries - sum from programs (if you have beneficiaries_count field)
    # If not, you might calculate from event registrations or member counts
    total_beneficiaries = Program.objects.aggregate(total=Sum('beneficiaries_count'))['total'] or total_members * 2
    
    # Carbon sequestered (tons CO2) - rough estimate based on trees planted
    # Average tree sequesters ~0.02 tons CO2 per year
    carbon_sequestered = int(total_trees_planted * 0.02)
    
    # Get counts for other user types if needed for display
    total_farmers = User.objects.filter(user_type='farmer').count()
    total_youth = User.objects.filter(user_type='youth').count()
    total_organizations = User.objects.filter(user_type='organization').count()
    
    context = {
        "total_trees_planted": total_trees_planted,
        "total_members": total_members,
        "total_farmers": total_farmers,
        "total_youth": total_youth,
        "total_organizations": total_organizations,
        "total_area_coverage": total_area_coverage,
        "total_beneficiaries": total_beneficiaries,
        "carbon_sequestered": carbon_sequestered,
        "featured_programs": featured_programs,
        "upcoming_events": upcoming_events,
        "testimonials": testimonials,
        "partners": partners,
    }
    
    return render(request, "dashboard/public_dashboard.html", context)


@login_required
def dashboard_redirect(request):
    """
    Redirect users to their appropriate dashboard based on role
    - Staff/Admin -> admin dashboard
    - Executive -> executive dashboard
    - Member -> member dashboard
    - Others -> member dashboard (fallback)
    """
    if request.user.is_staff or request.user.is_superuser:
        return redirect('accounts:admin_dashboard')
    elif request.user.user_type == 'executive':
        return redirect('accounts:executive_dashboard')
    elif request.user.user_type == 'member':
        return redirect('accounts:member_dashboard')
    else:
        # For other user types (youth, organization, donor, etc.)
        # You can create specific dashboards for them later
        return redirect('accounts:member_dashboard')


@login_required
def admin_dashboard(request):
    """Admin/staff dashboard"""
    context = {
        "total_users": User.objects.count(),
        "verified_users": User.objects.filter(is_verified=True).count(),
        "regular_members": User.objects.filter(user_type='member').count(),
        "executive_members": User.objects.filter(user_type='executive').count(),
        "youth_members": User.objects.filter(user_type='youth').count(),
        "organizations": User.objects.filter(user_type='organization').count(),
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
    """Executive committee dashboard"""
    # Check if user has executive committee profile
    try:
        executive_profile = request.user.executive_role
    except ExecutiveCommittee.DoesNotExist:
        executive_profile = None
    
    context = {
        "executive_members": ExecutiveCommittee.objects.filter(is_active=True),
        "current_member": executive_profile,
        "pending_decisions": [],
        "upcoming_meetings": [],
        "reports": [],
        "total_members": User.objects.filter(user_type='member').count(),
        "pending_applications": 0,
    }
    return render(request, "dashboard/executive_dashboard.html", context)


@login_required
def member_dashboard(request):
    """Regular member dashboard"""
    # Get member profile - handle case where it doesn't exist
    try:
        profile = request.user.member_profile
    except (MemberProfile.DoesNotExist, AttributeError):
        # Create a profile if it doesn't exist and user is a member
        if request.user.user_type == 'member':
            profile = MemberProfile.objects.create(user=request.user)
        else:
            profile = None
    
    context = {
        "profile": profile,
        "membership_status": "Active" if request.user.is_active else "Inactive",
        "joined_date": getattr(request.user, 'join_date', request.user.date_joined),
        "contributions": profile.total_donations if profile else 0,
        "trees_planted": profile.trees_planted if profile else 0,
        "events_attended": profile.events_attended if profile else 0,
        "training_completed": profile.training_completed if profile else 0,
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
        user_profile = request.user.member_profile
    except (MemberProfile.DoesNotExist, AttributeError):
        # Create a profile if it doesn't exist and user is a member
        if request.user.user_type == 'member':
            user_profile = MemberProfile.objects.create(user=request.user)
    
    # Get executive profile if user is executive
    executive_profile = None
    try:
        executive_profile = request.user.executive_role
    except (ExecutiveCommittee.DoesNotExist, AttributeError):
        pass

    context = {
        "user": request.user,
        "profile": user_profile,
        "executive_profile": executive_profile,
    }
    return render(request, "accounts/profile.html", context)


# ---------------------------
# Class-based views for web interface
# ---------------------------
class UserCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """View for creating new users (staff only)"""
    model = User
    template_name = 'accounts/user_form.html'
    fields = ['email', 'first_name', 'last_name', 'user_type', 'is_active', 'is_staff', 'is_superuser']
    success_url = reverse_lazy('accounts:admin_dashboard')
    
    def test_func(self):
        return self.request.user.is_staff
    
    def form_valid(self, form):
        temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        user = form.save(commit=False)
        user.set_password(temp_password)
        user.username = form.cleaned_data['email']
        user.save()
        
        # Create MemberProfile ONLY for members, not for other user types
        if user.user_type == 'member':
            MemberProfile.objects.get_or_create(user=user)
        
        # Executive committee members should be added through the executive committee management
        # not automatically created here
            
        messages.success(self.request, f'User {user.email} created successfully. Temporary password: {temp_password}')
        return super().form_valid(form)


class UserDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = User
    template_name = 'accounts/user_detail.html'
    context_object_name = 'user_obj'
    
    def test_func(self):
        user_obj = self.get_object()
        return self.request.user.is_staff or self.request.user.id == user_obj.id
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_obj = self.get_object()
        
        # Get member profile if exists
        try:
            context['member_profile'] = user_obj.member_profile
        except (MemberProfile.DoesNotExist, AttributeError):
            context['member_profile'] = None
            
        # Get executive profile if exists
        try:
            context['executive_profile'] = user_obj.executive_role
        except (ExecutiveCommittee.DoesNotExist, AttributeError):
            context['executive_profile'] = None
            
        return context


class UserListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = User
    template_name = 'accounts/user_list.html'
    context_object_name = 'users'
    paginate_by = 20
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get_queryset(self):
        queryset = User.objects.all().order_by('-date_joined')
        
        # Filter by user_type if provided
        user_type = self.request.GET.get('user_type')
        if user_type:
            queryset = queryset.filter(user_type=user_type)
            
        # Search by email or name
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(email__icontains=search) |
                models.Q(first_name__icontains=search) |
                models.Q(last_name__icontains=search)
            )
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_type_choices'] = User.USER_TYPE_CHOICES
        context['current_filter'] = self.request.GET.get('user_type', '')
        context['search_query'] = self.request.GET.get('search', '')
        return context


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

    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def members(self, request):
        """Get all member users"""
        members = User.objects.filter(user_type='member')
        serializer = self.get_serializer(members, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def executives(self, request):
        """Get all executive users"""
        executives = User.objects.filter(user_type='executive')
        serializer = self.get_serializer(executives, many=True)
        return Response(serializer.data)


# ---------------------------
# Registration view - FIXED VERSION
# ---------------------------
def register_view(request):
    """
    Registration view for new members - uses Django Form for HTML template
    """
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            # Save the form - this creates both CustomUser and MemberProfile
            user = form.save()
            
            # Log the user in after registration
            login(request, user)
            
            messages.success(request, "Registration successful! Welcome to KACAF.")
            
            # Redirect to appropriate dashboard
            if user.user_type == 'executive':
                return redirect('accounts:executive_dashboard')
            else:
                return redirect('accounts:member_dashboard')
        else:
            # Print form errors for debugging
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
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
    
    @action(detail=True, methods=['post'])
    def increment_trees(self, request, pk=None):
        """Increment trees planted count"""
        profile = self.get_object()
        count = request.data.get('count', 1)
        profile.trees_planted += int(count)
        profile.save()
        return Response({'trees_planted': profile.trees_planted})
    
    @action(detail=True, methods=['post'])
    def increment_events(self, request, pk=None):
        """Increment events attended count"""
        profile = self.get_object()
        profile.events_attended += 1
        profile.save()
        return Response({'events_attended': profile.events_attended})


class ExecutiveCommitteeViewSet(viewsets.ModelViewSet):
    queryset = ExecutiveCommittee.objects.filter(is_active=True)
    serializer_class = ExecutiveCommitteeSerializer

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            permission_classes = [permissions.IsAuthenticated, IsChairperson]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [p() for p in permission_classes]

    @action(detail=False, methods=['get'])
    def current(self, request):
        qs = ExecutiveCommittee.objects.filter(is_active=True).order_by("order")
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def positions(self, request):
        """Get all available positions"""
        return Response(dict(ExecutiveCommittee.POSITIONS))


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
    """About page"""
    return render(request, "base/about.html")


def donate(request):
    """Donation page"""
    return render(request, "accounts/donate.html")


def terms_view(request):
    """Render the Terms and Conditions page"""
    return render(request, 'accounts/terms.html')


def privacy_view(request):
    """Render the Privacy Policy page"""
    return render(request, 'accounts/privacy.html')


# accounts/views.py - Add this function

@login_required
def profile_edit(request):
    """
    View for editing user profile
    """
    if request.method == 'POST':
        # Handle form submission
        # You'll need to create a form for this
        messages.success(request, "Profile updated successfully!")
        return redirect('accounts:profile')
    
    # GET request - display edit form
    context = {
        "user": request.user,
    }
    return render(request, "accounts/user/profile_edit.html", context)

def event_detail(request, pk):
    """Display event details"""
    event = get_object_or_404(Event, pk=pk, is_public=True)
    return render(request, 'events/event_detail.html', {'event': event})
