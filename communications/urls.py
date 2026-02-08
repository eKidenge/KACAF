from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router and disable format suffixes
router = DefaultRouter()
router.include_format_suffixes = False  # ⚡ Prevent "drf_format_suffix already registered" error

# Register all viewsets
router.register(r'announcements', views.AnnouncementViewSet, basename='announcement')
router.register(r'newsletters', views.NewsletterViewSet, basename='newsletter')
router.register(r'feedback', views.FeedbackViewSet, basename='feedback')
router.register(r'contact-messages', views.ContactMessageViewSet, basename='contact-message')

# Web interface URLs (add these BEFORE the router)
urlpatterns = [
    # Web views for templates
    path('messages/', views.message_list, name='message_list'),
    path('dashboard/', views.communications_dashboard, name='communications_dashboard'),
    
    # ⚡ Added: web URL for creating announcements
    path('announcement/create/', views.announcement_create, name='announcement_create'),

    # API routes (router URLs)
    path('', include(router.urls)),
]

# Set the app_name (important for URL reversing)
app_name = 'communications'
