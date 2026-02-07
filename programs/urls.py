from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router and disable format suffixes
router = DefaultRouter()
router.include_format_suffixes = False  # ⚡ Prevent "drf_format_suffix already registered" error

# Register all viewsets
router.register(r'programs', views.ProgramViewSet, basename='program')
router.register(r'projects', views.ProjectViewSet, basename='project')
router.register(r'tree-plantings', views.TreePlantingViewSet, basename='tree-planting')
router.register(r'trainings', views.TrainingViewSet, basename='training')

# Include router URLs
urlpatterns = [
    path('', include((router.urls, 'programs'), namespace='programs')),
]
