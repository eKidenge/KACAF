from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


User = get_user_model()


class Event(models.Model):
    EVENT_TYPE = (
        ('workshop', 'Workshop'),
        ('training', 'Training'),
        ('meeting', 'Meeting'),
        ('field_visit', 'Field Visit'),
        ('tree_planting', 'Tree Planting'),
        ('fundraising', 'Fundraising'),
        ('awareness', 'Awareness Campaign'),
        ('celebration', 'Celebration/Ceremony'),
        ('conference', 'Conference'),
        ('other', 'Other'),
    )
    
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('postponed', 'Postponed'),
    )
    
    title = models.CharField(max_length=200)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE)
    description = models.TextField()
    
    # Event details
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    location = models.CharField(max_length=200)
    gps_coordinates = models.CharField(max_length=100, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    
    # Organizer details
    organizer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='organized_events')
    coordinator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='coordinated_events')
    contact_person = models.CharField(max_length=100, null=True, blank=True)
    contact_phone = models.CharField(max_length=15, null=True, blank=True)
    contact_email = models.EmailField(null=True, blank=True)
    
    # Capacity and registration
    max_participants = models.IntegerField(default=50)
    min_participants = models.IntegerField(default=1)
    requires_registration = models.BooleanField(default=True)
    registration_deadline = models.DateTimeField(null=True, blank=True)
    registration_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Status and visibility
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_public = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    
    # Logistics
    agenda = models.TextField(null=True, blank=True)
    requirements = models.TextField(null=True, blank=True, help_text="What participants should bring/prepare")
    materials_provided = models.TextField(null=True, blank=True)
    transport_arranged = models.BooleanField(default=False)
    meals_provided = models.BooleanField(default=False)
    accommodation_provided = models.BooleanField(default=False)
    
    # Budget
    budget = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    actual_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # Media
    banner_image = models.ImageField(upload_to='events/banners/', null=True, blank=True)
    gallery = models.ManyToManyField('EventPhoto', blank=True, related_name='event_gallery')
    
    # Statistics
    total_registrations = models.IntegerField(default=0)
    total_attendance = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-start_datetime']
    
    def __str__(self):
        return f"{self.title} - {self.get_event_type_display()}"


class EventRegistration(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('attended', 'Attended'),
        ('cancelled', 'Cancelled'),
        ('waiting_list', 'Waiting List'),
    )
    
    PAYMENT_STATUS = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('partial', 'Partially Paid'),
        ('waived', 'Fee Waived'),
        ('sponsored', 'Sponsored'),
    )
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    participant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='event_registrations')
    
    # Registration details
    registration_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    confirmation_date = models.DateTimeField(null=True, blank=True)
    
    # Attendance
    check_in_time = models.DateTimeField(null=True, blank=True)
    check_out_time = models.DateTimeField(null=True, blank=True)
    attended = models.BooleanField(default=False)
    
    # Payment
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    payment_method = models.CharField(max_length=50, null=True, blank=True)
    payment_reference = models.CharField(max_length=100, null=True, blank=True)
    payment_date = models.DateTimeField(null=True, blank=True)
    
    # Additional information
    dietary_requirements = models.TextField(null=True, blank=True)
    special_needs = models.TextField(null=True, blank=True)
    emergency_contact = models.CharField(max_length=100, null=True, blank=True)
    emergency_phone = models.CharField(max_length=15, null=True, blank=True)
    
    # Feedback
    rating = models.IntegerField(
        null=True, 
        blank=True, 
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    feedback = models.TextField(null=True, blank=True)
    
    notes = models.TextField(null=True, blank=True)
    
    class Meta:
        ordering = ['-registration_date']
        unique_together = ['event', 'participant']
    
    def __str__(self):
        return f"{self.participant.get_full_name()} - {self.event.title}"


class EventPhoto(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='photos')
    title = models.CharField(max_length=200, null=True, blank=True)
    caption = models.TextField(null=True, blank=True)
    photo = models.ImageField(upload_to='events/photos/')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_featured = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"Photo: {self.title or 'Untitled'} - {self.event.title}"


class EventResource(models.Model):
    RESOURCE_TYPE = (
        ('agenda', 'Agenda'),
        ('presentation', 'Presentation'),
        ('handout', 'Handout'),
        ('manual', 'Manual/Guide'),
        ('report', 'Report'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('other', 'Other'),
    )
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='resources')
    title = models.CharField(max_length=200)
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPE)
    description = models.TextField(null=True, blank=True)
    file = models.FileField(upload_to='events/resources/')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_public = models.BooleanField(default=True)
    download_count = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.title} - {self.event.title}"