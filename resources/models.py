from django.db import models
from django.utils import timezone
from django.urls import reverse

class ResourceCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, help_text="Font Awesome icon class", default="fa-file")
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Resource Categories"
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('resources:category_detail', args=[self.slug])

class Resource(models.Model):
    RESOURCE_TYPES = [
        ('guide', 'Guide/Manual'),
        ('toolkit', 'Toolkit'),
        ('report', 'Report'),
        ('case_study', 'Case Study'),
        ('policy', 'Policy Brief'),
        ('training', 'Training Material'),
        ('video', 'Video'),
        ('infographic', 'Infographic'),
        ('other', 'Other'),
    ]
    
    AUDIENCE = [
        ('farmers', 'Farmers'),
        ('youth', 'Youth'),
        ('members', 'All Members'),
        ('staff', 'Staff'),
        ('public', 'General Public'),
    ]
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(ResourceCategory, on_delete=models.CASCADE, related_name='resources')
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPES, default='guide')
    description = models.TextField()
    
    # File or link
    file = models.FileField(upload_to='resources/', blank=True, null=True)
    external_link = models.URLField(blank=True, null=True, help_text="External URL if no file")
    
    # Metadata
    audience = models.CharField(max_length=20, choices=AUDIENCE, default='public')
    author = models.CharField(max_length=200, blank=True)
    organization = models.CharField(max_length=200, blank=True)
    publish_date = models.DateField(default=timezone.now)
    
    # Stats
    downloads = models.IntegerField(default=0)
    views = models.IntegerField(default=0)
    
    # Status
    is_featured = models.BooleanField(default=False)
    is_published = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_featured', '-publish_date']
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('resources:resource_detail', args=[self.slug])
    
    def get_download_url(self):
        return reverse('resources:resource_download', args=[self.slug])

class ResourceCollection(models.Model):
    """For grouping resources (e.g., Farmer Training Pack)"""
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    cover_image = models.ImageField(upload_to='collections/', blank=True, null=True)
    resources = models.ManyToManyField(Resource, related_name='collections')
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('resources:collection_detail', args=[self.slug])