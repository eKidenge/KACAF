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

# Include router URLs with namespace
urlpatterns = [
    path('', include((router.urls, 'documents'), namespace='documents')),
]
