from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'finance'  # important for {% url 'finance:...' %}

# Create DRF router and disable format suffixes
router = DefaultRouter()
router.include_format_suffixes = False  # Prevent "drf_format_suffix already registered" error

# Register API viewsets
router.register(r'incomes', views.IncomeViewSet, basename='income')
router.register(r'expenses', views.ExpenseViewSet, basename='expense')
router.register(r'grants', views.GrantViewSet, basename='grant')
router.register(r'budgets', views.BudgetViewSet, basename='budget')

# Web interface URLs
urlpatterns = [
    # Web views
    path('transactions/', views.transaction_list, name='transaction_list'),
    path('income/create/', views.income_create, name='income_create'),
    path('expense/create/', views.expense_create, name='expense_create'),  # <-- new
    path('expense/create/', views.expense_create, name='expense_create'),
    path('budget/', views.budget_dashboard, name='budget_dashboard'),
    path('grant/create/', views.grant_create, name='grant_create'),
    
    # API routes
    path('api/', include((router.urls, 'finance'), namespace='finance')),

    # Extra API endpoint example (custom action on viewset)
    path(
        'financial-report/',
        views.BudgetViewSet.as_view({'get': 'financial_report'}),
        name='financial_report'
    ),
]
