from rest_framework import serializers
from .models import Event, EventRegistration, EventPhoto, EventResource
from accounts.serializers import UserSerializer


class EventSerializer(serializers.ModelSerializer):
    organizer = UserSerializer(read_only=True)
    coordinator = UserSerializer(read_only=True)
    
    class Meta:
        model = Event
        fields = '__all__'
        read_only_fields = ['total_registrations', 'total_attendance']


class EventRegistrationSerializer(serializers.ModelSerializer):
    participant = UserSerializer(read_only=True)
    
    class Meta:
        model = EventRegistration
        fields = '__all__'
        read_only_fields = ['registration_date', 'confirmation_date', 'check_in_time',
                           'check_out_time', 'payment_date']


class EventRegistrationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventRegistration
        fields = ['dietary_requirements', 'special_needs', 'emergency_contact', 'emergency_phone']


class EventPhotoSerializer(serializers.ModelSerializer):
    uploaded_by = UserSerializer(read_only=True)
    
    class Meta:
        model = EventPhoto
        fields = '__all__'
        read_only_fields = ['uploaded_by', 'uploaded_at']


class EventResourceSerializer(serializers.ModelSerializer):
    uploaded_by = UserSerializer(read_only=True)
    
    class Meta:
        model = EventResource
        fields = '__all__'
        read_only_fields = ['uploaded_by', 'uploaded_at', 'download_count']


class CheckInSerializer(serializers.Serializer):
    pass  # No data needed for now


class EventFeedbackSerializer(serializers.Serializer):
    rating = serializers.IntegerField(min_value=1, max_value=5)
    feedback = serializers.CharField(required=False, allow_blank=True)