# accounts/urls.py
from django.urls import path, include
from django.urls import path, include, reverse_lazy  # Add reverse_lazy here
from rest_framework.routers import DefaultRouter
from django.contrib.auth import views as auth_views
from . import views

app_name = "accounts"

# ---------------------------
# DRF Router for API endpoints
# ---------------------------
router = DefaultRouter()
router.include_format_suffixes = False

router.register(r"users", views.UserViewSet, basename="user")
router.register(r"profiles", views.MemberProfileViewSet, basename="profile")
router.register(
    r"executive-committee",
    views.ExecutiveCommitteeViewSet,
    basename="executive-committee",
)

# ---------------------------
# URL Patterns
# ---------------------------
urlpatterns = [
    # Public home
    path("", views.public_dashboard, name="home"),
    path("home/", views.public_dashboard, name="public_dashboard"),

    # Dashboards
    path("dashboard/", views.dashboard_redirect, name="dashboard"),
    path("dashboard/admin/", views.admin_dashboard, name="admin_dashboard"),
    path("dashboard/executive/", views.executive_dashboard, name="executive_dashboard"),
    path("dashboard/member/", views.member_dashboard, name="member_dashboard"),

    # About page
    path("about/", views.about_view, name="about"),

        # User profile
    path("profile/", views.profile, name="profile"),
    #path("profile/edit/", views.profile_edit, name="profile_edit"),  # ADD THIS LINE
    path("user/profile_edit/", views.profile_edit, name="profile_edit"),  # ADD THIS LINE

    # User management (web interface)
    path("users/create/", views.UserCreateView.as_view(), name="user_create"),
    path("users/<int:pk>/", views.UserDetailView.as_view(), name="user_detail"),
    path("users/", views.UserListView.as_view(), name="user_list"),

    # Authentication
    path(
        "login/",
        views.CustomLoginView.as_view(),  # Use custom login view
        name="login",
    ),
    path(
        "logout/",
        views.logout_view,  # Use custom logout view
        name="logout",
    ),
    path("register/", views.register_view, name="register"),
    path("change-password/", views.ChangePasswordView.as_view(), name="change-password"),

    # Password reset URLs
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="accounts/auth/password_reset_form.html",
            email_template_name="accounts/auth/password_reset_email.html",
            subject_template_name="accounts/auth/password_reset_subject.txt",
            success_url=reverse_lazy('accounts:password_reset_done')
        ),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="accounts/auth/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="accounts/auth/password_reset_confirm.html",
            success_url=reverse_lazy('accounts:password_reset_complete')
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="accounts/auth/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),

    # API endpoints via DRF router
    path("api/", include((router.urls, "accounts"), namespace="api")),

    # Other pages
    path('donate/', views.donate, name='donate'),
    path('terms/', views.terms_view, name='terms'),
    path('privacy/', views.privacy_view, name='privacy'),
]