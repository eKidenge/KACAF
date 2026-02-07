from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router and disable DRF format suffixes
router = DefaultRouter()
router.include_format_suffixes = False  # Important: prevents "drf_format_suffix already registered" error

# Register all viewsets for this app
router.register(r'assemblies', views.GeneralAssemblyViewSet, basename='assembly')
router.register(r'resolutions', views.ResolutionViewSet, basename='resolution')
router.register(r'membership-applications', views.MembershipApplicationViewSet, basename='membership-application')
router.register(r'disciplinary-actions', views.DisciplinaryActionViewSet, basename='disciplinary-action')

# Include router URLs
urlpatterns = [
    path('', include((router.urls, 'governance'), namespace='governance')),
]
