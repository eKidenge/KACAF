from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from rest_framework import viewsets, permissions, status, filters
import django_filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Event, EventRegistration, EventPhoto, EventResource
from .serializers import (
    EventSerializer, EventRegistrationSerializer,
    EventPhotoSerializer, EventResourceSerializer,
    EventRegistrationCreateSerializer, CheckInSerializer,
    EventFeedbackSerializer
)


class EventFilter(django_filters.FilterSet):
    start_date_from = django_filters.DateFilter(field_name='start_datetime', lookup_expr='gte')
    start_date_to = django_filters.DateFilter(field_name='start_datetime', lookup_expr='lte')
    event_type = django_filters.CharFilter(field_name='event_type')
    status = django_filters.CharFilter(field_name='status')
    is_public = django_filters.BooleanFilter(field_name='is_public')
    
    class Meta:
        model = Event
        fields = ['event_type', 'status', 'is_public', 'is_featured']


class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = EventFilter
    search_fields = ['title', 'description', 'location', 'agenda']
    ordering_fields = ['start_datetime', 'created_at', 'total_registrations']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        queryset = Event.objects.all()
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_public=True)
        
        # Filter for upcoming events
        upcoming = self.request.query_params.get('upcoming', None)
        if upcoming == 'true':
            queryset = queryset.filter(start_datetime__gte=timezone.now())
        
        # Filter for past events
        past = self.request.query_params.get('past', None)
        if past == 'true':
            queryset = queryset.filter(start_datetime__lt=timezone.now())
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        upcoming_events = Event.objects.filter(
            start_datetime__gte=timezone.now(),
            status__in=['published', 'ongoing']
        ).order_by('start_datetime')
        serializer = self.get_serializer(upcoming_events, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        featured_events = Event.objects.filter(
            is_featured=True,
            start_datetime__gte=timezone.now(),
            status__in=['published', 'ongoing']
        ).order_by('start_datetime')
        serializer = self.get_serializer(featured_events, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        event = self.get_object()
        stats = {
            'total_registrations': event.total_registrations,
            'total_attendance': event.total_attendance,
            'attendance_rate': round((event.total_attendance / max(event.total_registrations, 1)) * 100, 2),
            'payment_status': event.registrations.values('payment_status').annotate(count=Count('id')),
            'registrations_by_status': event.registrations.values('status').annotate(count=Count('id')),
        }
        return Response(stats)
    
    @action(detail=True, methods=['post'])
    def register(self, request, pk=None):
        event = self.get_object()
        
        # Check if registration is open
        if event.requires_registration and event.registration_deadline:
            if timezone.now() > event.registration_deadline:
                return Response({'error': 'Registration deadline has passed.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if already registered
        existing_registration = EventRegistration.objects.filter(
            event=event,
            participant=request.user
        ).first()
        
        if existing_registration:
            return Response({'error': 'Already registered for this event.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check capacity
        if event.registrations.filter(status__in=['confirmed', 'pending']).count() >= event.max_participants:
            return Response({'error': 'Event is full.'}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = EventRegistrationCreateSerializer(data=request.data)
        if serializer.is_valid():
            registration = serializer.save(event=event, participant=request.user)
            
            # Update event registration count
            event.total_registrations = event.registrations.count()
            event.save()
            
            return Response(
                EventRegistrationSerializer(registration).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EventRegistrationViewSet(viewsets.ModelViewSet):
    serializer_class = EventRegistrationSerializer
    
    def get_queryset(self):
        user = self.request.user
        event_id = self.request.query_params.get('event')
        
        if user.is_staff:
            if event_id:
                return EventRegistration.objects.filter(event_id=event_id)
            return EventRegistration.objects.all()
        else:
            if event_id:
                return EventRegistration.objects.filter(event_id=event_id, participant=user)
            return EventRegistration.objects.filter(participant=user)
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    @action(detail=True, methods=['post'])
    def check_in(self, request, pk=None):
        registration = self.get_object()
        
        if registration.attended:
            return Response({'error': 'Already checked in.'}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = CheckInSerializer(data=request.data)
        if serializer.is_valid():
            registration.check_in_time = timezone.now()
            registration.attended = True
            registration.status = 'attended'
            registration.save()
            
            # Update event attendance count
            event = registration.event
            event.total_attendance = event.registrations.filter(attended=True).count()
            event.save()
            
            return Response({'message': 'Checked in successfully.'}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def submit_feedback(self, request, pk=None):
        registration = self.get_object()
        
        if not registration.attended:
            return Response({'error': 'Cannot submit feedback without attending.'}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = EventFeedbackSerializer(data=request.data)
        if serializer.is_valid():
            registration.rating = serializer.validated_data['rating']
            registration.feedback = serializer.validated_data.get('feedback', '')
            registration.save()
            
            return Response({'message': 'Feedback submitted successfully.'}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def my_registrations(self, request):
        registrations = EventRegistration.objects.filter(participant=request.user)
        serializer = self.get_serializer(registrations, many=True)
        return Response(serializer.data)


class EventPhotoViewSet(viewsets.ModelViewSet):
    queryset = EventPhoto.objects.all()
    serializer_class = EventPhotoSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['event', 'is_featured', 'uploaded_by']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        featured_photos = EventPhoto.objects.filter(is_featured=True)
        serializer = self.get_serializer(featured_photos, many=True)
        return Response(serializer.data)


class EventResourceViewSet(viewsets.ModelViewSet):
    queryset = EventResource.objects.all()
    serializer_class = EventResourceSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['event', 'resource_type', 'is_public', 'uploaded_by']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def download(self, request, pk=None):
        resource = self.get_object()
        resource.download_count += 1
        resource.save()
        
        # Return the file URL for download
        return Response({
            'message': 'Download recorded',
            'download_url': request.build_absolute_uri(resource.file.url)
        })


# ------------------------------------------------------------
# Web Interface Views (for template rendering)
# ------------------------------------------------------------

@login_required
def event_list(request):
    """Web view for listing events"""
    # Get all events, but show only public ones for non-staff
    if request.user.is_staff:
        events = Event.objects.all()
    else:
        events = Event.objects.filter(is_public=True)
    
    # Filter by upcoming/past if specified
    filter_type = request.GET.get('filter', 'upcoming')
    if filter_type == 'upcoming':
        events = events.filter(start_datetime__gte=timezone.now())
    elif filter_type == 'past':
        events = events.filter(start_datetime__lt=timezone.now())
    
    # Get user's registrations
    user_registrations = EventRegistration.objects.filter(participant=request.user)
    registered_event_ids = user_registrations.values_list('event_id', flat=True)
    
    context = {
        'user': request.user,
        'events': events.order_by('start_datetime'),
        'registered_event_ids': list(registered_event_ids),
        'total_events': events.count(),
        'upcoming_count': events.filter(start_datetime__gte=timezone.now()).count(),
        'past_count': events.filter(start_datetime__lt=timezone.now()).count(),
        'filter_type': filter_type,
    }
    return render(request, 'events/event/event_list.html', context)


@login_required
def event_calendar(request):
    """Web view for event calendar"""
    # Get all events for the calendar
    if request.user.is_staff:
        events = Event.objects.all()
    else:
        events = Event.objects.filter(is_public=True)
    
    # Format events for FullCalendar or similar
    calendar_events = []
    for event in events:
        calendar_events.append({
            'id': event.id,
            'title': event.title,
            'start': event.start_datetime.isoformat(),
            'end': event.end_datetime.isoformat() if event.end_datetime else None,
            'location': event.location,
            'event_type': event.event_type,
            'status': event.status,
            'url': f"/api/events/events/{event.id}/",  # or create a web detail page
        })
    
    context = {
        'user': request.user,
        'calendar_events': calendar_events,
        'event_types': Event.objects.values_list('event_type', flat=True).distinct(),
        'total_events': events.count(),
    }
    return render(request, 'events/event_calendar.html', context)



    # Additional web views for event detail, create/edit, registration management, etc. can be added similarly.
    # events/views.py
from django.shortcuts import render
from django.utils import timezone
from .models import Event, EventPhoto, EventResource

def public_dashboard(request):
    """
    Public dashboard showing upcoming events, featured photos, and resources.
    """
    # Only public events that are upcoming
    upcoming_events = Event.objects.filter(
        is_public=True,
        start_datetime__gte=timezone.now(),
        status__in=['published', 'ongoing']
    ).order_by('start_datetime')

    # Featured photos for public gallery
    featured_photos = EventPhoto.objects.filter(
        is_featured=True,
        event__is_public=True
    ).order_by('-uploaded_at')

    # Public resources
    public_resources = EventResource.objects.filter(
        is_public=True,
        event__is_public=True
    ).order_by('-uploaded_at')

    context = {
        'upcoming_events': upcoming_events,
        'featured_photos': featured_photos,
        'public_resources': public_resources,
        'total_events': upcoming_events.count(),
        'total_photos': featured_photos.count(),
        'total_resources': public_resources.count(),
    }

    return render(request, 'dashboard/public_dashboard.html', context)


def public_event_detail(request, event_id):
    """
    Public view for a single event detail page.
    """
    try:
        event = Event.objects.get(id=event_id, is_public=True)
    except Event.DoesNotExist:
        event = None

    photos = event.photos.filter(is_featured=True) if event else []
    resources = event.resources.filter(is_public=True) if event else []

    context = {
        'event': event,
        'photos': photos,
        'resources': resources,
    }

    return render(request, 'dashboard/public_event_detail.html', context)
