from rest_framework import serializers
from .models import Announcement, Newsletter, Feedback, ContactMessage
from accounts.serializers import UserSerializer


class AnnouncementSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    published_by = UserSerializer(read_only=True)
    
    class Meta:
        model = Announcement
        fields = '__all__'
        read_only_fields = ['view_count', 'email_sent', 'sms_sent', 'push_sent',
                           'created_at', 'updated_at']


class NewsletterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Newsletter
        fields = '__all__'
        read_only_fields = ['sent_count', 'delivered_count', 'opened_count', 'click_count',
                           'bounce_count', 'unsubscribe_count', 'created_at', 'updated_at']


class FeedbackSerializer(serializers.ModelSerializer):
    submitted_by = UserSerializer(read_only=True)
    assigned_to = UserSerializer(read_only=True)
    resolved_by = UserSerializer(read_only=True)
    
    class Meta:
        model = Feedback
        fields = '__all__'
        read_only_fields = ['submitted_by', 'assigned_to', 'resolved_by', 'resolved_at',
                           'ip_address', 'user_agent', 'created_at', 'updated_at']


class ContactMessageSerializer(serializers.ModelSerializer):
    responded_by = UserSerializer(read_only=True)
    
    class Meta:
        model = ContactMessage
        fields = '__all__'
        read_only_fields = ['status', 'responded_by', 'response', 'responded_at',
                           'ip_address', 'user_agent', 'referrer', 'created_at', 'updated_at']


class NewsletterSubscriptionSerializer(serializers.Serializer):
    email = serializers.EmailField()
    subscribe = serializers.BooleanField(default=True)