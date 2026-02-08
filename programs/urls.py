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

# Web interface URLs (add these BEFORE the router)
urlpatterns = [
    # Web views for templates
    path('programs/', views.program_list, name='program_list'),
    path('programs/create/', views.program_create, name='program_create'),  # ✅ Added create view
    path('dashboard/', views.program_dashboard, name='program_dashboard'),
    
    # API routes (router URLs)
    path('', include(router.urls)),
]

# Set the app_name (important for URL reversing)
app_name = 'programs'
