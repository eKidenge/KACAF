from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router and disable format suffixes
router = DefaultRouter()
router.include_format_suffixes = False  # ⚡ Prevent "drf_format_suffix already registered" error

# Register viewsets
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'profiles', views.MemberProfileViewSet, basename='profile')
router.register(r'executive-committee', views.ExecutiveCommitteeViewSet, basename='executive-committee')

# URL patterns
urlpatterns = [
    # Traditional Django views (for HTML templates)
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('settings/', views.settings, name='settings'),
    path('user-list/', views.user_list, name='user_list'),
    
    # API endpoints (keep existing router)
    path('', include((router.urls, 'accounts'), namespace='api')),
    path('register/', views.UserRegistrationView.as_view(), name='register'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change-password'),
    
    # Optional: Include DRF auth URLs if needed
    # path('auth/', include('rest_framework.urls')),  # Optional DRF login/logout
]

# Add app namespace
app_name = 'accounts'