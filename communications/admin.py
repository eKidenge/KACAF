from django.contrib import admin
from .models import Announcement, AnnouncementAttachment, Newsletter, Feedback, ContactMessage


class AnnouncementAttachmentInline(admin.TabularInline):
    model = AnnouncementAttachment
    extra = 0
    fields = ('file', 'title', 'description')
    readonly_fields = ('uploaded_at',)


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'announcement_type', 'priority', 'target_audience', 'is_published', 'publish_date', 'view_count')
    list_filter = ('announcement_type', 'priority', 'target_audience', 'is_published', 'publish_date')
    search_fields = ('title', 'content', 'summary')
    filter_horizontal = ('specific_users', 'attachments')
    raw_id_fields = ('author', 'published_by', 'program', 'event', 'project')
    date_hierarchy = 'publish_date'
    inlines = [AnnouncementAttachmentInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'announcement_type', 'priority', 'content', 'summary')
        }),
        ('Audience & Publishing', {
            'fields': ('target_audience', 'specific_users', 'is_published', 'publish_date', 'expiry_date', 'author', 'published_by')
        }),
        ('Associations', {
            'fields': ('program', 'event', 'project')
        }),
        ('Media', {
            'fields': ('featured_image', 'og_image')
        }),
        ('Delivery Tracking', {
            'fields': ('email_sent', 'sms_sent', 'push_sent', 'view_count')
        }),
        ('SEO/Social', {
            'fields': ('meta_description', 'meta_keywords')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'view_count')
    
    def save_model(self, request, obj, form, change):
        if not obj.author:
            obj.author = request.user
        super().save_model(request, obj, form, change)


@admin.register(AnnouncementAttachment)
class AnnouncementAttachmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'announcement', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('title', 'description', 'announcement__title')
    raw_id_fields = ('announcement',)
    date_hierarchy = 'uploaded_at'
    
    fieldsets = (
        ('Attachment Details', {
            'fields': ('announcement', 'file', 'title', 'description')
        }),
        ('Timestamps', {
            'fields': ('uploaded_at',)
        }),
    )
    
    readonly_fields = ('uploaded_at',)


@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject', 'frequency', 'status', 'scheduled_for', 'sent_at', 'total_recipients')
    list_filter = ('frequency', 'status', 'scheduled_for', 'year')
    search_fields = ('title', 'subject', 'content')
    date_hierarchy = 'scheduled_for'
    
    fieldsets = (
        ('Newsletter Information', {
            'fields': ('title', 'subject', 'frequency', 'edition_number', 'volume_number', 'year')
        }),
        ('Content', {
            'fields': ('content', 'html_content')
        }),
        ('Schedule & Status', {
            'fields': ('scheduled_for', 'sent_at', 'status', 'is_template', 'target_segment')
        }),
        ('Statistics', {
            'fields': ('total_recipients', 'sent_count', 'delivered_count', 'opened_count', 'click_count', 'bounce_count', 'unsubscribe_count')
        }),
        ('Campaign Tracking', {
            'fields': ('campaign_id', 'tracking_id')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('subject', 'feedback_type', 'submitted_by', 'status', 'priority', 'assigned_to', 'created_at')
    list_filter = ('feedback_type', 'status', 'priority', 'created_at')
    search_fields = ('subject', 'message', 'submitter_name', 'submitter_email')
    raw_id_fields = ('submitted_by', 'assigned_to', 'resolved_by', 'program', 'event', 'document')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Feedback Details', {
            'fields': ('feedback_type', 'subject', 'message')
        }),
        ('Submitter Information', {
            'fields': ('submitted_by', 'submitter_name', 'submitter_email', 'submitter_phone')
        }),
        ('Associations', {
            'fields': ('program', 'event', 'document')
        }),
        ('Status & Handling', {
            'fields': ('status', 'priority', 'assigned_to', 'follow_up_required', 'allow_contact')
        }),
        ('Resolution', {
            'fields': ('resolution', 'resolved_by', 'resolved_at')
        }),
        ('Metadata', {
            'fields': ('ip_address', 'user_agent', 'created_at', 'updated_at')
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'category', 'subject', 'status', 'created_at')
    list_filter = ('category', 'status', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message', 'organization')
    raw_id_fields = ('responded_by',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Message Details', {
            'fields': ('category', 'subject', 'message')
        }),
        ('Contact Information', {
            'fields': ('name', 'email', 'phone', 'organization')
        }),
        ('Status & Response', {
            'fields': ('status', 'responded_by', 'response', 'responded_at')
        }),
        ('Metadata', {
            'fields': ('ip_address', 'user_agent', 'referrer', 'created_at', 'updated_at')
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')