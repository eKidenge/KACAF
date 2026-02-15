from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, Http404
from django.db.models import Q, Count
import os
from .models import Resource, ResourceCategory, ResourceCollection

class ResourceListView(ListView):
    model = Resource
    template_name = 'resources/resource_list.html'
    context_object_name = 'resources'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Resource.objects.filter(is_published=True)
        
        # Filter by category
        category_slug = self.request.GET.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        
        # Filter by type
        resource_type = self.request.GET.get('type')
        if resource_type:
            queryset = queryset.filter(resource_type=resource_type)
        
        # Filter by audience
        audience = self.request.GET.get('audience')
        if audience:
            queryset = queryset.filter(audience=audience)
        
        # Search
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) | 
                Q(description__icontains=query) |
                Q(author__icontains=query)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = ResourceCategory.objects.filter(
            resources__is_published=True
        ).annotate(
            resource_count=Count('resources')
        ).order_by('order')
        context['featured_resources'] = Resource.objects.filter(
            is_published=True, 
            is_featured=True
        )[:6]
        context['collections'] = ResourceCollection.objects.filter(
            is_published=True
        )[:3]
        return context

class ResourceDetailView(DetailView):
    model = Resource
    template_name = 'resources/resource_detail.html'
    context_object_name = 'resource'
    
    def get_object(self):
        resource = super().get_object()
        # Increment view count
        resource.views += 1
        resource.save(update_fields=['views'])
        return resource
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['related_resources'] = Resource.objects.filter(
            is_published=True,
            category=self.object.category
        ).exclude(id=self.object.id)[:3]
        return context

def download_resource(request, slug):
    resource = get_object_or_404(Resource, slug=slug, is_published=True)
    
    if not resource.file:
        raise Http404("No file available for download")
    
    # Increment download count
    resource.downloads += 1
    resource.save(update_fields=['downloads'])
    
    # Serve file
    response = HttpResponse(resource.file, content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="{os.path.basename(resource.file.name)}"'
    return response

class CategoryDetailView(DetailView):
    model = ResourceCategory
    template_name = 'resources/category_detail.html'
    context_object_name = 'category'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['resources'] = Resource.objects.filter(
            category=self.object,
            is_published=True
        )
        return context

class CollectionDetailView(DetailView):
    model = ResourceCollection
    template_name = 'resources/collection_detail.html'
    context_object_name = 'collection'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['resources'] = self.object.resources.filter(is_published=True)
        return context