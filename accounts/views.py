from django.shortcuts import render, redirect  # Added redirect import
from django.contrib.auth import get_user_model
from rest_framework import viewsets, generics, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.decorators import login_required

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
    return render(request, "dashboard/admin_dashboard.html")


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