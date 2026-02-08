from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'governance'  # important for {% url 'governance:...' %}

# DRF router for API endpoints
router = DefaultRouter()
router.include_format_suffixes = False

# Register viewsets
router.register(r'assemblies', views.GeneralAssemblyViewSet, basename='assembly')
router.register(r'resolutions', views.ResolutionViewSet, basename='resolution')
router.register(r'membership-applications', views.MembershipApplicationViewSet, basename='membership-application')
router.register(r'disciplinary-actions', views.DisciplinaryActionViewSet, basename='disciplinary-action')

# Web interface URLs
urlpatterns = [
    # Web views
    path('membership/apply/', views.membership_application_create, name='membership_application_create'),
    path('membership/', views.membership_dashboard, name='membership_dashboard'),
    path('assemblies/create/', views.assembly_create, name='assembly_create'),

    # API routes
    path('api/', include(router.urls)),
]
