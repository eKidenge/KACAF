from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import FileExtensionValidator


User = get_user_model()


class Announcement(models.Model):
    ANNOUNCEMENT_TYPE = (
        ('general', 'General Announcement'),
        ('event', 'Event Announcement'),
        ('program', 'Program Update'),
        ('opportunity', 'Opportunity'),
        ('emergency', 'Emergency Alert'),
        ('maintenance', 'System Maintenance'),
        ('policy', 'Policy Change'),
        ('achievement', 'Achievement/Celebration'),
    )
    
    PRIORITY_LEVEL = (
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )
    
    TARGET_AUDIENCE = (
        ('all', 'All Users'),
        ('members', 'Members Only'),
        ('executive', 'Executive Committee'),
        ('youth', 'Youth Members'),
        ('women', 'Women Members'),
        ('farmers', 'Farmer Members'),
        ('staff', 'Staff Only'),
        ('custom', 'Custom Audience'),
    )
    
    title = models.CharField(max_length=200)
    announcement_type = models.CharField(max_length=20, choices=ANNOUNCEMENT_TYPE)
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVEL, default='normal')
    
    # Content
    content = models.TextField()
    summary = models.TextField(null=True, blank=True, help_text="Brief summary for notifications")
    
    # Target audience
    target_audience = models.CharField(max_length=20, choices=TARGET_AUDIENCE, default='all')
    specific_users = models.ManyToManyField(User, blank=True, related_name='targeted_announcements')
    
    # Publishing
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='authored_announcements')
    publish_date = models.DateTimeField(default=timezone.now)
    expiry_date = models.DateTimeField(null=True, blank=True)
    is_published = models.BooleanField(default=False)
    published_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='published_announcements')
    
    # Associations
    program = models.ForeignKey('programs.Program', on_delete=models.SET_NULL, null=True, blank=True, related_name='announcements')
    event = models.ForeignKey('events.Event', on_delete=models.SET_NULL, null=True, blank=True, related_name='announcements')
    project = models.ForeignKey('programs.Project', on_delete=models.SET_NULL, null=True, blank=True, related_name='announcements')
    
    # Media
    featured_image = models.ImageField(upload_to='announcements/images/', null=True, blank=True)
    attachments = models.ManyToManyField('AnnouncementAttachment', blank=True, related_name='announcements')
    
    # Tracking
    view_count = models.IntegerField(default=0)
    email_sent = models.BooleanField(default=False)
    sms_sent = models.BooleanField(default=False)
    push_sent = models.BooleanField(default=False)
    
    # SEO/Social
    meta_description = models.TextField(null=True, blank=True)
    meta_keywords = models.CharField(max_length=500, null=True, blank=True)
    og_image = models.ImageField(upload_to='announcements/og-images/', null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-publish_date']
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if self.is_published and not self.published_by and hasattr(self, 'request') and self.request.user:
            self.published_by = self.request.user
        super().save(*args, **kwargs)


class AnnouncementAttachment(models.Model):
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE, related_name='attachment_files')
    file = models.FileField(
        upload_to='announcements/attachments/',
        validators=[
            FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'jpg', 'png', 'zip'])
        ]
    )
    title = models.CharField(max_length=200, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return self.title or self.file.name


class Newsletter(models.Model):
    FREQUENCY = (
        ('weekly', 'Weekly'),
        ('biweekly', 'Bi-weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('biannual', 'Bi-annual'),
        ('annual', 'Annual'),
        ('special', 'Special Edition'),
    )
    
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('sending', 'Sending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    )
    
    title = models.CharField(max_length=200)
    subject = models.CharField(max_length=200)
    frequency = models.CharField(max_length=20, choices=FREQUENCY, null=True, blank=True)
    
    # Content
    content = models.TextField()
    html_content = models.TextField(null=True, blank=True)
    
    # Edition info
    edition_number = models.IntegerField(null=True, blank=True)
    volume_number = models.IntegerField(null=True, blank=True)
    year = models.IntegerField(default=timezone.now().year)
    
    # Schedule
    scheduled_for = models.DateTimeField()
    sent_at = models.DateTimeField(null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_template = models.BooleanField(default=False)
    
    # Target audience
    target_segment = models.CharField(max_length=20, choices=Announcement.TARGET_AUDIENCE, default='all')
    
    # Statistics
    total_recipients = models.IntegerField(default=0)
    sent_count = models.IntegerField(default=0)
    delivered_count = models.IntegerField(default=0)
    opened_count = models.IntegerField(default=0)
    click_count = models.IntegerField(default=0)
    bounce_count = models.IntegerField(default=0)
    unsubscribe_count = models.IntegerField(default=0)
    
    # Campaign tracking
    campaign_id = models.CharField(max_length=100, null=True, blank=True)
    tracking_id = models.UUIDField(null=True, blank=True, unique=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-scheduled_for']
    
    def __str__(self):
        return f"{self.title} - Edition {self.edition_number or 'N/A'}"


class Feedback(models.Model):
    FEEDBACK_TYPE = (
        ('general', 'General Feedback'),
        ('suggestion', 'Suggestion'),
        ('complaint', 'Complaint'),
        ('compliment', 'Compliment'),
        ('bug_report', 'Bug Report'),
        ('feature_request', 'Feature Request'),
        ('inquiry', 'Inquiry'),
    )
    
    STATUS_CHOICES = (
        ('new', 'New'),
        ('acknowledged', 'Acknowledged'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    )
    
    feedback_type = models.CharField(max_length=20, choices=FEEDBACK_TYPE)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    
    # Submitter info
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='submitted_feedback')
    submitter_name = models.CharField(max_length=100, null=True, blank=True)
    submitter_email = models.EmailField(null=True, blank=True)
    submitter_phone = models.CharField(max_length=15, null=True, blank=True)
    
    # Associations
    program = models.ForeignKey('programs.Program', on_delete=models.SET_NULL, null=True, blank=True, related_name='feedback')
    event = models.ForeignKey('events.Event', on_delete=models.SET_NULL, null=True, blank=True, related_name='feedback')
    document = models.ForeignKey('documents.Document', on_delete=models.SET_NULL, null=True, blank=True, related_name='feedback')
    
    # Status and handling
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    priority = models.CharField(max_length=10, choices=Announcement.PRIORITY_LEVEL, default='normal')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_feedback')
    
    # Resolution
    resolution = models.TextField(null=True, blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_feedback')
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # Contact preferences
    follow_up_required = models.BooleanField(default=False)
    allow_contact = models.BooleanField(default=True)
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_feedback_type_display()}: {self.subject}"


class ContactMessage(models.Model):
    CATEGORY_CHOICES = (
        ('general', 'General Inquiry'),
        ('membership', 'Membership Inquiry'),
        ('donation', 'Donation Inquiry'),
        ('partnership', 'Partnership Inquiry'),
        ('media', 'Media Inquiry'),
        ('volunteer', 'Volunteer Inquiry'),
        ('technical', 'Technical Support'),
        ('other', 'Other'),
    )
    
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15, null=True, blank=True)
    organization = models.CharField(max_length=200, null=True, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    subject = models.CharField(max_length=200)
    message = models.TextField()
    
    # Status
    status = models.CharField(max_length=20, choices=[
        ('new', 'New'),
        ('read', 'Read'),
        ('replied', 'Replied'),
        ('archived', 'Archived'),
    ], default='new')
    
    # Response tracking
    responded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    response = models.TextField(null=True, blank=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    referrer = models.URLField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name}: {self.subject}"