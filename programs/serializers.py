from rest_framework import serializers
from .models import Program, Project, TreePlanting, Training
from accounts.serializers import UserSerializer


class ProgramSerializer(serializers.ModelSerializer):
    program_manager = UserSerializer(read_only=True)
    
    class Meta:
        model = Program
        fields = '__all__'


class ProjectSerializer(serializers.ModelSerializer):
    project_lead = UserSerializer(read_only=True)
    
    class Meta:
        model = Project
        fields = '__all__'


class TreePlantingSerializer(serializers.ModelSerializer):
    farmer = UserSerializer(read_only=True)
    
    class Meta:
        model = TreePlanting
        fields = '__all__'
        read_only_fields = ['farmer']


class TrainingSerializer(serializers.ModelSerializer):
    trainer = UserSerializer(read_only=True)
    
    class Meta:
        model = Training
        fields = '__all__'


class ProgramProgressSerializer(serializers.Serializer):
    progress = serializers.IntegerField(min_value=0, max_value=100)
    beneficiaries_reached = serializers.IntegerField(min_value=0)
    actual_spent = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)