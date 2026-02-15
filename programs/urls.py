from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# API Router
router = DefaultRouter()
router.register(r'programs', views.ProgramViewSet, basename='program')
router.register(r'projects', views.ProjectViewSet, basename='project')
router.register(r'tree-plantings', views.TreePlantingViewSet, basename='tree-planting')
router.register(r'trainings', views.TrainingViewSet, basename='training')

urlpatterns = [
    # Web Views
    path('', views.web_program_list, name='program_list'),
    path('dashboard/', views.web_program_dashboard, name='program_dashboard'),
    path('create/', views.web_program_create, name='program_create'),
    path('<int:pk>/', views.web_program_detail, name='program_detail'),
    path('<int:pk>/edit/', views.web_program_edit, name='program_edit'),
    path('my-trees/', views.web_my_trees, name='my_trees'),
    path('trees/add/', views.web_add_tree_planting, name='add_tree_planting'),
    path('trees/<int:pk>/', views.web_tree_detail, name='tree_detail'),
    path('trees/<int:pk>/update-survival/', views.web_update_tree_survival, name='update_tree_survival'),
    path('<int:pk>/report/', views.program_report, name='program_report'),
    path('<int:pk>/join/', views.web_program_join, name='program_join'),
    path('public-dashboard/', views.public_dashboard, name='public_dashboard'),
    # API Views
    path('api/', include(router.urls)),
]

app_name = 'programs'