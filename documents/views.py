from django.db.models import Q, Count
from django.utils import timezone
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import DocumentCategory, Document, DocumentAccessLog, DocumentReview, DocumentTemplate
from .serializers import (
    DocumentCategorySerializer, DocumentSerializer,
    DocumentReviewSerializer, DocumentTemplateSerializer,
    DocumentAccessSerializer
)
from .permissions import CanAccessDocument


class DocumentCategoryViewSet(viewsets.ModelViewSet):
    queryset = DocumentCategory.objects.all()
    serializer_class = DocumentCategorySerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    @action(detail=True, methods=['get'])
    def documents(self, request, pk=None):
        category = self.get_object()
        documents = category.documents.filter(is_active=True)
        
        # Filter by access level
        user = request.user
        if user.is_staff or user.user_type == 'executive':
            documents = documents.all()
        elif user.is_authenticated:
            documents = documents.exclude(access_level='confidential')
        else:
            documents = documents.filter(access_level='public')
        
        serializer = DocumentSerializer(documents, many=True, context={'request': request})
        return Response(serializer.data)


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.filter(is_active=True)
    serializer_class = DocumentSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['document_type', 'category', 'status', 'access_level', 'program', 'project', 'event']
    search_fields = ['title', 'description', 'tags', 'keywords']
    ordering_fields = ['title', 'created_at', 'download_count', 'effective_date']
    permission_classes = [permissions.IsAuthenticated, CanAccessDocument]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Apply access level filtering
        if user.is_staff or user.user_type == 'executive':
            return queryset
        elif user.is_authenticated:
            return queryset.exclude(access_level='confidential')
        else:
            return queryset.filter(access_level='public')
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Log view access
        if request.user.is_authenticated:
            DocumentAccessLog.objects.create(
                document=instance,
                user=request.user,
                access_type='view',
                ip_address=self.get_client_ip(request)
            )
            
            # Update view count
            instance.view_count += 1
            instance.last_viewed = timezone.now()
            instance.save()
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        document = self.get_object()
        
        # Check download permission
        if not self.check_download_permission(request.user, document):
            return Response({'error': 'Not authorized to download this document.'}, status=status.HTTP_403_FORBIDDEN)
        
        # Log download access
        if request.user.is_authenticated:
            DocumentAccessLog.objects.create(
                document=document,
                user=request.user,
                access_type='download',
                ip_address=self.get_client_ip(request)
            )
            
            # Update download count
            document.download_count += 1
            document.last_downloaded = timezone.now()
            document.save()
        
        # Return file URL
        return Response({
            'download_url': request.build_absolute_uri(document.file.url),
            'filename': document.file.name.split('/')[-1],
            'file_size': document.file_size,
            'file_format': document.file_format
        })
    
    @action(detail=True, methods=['get'])
    def access_logs(self, request, pk=None):
        document = self.get_object()
        if not request.user.is_staff and request.user.user_type != 'executive':
            return Response({'error': 'Not authorized.'}, status=status.HTTP_403_FORBIDDEN)
        
        logs = document.access_logs.all()[:100]  # Limit to recent 100
        data = [
            {
                'user': log.user.get_full_name() if log.user else 'Anonymous',
                'access_type': log.access_type,
                'accessed_at': log.accessed_at,
                'ip_address': log.ip_address
            }
            for log in logs
        ]
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def expired(self, request):
        expired_docs = Document.objects.filter(
            expiry_date__lt=timezone.now().date(),
            is_active=True
        )
        serializer = self.get_serializer(expired_docs, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def expiring_soon(self, request):
        thirty_days_from_now = timezone.now().date() + timezone.timedelta(days=30)
        expiring = Document.objects.filter(
            expiry_date__gte=timezone.now().date(),
            expiry_date__lte=thirty_days_from_now,
            is_active=True
        )
        serializer = self.get_serializer(expiring, many=True)
        return Response(serializer.data)
    
    def check_download_permission(self, user, document):
        """Check if user has permission to download the document."""
        if user.is_staff or user.user_type == 'executive':
            return True
        
        if document.access_level == 'public':
            return True
        
        if document.access_level == 'member' and user.is_authenticated:
            return True
        
        if document.access_level == 'executive' and user.user_type == 'executive':
            return True
        
        return False
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class DocumentReviewViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentReviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        document_id = self.request.query_params.get('document')
        
        if user.is_staff or user.user_type == 'executive':
            if document_id:
                return DocumentReview.objects.filter(document_id=document_id)
            return DocumentReview.objects.all()
        
        if document_id:
            return DocumentReview.objects.filter(document_id=document_id, reviewer=user)
        return DocumentReview.objects.filter(reviewer=user)
    
    def perform_create(self, serializer):
        serializer.save(reviewer=self.request.user)


class DocumentTemplateViewSet(viewsets.ModelViewSet):
    queryset = DocumentTemplate.objects.filter(is_active=True)
    serializer_class = DocumentTemplateSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['template_type']
    search_fields = ['name', 'description']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        template = self.get_object()
        
        # Update usage statistics
        template.usage_count += 1
        template.last_used = timezone.now()
        template.save()
        
        return Response({
            'download_url': request.build_absolute_uri(template.template_file.url),
            'filename': template.template_file.name.split('/')[-1]
        })


# ------------------------------------------------------------
# Web Interface Views (for template rendering)
# ------------------------------------------------------------

@login_required
def document_list(request):
    """Web view for listing documents"""
    # Get all active documents with appropriate filtering
    if request.user.is_staff or getattr(request.user, 'user_type', None) == 'executive':
        documents = Document.objects.filter(is_active=True)
    elif request.user.is_authenticated:
        documents = Document.objects.filter(is_active=True).exclude(access_level='confidential')
    else:
        documents = Document.objects.filter(is_active=True, access_level='public')
    
    # Filter by document type if specified
    document_type = request.GET.get('type', '')
    if document_type:
        documents = documents.filter(document_type=document_type)
    
    # Filter by category if specified
    category_id = request.GET.get('category', '')
    if category_id:
        documents = documents.filter(category_id=category_id)
    
    # Get document categories for filter dropdown
    categories = DocumentCategory.objects.all()
    
    # Get document statistics
    total_documents = Document.objects.filter(is_active=True).count()
    confidential_count = Document.objects.filter(access_level='confidential', is_active=True).count()
    expiring_soon = Document.objects.filter(
        expiry_date__gte=timezone.now().date(),
        expiry_date__lte=timezone.now().date() + timezone.timedelta(days=30),
        is_active=True
    ).count()
    
    context = {
        'user': request.user,
        'documents': documents.order_by('-created_at'),
        'categories': categories,
        'total_documents': total_documents,
        'confidential_count': confidential_count,
        'expiring_soon_count': expiring_soon,
        'document_types': Document.objects.values_list('document_type', flat=True).distinct(),
        'selected_type': document_type,
        'selected_category': category_id,
        'current_year': timezone.now().year,
    }
    return render(request, 'documents/document_list.html', context)


@login_required
def document_dashboard(request):
    """Web view for document management dashboard"""
    # Get statistics for dashboard
    total_documents = Document.objects.filter(is_active=True).count()
    total_categories = DocumentCategory.objects.count()
    total_downloads = Document.objects.aggregate(total=Count('download_count'))['total'] or 0
    total_views = Document.objects.aggregate(total=Count('view_count'))['total'] or 0
    
    # Get recent documents
    recent_documents = Document.objects.filter(is_active=True).order_by('-created_at')[:10]
    
    # Get popular documents (by downloads)
    popular_documents = Document.objects.filter(is_active=True).order_by('-download_count')[:5]
    
    # Get documents by type
    documents_by_type = Document.objects.filter(is_active=True).values('document_type').annotate(
        count=Count('id'),
        total_downloads=Count('download_count'),
        total_views=Count('view_count')
    )
    
    # Get expiring documents
    expiring_documents = Document.objects.filter(
        expiry_date__gte=timezone.now().date(),
        expiry_date__lte=timezone.now().date() + timezone.timedelta(days=30),
        is_active=True
    ).order_by('expiry_date')[:5]
    
    # Get access statistics
    if request.user.is_staff or getattr(request.user, 'user_type', None) == 'executive':
        recent_access_logs = DocumentAccessLog.objects.all().order_by('-accessed_at')[:20]
    else:
        recent_access_logs = DocumentAccessLog.objects.filter(user=request.user).order_by('-accessed_at')[:10]
    
    context = {
        'user': request.user,
        'total_documents': total_documents,
        'total_categories': total_categories,
        'total_downloads': total_downloads,
        'total_views': total_views,
        'recent_documents': recent_documents,
        'popular_documents': popular_documents,
        'documents_by_type': documents_by_type,
        'expiring_documents': expiring_documents,
        'recent_access_logs': recent_access_logs,
        'current_year': timezone.now().year,
        'current_month': timezone.now().month,
    }
    return render(request, 'documents/document_dashboard.html', context)