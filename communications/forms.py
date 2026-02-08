# communications/forms.py
from django import forms
from .models import Announcement, Newsletter, Feedback, ContactMessage

class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = [
            'title',
            'announcement_type',
            'priority',
            'content',
            'summary',
            'target_audience',
            'specific_users',
            'publish_date',  # corrected field name
            'expiry_date',
            'is_published',
            'program',
            'event',
            'project',
            'featured_image',
            'attachments',
        ]

class NewsletterForm(forms.ModelForm):
    class Meta:
        model = Newsletter
        fields = [
            'title',
            'subject',
            'frequency',
            'content',
            'html_content',
            'edition_number',
            'volume_number',
            'year',
            'scheduled_for',
            'status',
            'is_template',
            'target_segment',
        ]

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = [
            'feedback_type',
            'subject',
            'message',
            'submitted_by',
            'submitter_name',
            'submitter_email',
            'submitter_phone',
            'program',
            'event',
            'document',
            'status',
            'priority',
            'assigned_to',
            'resolution',
            'resolved_by',
            'resolved_at',
            'follow_up_required',
            'allow_contact',
        ]

class ContactMessageForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = [
            'name',
            'email',
            'phone',
            'organization',
            'category',
            'subject',
            'message',
            'status',
            'responded_by',
            'response',
            'responded_at',
        ]
