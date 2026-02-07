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
    path('', include((router.urls, 'accounts'), namespace='accounts')),
    path('register/', views.UserRegistrationView.as_view(), name='register'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change-password'),
    #path('auth/', include('rest_framework.urls')),  # Optional DRF login/logout
]
