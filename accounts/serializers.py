from django.contrib.auth import get_user_model, password_validation
from rest_framework import serializers
from .models import CustomUser, MemberProfile, ExecutiveCommittee

User = get_user_model()


# ---------------------------
# User serializer
# ---------------------------
class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'user_type', 'membership_type', 'phone', 'id_number', 'date_of_birth',
            'gender', 'occupation', 'education_level', 'profile_picture', 'bio',
            'county', 'sub_county', 'ward', 'village', 'postal_address', 'postal_code',
            'organization_name', 'referral_source', 'interests', 'skills',
            'newsletter_subscription', 'terms_accepted', 'data_consent',
            'join_date', 'is_verified', 'verification_date', 'is_active'
        ]
        read_only_fields = ['id', 'join_date', 'is_verified', 'verification_date']
    
    def get_full_name(self, obj):
        return obj.get_full_name()


# ---------------------------
# User registration serializer
# ---------------------------
class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[password_validation.validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    
    # Personal Information
    phone = serializers.CharField(max_length=15, required=True)
    id_number = serializers.CharField(max_length=20, required=True)
    date_of_birth = serializers.DateField(required=True)
    gender = serializers.ChoiceField(choices=['male', 'female', 'other'], required=True)
    occupation = serializers.CharField(max_length=100, required=False, allow_blank=True)
    education_level = serializers.ChoiceField(
        choices=['primary', 'secondary', 'certificate', 'diploma', 'degree', 'masters', 'phd'],
        required=False, allow_blank=True, allow_null=True
    )
    profile_picture = serializers.ImageField(required=False, allow_null=True)
    
    # Location Information
    county = serializers.CharField(max_length=100, required=True)
    sub_county = serializers.CharField(max_length=100, required=True)
    ward = serializers.CharField(max_length=100, required=True)
    village = serializers.CharField(max_length=100, required=True)
    postal_address = serializers.CharField(max_length=100, required=False, allow_blank=True)
    postal_code = serializers.CharField(max_length=20, required=False, allow_blank=True)
    
    # Membership Information
    user_type = serializers.ChoiceField(
        choices=['member', 'farmer', 'youth', 'organization', 'executive', 'staff', 'donor', 'admin'],
        default='member'
    )
    organization_name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    referral_source = serializers.ChoiceField(
        choices=['social_media', 'friend', 'event', 'radio', 'newspaper', 'other'],
        required=False, allow_blank=True, allow_null=True
    )
    interests = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    skills = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    
    # Consent Fields
    newsletter_subscription = serializers.BooleanField(default=False)
    terms_accepted = serializers.BooleanField(required=True)
    data_consent = serializers.BooleanField(required=True)

    class Meta:
        model = CustomUser
        fields = [
            'username', 'email', 'first_name', 'last_name', 'password', 'password2',
            'phone', 'id_number', 'date_of_birth', 'gender', 'occupation', 
            'education_level', 'profile_picture', 'county', 'sub_county', 'ward', 
            'village', 'postal_address', 'postal_code', 'user_type', 
            'organization_name', 'referral_source', 'interests', 'skills',
            'newsletter_subscription', 'terms_accepted', 'data_consent'
        ]
        extra_kwargs = {
            'username': {'required': False},
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {'required': True},
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        
        # Auto-generate username from email if not provided
        if not attrs.get('username') and attrs.get('email'):
            attrs['username'] = attrs['email'].split('@')[0]
            
        # Ensure terms are accepted
        if not attrs.get('terms_accepted'):
            raise serializers.ValidationError({"terms_accepted": "You must accept the terms and conditions."})
            
        # Ensure data consent is given
        if not attrs.get('data_consent'):
            raise serializers.ValidationError({"data_consent": "You must consent to data processing."})
            
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        
        # Create user with all fields
        user = CustomUser(**validated_data)
        user.set_password(password)
        user.save()
        
        return user


# ---------------------------
# MemberProfile serializer
# ---------------------------
class MemberProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(), source='user', write_only=True
    )

    class Meta:
        model = MemberProfile
        fields = [
            'id', 'user', 'user_id', 'farm_size', 'trees_planted', 
            'conservation_practices', 'total_donations', 'events_attended', 
            'training_completed', 'receive_newsletter', 'receive_sms', 
            'receive_email', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# ---------------------------
# ExecutiveCommittee serializer
# ---------------------------
class ExecutiveCommitteeSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(), source='user', write_only=True
    )
    position_display = serializers.CharField(source='get_position_display', read_only=True)

    class Meta:
        model = ExecutiveCommittee
        fields = [
            'id', 'user', 'user_id', 'position', 'position_display', 'order',
            'responsibilities', 'term_start', 'term_end', 'is_active',
            'can_suspend_members', 'can_manage_finances', 'can_represent_legally',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# ---------------------------
# Change password serializer
# ---------------------------
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, validators=[password_validation.validate_password])
    new_password2 = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({"new_password": "Password fields didn't match."})
        return attrs


# ---------------------------
# User update serializer
# ---------------------------
class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'email', 'phone', 'id_number',
            'date_of_birth', 'gender', 'occupation', 'education_level',
            'profile_picture', 'county', 'sub_county', 'ward', 'village',
            'postal_address', 'postal_code', 'organization_name',
            'referral_source', 'interests', 'skills', 'bio',
            'newsletter_subscription'
        ]