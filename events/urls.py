from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router and disable format suffixes
router = DefaultRouter()
router.include_format_suffixes = False

# Register all viewsets
router.register(r'events', views.EventViewSet, basename='event')
router.register(r'event-registrations', views.EventRegistrationViewSet, basename='event-registration')
router.register(r'event-photos', views.EventPhotoViewSet, basename='event-photo')
router.register(r'event-resources', views.EventResourceViewSet, basename='event-resource')

# Web interface URLs (add these BEFORE the router)
urlpatterns = [
    # Web views for templates
    path('events/', views.event_list, name='event_list'),
    path('events/calendar/', views.event_calendar, name='event_calendar'),
    path('public/dashboard/', views.public_dashboard, name='public_dashboard'),
    
    # API routes (router URLs)
    path('', include(router.urls)),
]

# Set the app_name (important for URL reversing)
app_name = 'events'