from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router and disable format suffixes
router = DefaultRouter()
router.include_format_suffixes = False  # ⚡ Prevent "drf_format_suffix already registered" error

# Register all viewsets
router.register(r'events', views.EventViewSet, basename='event')
router.register(r'event-registrations', views.EventRegistrationViewSet, basename='event-registration')
router.register(r'event-photos', views.EventPhotoViewSet, basename='event-photo')
router.register(r'event-resources', views.EventResourceViewSet, basename='event-resource')

# Include router URLs with namespace
urlpatterns = [
    path('', include((router.urls, 'events'), namespace='events')),
]
