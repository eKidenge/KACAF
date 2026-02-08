from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router and disable format suffixes
router = DefaultRouter()
router.include_format_suffixes = False  # ⚡ Prevent "drf_format_suffix already registered" error

# Register all viewsets
router.register(r'categories', views.DocumentCategoryViewSet, basename='document-category')
router.register(r'documents', views.DocumentViewSet, basename='document')
router.register(r'document-reviews', views.DocumentReviewViewSet, basename='document-review')
router.register(r'templates', views.DocumentTemplateViewSet, basename='document-template')

# Web interface URLs (add these BEFORE the router)
urlpatterns = [
    # Web views for templates
    path('documents/', views.document_list, name='document_list'),
    path('dashboard/', views.document_dashboard, name='document_dashboard'),
    
    # API routes (router URLs)
    path('', include(router.urls)),
]

# Set the app_name (important for URL reversing)
app_name = 'documents'