from django.urls import path
from . import views

app_name = 'pages'

urlpatterns = [
    path('', views.public_dashboard, name='public_dashboard'),  # Landing page
    path('dashboard/', views.dashboard, name='dashboard'),      # Role-based dashboard
]
