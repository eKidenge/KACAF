from django.db.models import Q
from django.utils import timezone
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from rest_framework import viewsets, permissions, status
from rest_framework import filters
import django_filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Announcement, AnnouncementAttachment, Newsletter, Feedback, ContactMessage
from .serializers import (
    AnnouncementSerializer, NewsletterSerializer,
    FeedbackSerializer, ContactMessageSerializer,
    NewsletterSubscriptionSerializer
)


class AnnouncementFilter(django_filters.FilterSet):
    announcement_type = django_filters.CharFilter(field_name='announcement_type')
    priority = django_filters.CharFilter(field_name='priority')
    target_audience = django_filters.CharFilter(field_name='target_audience')
    is_published = django_filters.BooleanFilter(field_name='is_published')
    start_date = django_filters.DateFilter(field_name='publish_date', lookup_expr='gte')
    end_date = django_filters.DateFilter(field_name='publish_date', lookup_expr='lte')
    
    class Meta:
        model = Announcement
        fields = ['announcement_type', 'priority', 'target_audience', 'is_published', 'program', 'event', 'project']


class AnnouncementViewSet(viewsets.ModelViewSet):
    queryset = Announcement.objects.filter(is_published=True)
    serializer_class = AnnouncementSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = AnnouncementFilter
    search_fields = ['title', 'content', 'summary']
    ordering_fields = ['publish_date', 'priority', 'created_at']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Filter by publish date and expiry date
        now = timezone.now()
        queryset = queryset.filter(
            Q(expiry_date__isnull=True) | Q(expiry_date__gt=now)
        )
        
        # Filter by target audience
        if user.is_authenticated:
            if user.is_staff or user.user_type == 'executive':
                # Staff and executives can see all announcements
                return queryset
            
            # Filter based on target audience
            audience_filter = Q(target_audience='all') | Q(target_audience='members')
            
            # Add specific user targeting
            audience_filter |= Q(specific_users=user)
            
            # Add role-based targeting
            if user.user_type == 'executive':
                audience_filter |= Q(target_audience='executive')
            elif user.membership_type == 'honorary':
                audience_filter |= Q(target_audience__in=['executive', 'members'])
            
            # Apply audience filter
            queryset = queryset.filter(audience_filter)
        else:
            # Non-authenticated users can only see public announcements
            queryset = queryset.filter(target_audience='all')
        
        return queryset.distinct()
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Increment view count
        instance.view_count += 1
        instance.save()
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def latest(self, request):
        latest_announcements = self.get_queryset().order_by('-publish_date')[:10]
        serializer = self.get_serializer(latest_announcements, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def urgent(self, request):
        urgent_announcements = self.get_queryset().filter(
            priority='urgent',
            expiry_date__gt=timezone.now()
        ).order_by('-publish_date')
        serializer = self.get_serializer(urgent_announcements, many=True)
        return Response(serializer.data)


class NewsletterViewSet(viewsets.ModelViewSet):
    queryset = Newsletter.objects.all()
    serializer_class = NewsletterSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['frequency', 'status', 'year', 'is_template']
    search_fields = ['title', 'subject', 'content']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'send_test']:
            permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Non-staff can only see sent newsletters
        if not self.request.user.is_staff and self.request.user.user_type != 'executive':
            queryset = queryset.filter(status='sent')
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def send_test(self, request, pk=None):
        newsletter = self.get_object()
        
        # Send test email to requester
        try:
            send_mail(
                subject=f"[TEST] {newsletter.subject}",
                message=newsletter.content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[request.user.email],
                html_message=newsletter.html_content,
                fail_silently=False,
            )
            
            return Response({'message': f'Test email sent to {request.user.email}'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': f'Failed to send test email: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def templates(self, request):
        templates = Newsletter.objects.filter(is_template=True)
        serializer = self.get_serializer(templates, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def archived(self, request):
        archived = Newsletter.objects.filter(status='sent').order_by('-sent_at')
        serializer = self.get_serializer(archived, many=True)
        return Response(serializer.data)


class FeedbackViewSet(viewsets.ModelViewSet):
    serializer_class = FeedbackSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_staff or user.user_type == 'executive':
            return Feedback.objects.all()
        elif user.is_authenticated:
            return Feedback.objects.filter(submitted_by=user)
        else:
            return Feedback.objects.none()
    
    def get_permissions(self):
        if self.action in ['create']:
            permission_classes = [permissions.AllowAny]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            serializer.save(submitted_by=self.request.user)
        else:
            serializer.save()
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, permissions.IsAdminUser])
    def assign(self, request, pk=None):
        feedback = self.get_object()
        assigned_to_id = request.data.get('assigned_to')
        
        if assigned_to_id:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                assigned_to = User.objects.get(id=assigned_to_id)
                feedback.assigned_to = assigned_to
                feedback.save()
                return Response({'message': f'Assigned to {assigned_to.get_full_name()}'}, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return Response({'error': 'User not found'}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({'error': 'assigned_to is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, permissions.IsAdminUser])
    def resolve(self, request, pk=None):
        feedback = self.get_object()
        resolution = request.data.get('resolution', '')
        
        feedback.status = 'resolved'
        feedback.resolution = resolution
        feedback.resolved_by = request.user
        feedback.resolved_at = timezone.now()
        feedback.save()
        
        return Response({'message': 'Feedback marked as resolved'}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated, permissions.IsAdminUser])
    def unresolved(self, request):
        unresolved = Feedback.objects.filter(status__in=['new', 'acknowledged', 'in_progress'])
        serializer = self.get_serializer(unresolved, many=True)
        return Response(serializer.data)


class ContactMessageViewSet(viewsets.ModelViewSet):
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageSerializer
    permission_classes = [permissions.AllowAny]  # Allow anyone to contact
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        # Log IP address and user agent
        ip_address = self.get_client_ip(self.request)
        user_agent = self.request.META.get('HTTP_USER_AGENT', '')
        referrer = self.request.META.get('HTTP_REFERER', '')
        
        serializer.save(
            ip_address=ip_address,
            user_agent=user_agent,
            referrer=referrer
        )
        
        # Send notification email to admin
        try:
            contact_message = serializer.instance
            send_mail(
                subject=f'New Contact Message: {contact_message.subject}',
                message=f"""
                New contact message received:
                
                Name: {contact_message.name}
                Email: {contact_message.email}
                Phone: {contact_message.phone}
                Organization: {contact_message.organization}
                Category: {contact_message.get_category_display()}
                Subject: {contact_message.subject}
                Message: {contact_message.message}
                
                Received at: {contact_message.created_at}
                """,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.ADMIN_EMAIL] if hasattr(settings, 'ADMIN_EMAIL') else [settings.DEFAULT_FROM_EMAIL],
                fail_silently=True,
            )
        except Exception:
            pass  # Silently fail email notification
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, permissions.IsAdminUser])
    def respond(self, request, pk=None):
        contact_message = self.get_object()
        response = request.data.get('response', '')
        
        if not response:
            return Response({'error': 'Response message is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Update message status
        contact_message.status = 'replied'
        contact_message.response = response
        contact_message.responded_by = request.user
        contact_message.responded_at = timezone.now()
        contact_message.save()
        
        # Send response email
        try:
            send_mail(
                subject=f'Re: {contact_message.subject}',
                message=response,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[contact_message.email],
                fail_silently=True,
            )
            
            return Response({'message': 'Response sent successfully'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': f'Failed to send email: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated, permissions.IsAdminUser])
    def new_messages(self, request):
        new_messages = ContactMessage.objects.filter(status='new').order_by('-created_at')
        serializer = self.get_serializer(new_messages, many=True)
        return Response(serializer.data)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


# ------------------------------------------------------------
# Web Interface Views (for template rendering)
# ------------------------------------------------------------

@login_required
def message_list(request):
    """Web view for listing messages and announcements"""
    # Get announcements based on user role
    if request.user.is_staff or getattr(request.user, 'user_type', None) == 'executive':
        announcements = Announcement.objects.filter(is_published=True)
    elif request.user.is_authenticated:
        # FIXED: Use chained filters instead of mixing kwargs with Q objects
        announcements = Announcement.objects.filter(
            Q(is_published=True) &
            (Q(target_audience='all') | 
             Q(target_audience='members') |
             Q(specific_users=request.user))
        ).distinct()
    else:
        announcements = Announcement.objects.filter(is_published=True, target_audience='all')
    
    # Filter by expiry date
    now = timezone.now()
    announcements = announcements.filter(
        Q(expiry_date__isnull=True) | Q(expiry_date__gt=now)
    )
    
    # Get newsletters
    newsletters = Newsletter.objects.filter(status='sent').order_by('-sent_at')[:10]
    
    # Get recent feedback if user is staff/executive
    recent_feedback = None
    if request.user.is_staff or getattr(request.user, 'user_type', None) == 'executive':
        recent_feedback = Feedback.objects.all().order_by('-created_at')[:5]
    
    # Get user's own feedback submissions
    my_feedback = Feedback.objects.filter(submitted_by=request.user).order_by('-created_at')[:10]
    
    context = {
        'user': request.user,
        'announcements': announcements.order_by('-publish_date'),
        'newsletters': newsletters,
        'recent_feedback': recent_feedback,
        'my_feedback': my_feedback,
        'urgent_announcements': announcements.filter(priority='urgent').count(),
        'total_announcements': announcements.count(),
        'current_year': timezone.now().year,
        'current_month': timezone.now().month,
    }
    return render(request, 'communications/message_list.html', context)


@login_required
def communications_dashboard(request):
    """Web view for communications dashboard"""
    # Get announcement statistics
    total_announcements = Announcement.objects.count()
    published_announcements = Announcement.objects.filter(is_published=True).count()
    urgent_announcements = Announcement.objects.filter(priority='urgent', is_published=True).count()
    
    # Get newsletter statistics
    total_newsletters = Newsletter.objects.count()
    sent_newsletters = Newsletter.objects.filter(status='sent').count()
    newsletter_templates = Newsletter.objects.filter(is_template=True).count()
    
    # Get feedback statistics
    total_feedback = Feedback.objects.count()
    unresolved_feedback = Feedback.objects.filter(status__in=['new', 'acknowledged', 'in_progress']).count()
    
    # Get contact message statistics
    total_contact_messages = ContactMessage.objects.count()
    new_contact_messages = ContactMessage.objects.filter(status='new').count()
    
    # Get recent announcements
    recent_announcements = Announcement.objects.filter(is_published=True).order_by('-publish_date')[:10]
    
    # Get recent newsletters
    recent_newsletters = Newsletter.objects.filter(status='sent').order_by('-sent_at')[:5]
    
    # Get recent feedback (if user is staff/executive)
    recent_feedback = None
    if request.user.is_staff or getattr(request.user, 'user_type', None) == 'executive':
        recent_feedback = Feedback.objects.all().order_by('-created_at')[:5]
    
    # Get recent contact messages (if user is staff/executive)
    recent_contact_messages = None
    if request.user.is_staff or getattr(request.user, 'user_type', None) == 'executive':
        recent_contact_messages = ContactMessage.objects.all().order_by('-created_at')[:5]
    
    context = {
        'user': request.user,
        'total_announcements': total_announcements,
        'published_announcements': published_announcements,
        'urgent_announcements': urgent_announcements,
        'total_newsletters': total_newsletters,
        'sent_newsletters': sent_newsletters,
        'newsletter_templates': newsletter_templates,
        'total_feedback': total_feedback,
        'unresolved_feedback': unresolved_feedback,
        'total_contact_messages': total_contact_messages,
        'new_contact_messages': new_contact_messages,
        'recent_announcements': recent_announcements,
        'recent_newsletters': recent_newsletters,
        'recent_feedback': recent_feedback,
        'recent_contact_messages': recent_contact_messages,
        'current_year': timezone.now().year,
        'current_month': timezone.now().month,
        'feedback_resolution_rate': ((total_feedback - unresolved_feedback) / total_feedback * 100) if total_feedback > 0 else 0,
        'contact_response_rate': (ContactMessage.objects.filter(status='replied').count() / total_contact_messages * 100) if total_contact_messages > 0 else 0,
    }
    return render(request, 'communications/communications_dashboard.html', context)

from django.shortcuts import render, redirect
from .models import Announcement
from .forms import AnnouncementForm  # make sure you have a form for Announcement

# ⚡ Web view for creating an announcement
def announcement_create(request):
    if request.method == 'POST':
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('communications:communications_dashboard')  # Redirect after save
    else:
        form = AnnouncementForm()
    
    context = {
        'form': form,
    }
    return render(request, 'communications/announcement_form.html', context)

# communications/views.py
from django.shortcuts import render

def contact(request):
    """
    Render the 'Contact Us' page.
    """
    return render(request, "communications/contact.html")

# communications/views.py
from django.shortcuts import redirect
from .models import Newsletter  # replace with your actual model

def newsletter_subscribe(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        if name and email:
            Newsletter.objects.create(name=name, email=email)
    return redirect('/')  # redirect to home or wherever you want


