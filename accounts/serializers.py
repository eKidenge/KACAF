from django.contrib.auth import get_user_model, password_validation
from rest_framework import serializers
from .models import MemberProfile, ExecutiveCommittee

User = get_user_model()


# ---------------------------
# User serializer
# ---------------------------
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'user_type', 'is_active']
        read_only_fields = ['id', 'is_active']


# ---------------------------
# User registration serializer
# ---------------------------
class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[password_validation.validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'user_type', 'password', 'password2']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn’t match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user


# ---------------------------
# MemberProfile serializer
# ---------------------------
class MemberProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = MemberProfile
        fields = ['id', 'user', 'phone', 'address', 'date_of_birth', 'gender']
        read_only_fields = ['id', 'user']


# ---------------------------
# ExecutiveCommittee serializer
# ---------------------------
class ExecutiveCommitteeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExecutiveCommittee
        fields = ['id', 'name', 'role', 'order', 'is_active']
        read_only_fields = ['id']


# ---------------------------
# Change password serializer
# ---------------------------
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[password_validation.validate_password])


# ---------------------------
# Optional user update serializer
# ---------------------------
class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
