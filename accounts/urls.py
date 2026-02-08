from django.urls import path, include
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

    #path("", views.public_dashboard, name="home"),  # <-- this is for '/'
    path("home/", views.public_dashboard, name="public_dashboard"),  # <-- add this

    # Dashboards
    path("dashboard/", views.dashboard_redirect, name="dashboard"),
    path("dashboard/admin/", views.admin_dashboard, name="admin_dashboard"),
    path("dashboard/executive/", views.executive_dashboard, name="executive_dashboard"),
    path("dashboard/member/", views.member_dashboard, name="member_dashboard"),

    # About page
    path("about/", views.about_view, name="about"),

    # User profile
    path("profile/", views.profile, name="profile"),
    
    # User management (web interface)
    path("users/create/", views.UserCreateView.as_view(), name="user_create"),
    path("users/<int:pk>/", views.UserDetailView.as_view(), name="user_detail"),
    path("users/", views.UserListView.as_view(), name="user_list"),

    # Authentication
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="accounts/login.html"),
        name="login",
    ),
    path(
        "logout/",
        auth_views.LogoutView.as_view(next_page="/"),
        name="logout",
    ),
    path("register/", views.UserRegistrationView.as_view(), name="register"),
    path("change-password/", views.ChangePasswordView.as_view(), name="change-password"),

    # API endpoints via DRF router
    path("api/", include((router.urls, "accounts"), namespace="api")),

    path('donate/', views.donate, name='donate'),
]
