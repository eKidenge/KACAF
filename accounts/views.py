# accounts/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import CreateView, DetailView, ListView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.utils import timezone
from django.db.models import Sum, Count, Q
from rest_framework import viewsets, generics, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
import random
import string
import json

from events.models import Event, EventRegistration
from programs.models import Program, Project, TreePlanting
from testimonials.models import Testimonial
from partners.models import Partner

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
def public_dashboard(request):
    """Public facing homepage/dashboard"""

    featured_programs = Program.objects.filter(
        status='active'
    ).order_by('-created_at')[:3]

    upcoming_events = Event.objects.filter(
        is_public=True,
        start_datetime__gte=timezone.now(),
        status__in=['published', 'ongoing']
    ).order_by('start_datetime')[:3]

    testimonials = Testimonial.objects.all().order_by('-created_at')[:3]
    partners = Partner.objects.all()[:4]

    total_trees_planted = MemberProfile.objects.aggregate(
        total=Sum('trees_planted')
    )['total'] or 0

    total_members = User.objects.filter(user_type='member').count()
    total_area_coverage = 1200

    total_beneficiaries = Program.objects.aggregate(
        total=Sum('beneficiaries_reached')
    )['total'] or total_members * 2

    carbon_sequestered = int(total_trees_planted * 0.02)

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
    """Redirect users to their appropriate dashboard based on role"""
    if request.user.is_staff or request.user.is_superuser:
        return redirect('accounts:admin_dashboard')
    elif request.user.user_type == 'executive':
        return redirect('accounts:executive_dashboard')
    elif request.user.user_type == 'member':
        return redirect('accounts:member_dashboard')
    else:
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
    """Regular member dashboard — supplies every variable the template expects."""
    # Get or create the member profile
    profile, _ = MemberProfile.objects.get_or_create(user=request.user)

    now = timezone.now()

    # ---- Trees ----
    tree_qs = TreePlanting.objects.filter(farmer=request.user)
    user_trees_count = tree_qs.aggregate(total=Sum('quantity'))['total'] or 0

    monthly_trees = tree_qs.filter(
        planting_date__year=now.year,
        planting_date__month=now.month
    ).aggregate(total=Sum('quantity'))['total'] or 0

    yearly_trees = tree_qs.filter(
        planting_date__year=now.year
    ).aggregate(total=Sum('quantity'))['total'] or 0

    # Survival rate = average of survival_rate across the user's plantings
    survival_agg = tree_qs.aggregate(
        total_rate=Sum('survival_rate'),
        count=Count('id')
    )
    if survival_agg['count']:
        user_trees_survival_rate = round(
            survival_agg['total_rate'] / survival_agg['count']
        )
    else:
        user_trees_survival_rate = 0

    # Carbon: ~0.02 tons CO2 per tree per year; ~4.6 tons per car per year
    carbon_sequestration = round(float(user_trees_count) * 0.02, 2)
    equivalent_cars = round(carbon_sequestration / 4.6, 1)

    # Species chart data — must be JSON-encoded strings for Chart.js
    species_qs = (
        tree_qs.values('species')
        .annotate(n=Sum('quantity'))
        .order_by('-n')
    )
    tree_species_labels = json.dumps([s['species'] or 'Unknown' for s in species_qs])
    tree_species_data = json.dumps([s['n'] for s in species_qs])

    # ---- Events ----
    registrations = EventRegistration.objects.filter(user=request.user)
    registered_events = registrations.count()
    registered_events_list = list(registrations.values_list('event_id', flat=True))

    upcoming_events_qs = Event.objects.filter(
        is_public=True,
        start_datetime__gte=now,
        status__in=['published', 'ongoing'],
    ).order_by('start_datetime')[:5]

    upcoming_events_count = upcoming_events_qs.count()

    # 'attended' may not exist on EventRegistration; guard it
    attended_events = 0
    if hasattr(EventRegistration, 'attended'):
        attended_events = registrations.filter(attended=True).count()

    # ---- Contributions ----
    total_contributions = getattr(profile, 'total_donations', 0) or 0
    volunteer_hours = getattr(profile, 'volunteer_hours', 0) or 0
    training_completed = getattr(profile, 'training_completed', 0) or 0

    # ---- Level system ----
    tree_points = min(user_trees_count, 50)
    event_points = min(attended_events * 2, 20)
    training_points = min(training_completed * 3, 30)
    current_points = tree_points + event_points + training_points

    LEVELS = [
        (0, 'Seedling'),
        (25, 'Sapling'),
        (50, 'Young Tree'),
        (75, 'Mature Tree'),
        (100, 'Forest Guardian'),
    ]

    user_level = 1
    user_level_title = LEVELS[0][1]
    next_level_points = LEVELS[1][0]

    for i, (threshold, title) in enumerate(LEVELS):
        if current_points >= threshold:
            user_level = i + 1
            user_level_title = title
            if i + 1 < len(LEVELS):
                next_level_points = LEVELS[i + 1][0]
            else:
                next_level_points = threshold

    if next_level_points and current_points < next_level_points:
        level_progress = min(100, int((current_points / next_level_points) * 100))
    else:
        level_progress = 100

    # ---- Recent activity ----
    recent_activities = []
    for tp in tree_qs.order_by('-created_at')[:3]:
        recent_activities.append({
            'title': f'Planted {tp.quantity} × {tp.species}',
            'description': tp.planting_site,
            'timestamp': tp.created_at,
            'type': 'tree_planting',
        })

    # ---- Announcements (optional) ----
    announcements = []
    try:
        from communications.models import Announcement
        announcements = Announcement.objects.order_by('-publish_date')[:3]
    except Exception:
        announcements = []

    context = {
        'profile': profile,

        # Trees & impact
        'user_trees_count': user_trees_count,
        'monthly_trees': monthly_trees,
        'yearly_trees': yearly_trees,
        'recent_trees_count': monthly_trees,
        'user_trees_survival_rate': user_trees_survival_rate,
        'carbon_sequestration': carbon_sequestration,
        'equivalent_cars': equivalent_cars,
        'tree_species_labels': tree_species_labels,
        'tree_species_data': tree_species_data,

        # Events
        'registered_events': registered_events,
        'registered_events_list': registered_events_list,
        'upcoming_events': upcoming_events_qs,
        'upcoming_events_count': upcoming_events_count,
        'attended_events': attended_events,

        # Contributions
        'total_contributions': total_contributions,
        'volunteer_hours': volunteer_hours,

        # Level / gamification
        'user_level': user_level,
        'user_level_title': user_level_title,
        'current_points': current_points,
        'next_level_points': next_level_points,
        'level_progress': level_progress,
        'tree_points': tree_points,
        'event_points': event_points,
        'training_points': training_points,

        # Lists
        'recent_activities': recent_activities,
        'achievements': [],
        'announcements': announcements,
    }
    return render(request, "dashboard/member_dashboard.html", context)


