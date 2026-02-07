from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import FileExtensionValidator


User = get_user_model()


class DocumentCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(null=True, blank=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subcategories')
    order = models.IntegerField(default=0, help_text="Display order")
    icon = models.CharField(max_length=50, null=True, blank=True, help_text="FontAwesome icon class")
    
    class Meta:
        verbose_name_plural = "Document Categories"
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name


class Document(models.Model):
    DOCUMENT_TYPE = (
        ('policy', 'Policy'),
        ('procedure', 'Procedure'),
        ('report', 'Report'),
        ('form', 'Form/Template'),
        ('guideline', 'Guideline/Manual'),
        ('agreement', 'Agreement/Contract'),
        ('certificate', 'Certificate'),
        ('minutes', 'Meeting Minutes'),
        ('financial', 'Financial Document'),
        ('legal', 'Legal Document'),
        ('other', 'Other'),
    )
    
    ACCESS_LEVEL = (
        ('public', 'Public'),
        ('member', 'Members Only'),
        ('executive', 'Executive Committee'),
        ('confidential', 'Confidential'),
        ('restricted', 'Restricted'),
    )
    
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('review', 'Under Review'),
        ('approved', 'Approved'),
        ('archived', 'Archived'),
        ('obsolete', 'Obsolete'),
    )
    
    title = models.CharField(max_length=200)
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPE)
    category = models.ForeignKey(DocumentCategory, on_delete=models.SET_NULL, null=True, related_name='documents')
    
    # File details
    file = models.FileField(
        upload_to='documents/',
        validators=[
            FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'jpg', 'png'])
        ]
    )
    file_size = models.BigIntegerField(help_text="Size in bytes", default=0)
    file_format = models.CharField(max_length=10, help_text="File extension")
    
    # Metadata
    description = models.TextField(null=True, blank=True)
    version = models.CharField(max_length=20, default='1.0')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    access_level = models.CharField(max_length=20, choices=ACCESS_LEVEL, default='member')
    
    # Associated data
    program = models.ForeignKey('programs.Program', on_delete=models.SET_NULL, null=True, blank=True, related_name='documents')
    project = models.ForeignKey('programs.Project', on_delete=models.SET_NULL, null=True, blank=True, related_name='documents')
    event = models.ForeignKey('events.Event', on_delete=models.SET_NULL, null=True, blank=True, related_name='documents')
    
    # Ownership and approval
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='owned_documents')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_documents')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_documents')
    approval_date = models.DateField(null=True, blank=True)
    
    # Validity
    effective_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Tracking
    download_count = models.IntegerField(default=0)
    view_count = models.IntegerField(default=0)
    last_downloaded = models.DateTimeField(null=True, blank=True)
    last_viewed = models.DateTimeField(null=True, blank=True)
    
    # Tags and keywords
    tags = models.CharField(max_length=500, null=True, blank=True, help_text="Comma-separated tags")
    keywords = models.TextField(null=True, blank=True, help_text="Search keywords")
    
    # Version control
    previous_version = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='next_versions')
    change_log = models.TextField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} (v{self.version})"
    
    def save(self, *args, **kwargs):
        # Set file size and format
        if self.file:
            self.file_size = self.file.size
            self.file_format = self.file.name.split('.')[-1].lower()
        
        # Set created_by if not set
        if not self.created_by and hasattr(self, 'request') and self.request.user:
            self.created_by = self.request.user
        
        super().save(*args, **kwargs)


class DocumentAccessLog(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='access_logs')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    access_type = models.CharField(max_length=10, choices=[('view', 'View'), ('download', 'Download')])
    accessed_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    
    class Meta:
        ordering = ['-accessed_at']
    
    def __str__(self):
        return f"{self.user} {self.access_type}d {self.document.title}"


class DocumentReview(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='document_reviews')
    review_date = models.DateTimeField(auto_now_add=True)
    comments = models.TextField()
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('reviewed', 'Reviewed'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('requires_changes', 'Requires Changes'),
    ], default='pending')
    changes_required = models.TextField(null=True, blank=True)
    
    class Meta:
        ordering = ['-review_date']
    
    def __str__(self):
        return f"Review by {self.reviewer} for {self.document.title}"


class DocumentTemplate(models.Model):
    TEMPLATE_TYPE = (
        ('membership_form', 'Membership Application Form'),
        ('event_registration', 'Event Registration Form'),
        ('project_proposal', 'Project Proposal Template'),
        ('financial_report', 'Financial Report Template'),
        ('meeting_minutes', 'Meeting Minutes Template'),
        ('letter', 'Official Letter Template'),
        ('certificate', 'Certificate Template'),
        ('other', 'Other'),
    )
    
    name = models.CharField(max_length=200)
    template_type = models.CharField(max_length=30, choices=TEMPLATE_TYPE)
    description = models.TextField(null=True, blank=True)
    
    # Template files
    template_file = models.FileField(upload_to='templates/', help_text="Editable template file (DOCX, XLSX, etc.)")
    preview_image = models.ImageField(upload_to='templates/previews/', null=True, blank=True)
    
    # Usage tracking
    usage_count = models.IntegerField(default=0)
    last_used = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    is_active = models.BooleanField(default=True)
    version = models.CharField(max_length=20, default='1.0')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"