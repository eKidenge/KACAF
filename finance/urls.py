from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router and disable format suffixes
router = DefaultRouter()
router.include_format_suffixes = False  # ⚡ Prevent "drf_format_suffix already registered" error

# Register viewsets
router.register(r'incomes', views.IncomeViewSet, basename='income')
router.register(r'expenses', views.ExpenseViewSet, basename='expense')
router.register(r'grants', views.GrantViewSet, basename='grant')
router.register(r'budgets', views.BudgetViewSet, basename='budget')

# URL patterns
urlpatterns = [
    path('', include((router.urls, 'finance'), namespace='finance')),
    path(
        'financial-report/',
        views.BudgetViewSet.as_view({'get': 'financial_report'}),
        name='financial-report'
    ),
]
