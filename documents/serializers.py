from rest_framework import serializers
from .models import DocumentCategory, Document, DocumentReview, DocumentTemplate
from accounts.serializers import UserSerializer


class DocumentCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentCategory
        fields = '__all__'


class DocumentSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    approved_by = UserSerializer(read_only=True)
    
    class Meta:
        model = Document
        fields = '__all__'
        read_only_fields = ['file_size', 'file_format', 'download_count', 'view_count',
                           'last_downloaded', 'last_viewed', 'created_at', 'updated_at']


class DocumentReviewSerializer(serializers.ModelSerializer):
    reviewer = UserSerializer(read_only=True)
    
    class Meta:
        model = DocumentReview
        fields = '__all__'
        read_only_fields = ['reviewer', 'review_date']


class DocumentTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentTemplate
        fields = '__all__'
        read_only_fields = ['usage_count', 'last_used', 'created_at', 'updated_at']


class DocumentAccessSerializer(serializers.Serializer):
    pass