# ---------------------------
# User profile
# ---------------------------
@login_required
def profile(request):
    """Renders the user's profile page."""
    user_profile = None
    try:
        user_profile = request.user.member_profile
    except (MemberProfile.DoesNotExist, AttributeError):
        if request.user.user_type == 'member':
            user_profile = MemberProfile.objects.create(user=request.user)

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
    fields = ['email', 'first_name', 'last_name', 'user_type',
              'is_active', 'is_staff', 'is_superuser']
    success_url = reverse_lazy('accounts:admin_dashboard')

    def test_func(self):
        return self.request.user.is_staff

    def form_valid(self, form):
        temp_password = ''.join(
            random.choices(string.ascii_letters + string.digits, k=10)
        )
        user = form.save(commit=False)
        user.set_password(temp_password)
        user.username = form.cleaned_data['email']
        user.save()

        if user.user_type == 'member':
            MemberProfile.objects.get_or_create(user=user)

        messages.success(
            self.request,
            f'User {user.email} created successfully. Temporary password: {temp_password}'
        )
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

        try:
            context['member_profile'] = user_obj.member_profile
        except (MemberProfile.DoesNotExist, AttributeError):
            context['member_profile'] = None

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

        user_type = self.request.GET.get('user_type')
        if user_type:
            queryset = queryset.filter(user_type=user_type)

        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
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
        members = User.objects.filter(user_type='member')
        serializer = self.get_serializer(members, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def executives(self, request):
        executives = User.objects.filter(user_type='executive')
        serializer = self.get_serializer(executives, many=True)
        return Response(serializer.data)


# ---------------------------
# Registration view
# ---------------------------
def register_view(request):
    """
    Registration view for new members.

    After successful registration we send the user to the login page
    (rather than an empty dashboard) so they can log in cleanly.
    """
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            messages.success(
                request,
                "Registration successful! Please log in to continue."
            )
            return redirect('accounts:login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = UserRegistrationForm()

    return render(request, "accounts/auth/register.html", {"form": form})


# ---------------------------
# API view sets
# ---------------------------
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
        profile = self.get_object()
        count = request.data.get('count', 1)
        profile.trees_planted += int(count)
        profile.save()
        return Response({'trees_planted': profile.trees_planted})

    @action(detail=True, methods=['post'])
    def increment_events(self, request, pk=None):
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

        return Response(
            {"message": "Password updated successfully."},
            status=status.HTTP_200_OK
        )


# ---------------------------
# Static pages
# ---------------------------
def about_view(request):
    return render(request, "base/about.html")


def donate(request):
    return render(request, "accounts/donate.html")


def terms_view(request):
    return render(request, 'accounts/terms.html')


def privacy_view(request):
    return render(request, 'accounts/privacy.html')


@login_required
def profile_edit(request):
    """View for editing user profile"""
    if request.method == 'POST':
        messages.success(request, "Profile updated successfully!")
        return redirect('accounts:profile')

    context = {"user": request.user}
    return render(request, "accounts/user/profile_edit.html", context)


def event_detail(request, pk):
    """Display event details"""
    event = get_object_or_404(Event, pk=pk, is_public=True)
    return render(request, 'events/event_detail.html', {'event': event})
