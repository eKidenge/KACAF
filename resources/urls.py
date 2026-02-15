from django.urls import path
from . import views

app_name = 'resources'

urlpatterns = [
    path('', views.ResourceListView.as_view(), name='resource_list'),
    path('<slug:slug>/', views.ResourceDetailView.as_view(), name='resource_detail'),
    path('<slug:slug>/download/', views.download_resource, name='resource_download'),
    path('category/<slug:slug>/', views.CategoryDetailView.as_view(), name='category_detail'),
    path('collection/<slug:slug>/', views.CollectionDetailView.as_view(), name='collection_detail'),
]