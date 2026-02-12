# programs/forms.py
from django import forms
from .models import Program, Project, TreePlanting, Training

class ProgramForm(forms.ModelForm):
    """Form for creating and editing programs"""
    
    class Meta:
        model = Program
        fields = [
            'title',
            'program_type',
            'description',
            'objectives',
            'county',
            'sub_counties',
            'wards',
            'start_date',
            'end_date',
            'duration_months',
            'estimated_budget',
            'actual_spent',
            'program_manager',
            'partners',
            'status',
            'progress',
            'beneficiaries_target',
            'beneficiaries_reached',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'program_type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'objectives': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'county': forms.TextInput(attrs={'class': 'form-control'}),
            'sub_counties': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Comma-separated list'}),
            'wards': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Comma-separated list'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'duration_months': forms.NumberInput(attrs={'class': 'form-control'}),
            'estimated_budget': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'actual_spent': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'program_manager': forms.Select(attrs={'class': 'form-control'}),
            'partners': forms.Textarea(attrs={'rows': 2, 'class': 'form-control', 'placeholder': 'List partner organizations'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'progress': forms.NumberInput(attrs={'class': 'form-control', 'step': '1', 'min': '0', 'max': '100'}),
            'beneficiaries_target': forms.NumberInput(attrs={'class': 'form-control'}),
            'beneficiaries_reached': forms.NumberInput(attrs={'class': 'form-control'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError("End date cannot be before start date.")
        
        return cleaned_data


class ProjectForm(forms.ModelForm):
    """Form for creating and editing projects"""
    
    class Meta:
        model = Project
        fields = [
            'program',
            'title',
            'description',
            'trees_target',
            'trees_planted',
            'area_coverage',
            'carbon_sequestration',
            'gps_coordinates',
            'land_owner',
            'land_size',
            'start_date',
            'end_date',
            'budget',
            'project_lead',
            'status',
        ]
        widgets = {
            'program': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'trees_target': forms.NumberInput(attrs={'class': 'form-control'}),
            'trees_planted': forms.NumberInput(attrs={'class': 'form-control'}),
            'area_coverage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'carbon_sequestration': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'gps_coordinates': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Latitude,Longitude'}),
            'land_owner': forms.TextInput(attrs={'class': 'form-control'}),
            'land_size': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'budget': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'project_lead': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active programs
        self.fields['program'].queryset = Program.objects.all()
        # Only show users who are staff or program managers
        self.fields['project_lead'].queryset = User.objects.filter(is_staff=True)


class TreePlantingForm(forms.ModelForm):
    """Form for creating and editing tree planting records"""
    
    class Meta:
        model = TreePlanting
        fields = [
            'project',
            'tree_type',
            'species',
            'quantity',
            'planting_date',
            'planting_site',
            'gps_coordinates',
            'survival_rate',
            'last_monitoring_date',
            'monitoring_notes',
            'photo',
        ]
        widgets = {
            'project': forms.Select(attrs={'class': 'form-control'}),
            'tree_type': forms.Select(attrs={'class': 'form-control'}),
            'species': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'planting_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'planting_site': forms.TextInput(attrs={'class': 'form-control'}),
            'gps_coordinates': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Latitude,Longitude'}),
            'survival_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '1', 'min': '0', 'max': '100'}),
            'last_monitoring_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'monitoring_notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active projects
        self.fields['project'].queryset = Project.objects.filter(status__in=['ongoing', 'approved'])
        self.fields['survival_rate'].required = False
        self.fields['last_monitoring_date'].required = False
        self.fields['monitoring_notes'].required = False
        self.fields['photo'].required = False
        self.fields['gps_coordinates'].required = False


class TrainingForm(forms.ModelForm):
    """Form for creating and editing trainings"""
    
    class Meta:
        model = Training
        fields = [
            'program',
            'title',
            'training_type',
            'description',
            'date',
            'start_time',
            'end_time',
            'location',
            'trainer',
            'max_participants',
            'agenda',
            'materials',
            'photos',
        ]
        widgets = {
            'program': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'training_type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'trainer': forms.Select(attrs={'class': 'form-control'}),
            'max_participants': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'agenda': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'materials': forms.FileInput(attrs={'class': 'form-control'}),
            'photos': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['program'].required = False
        self.fields['agenda'].required = False
        self.fields['materials'].required = False
        self.fields['photos'].required = False
        # Only show active programs
        self.fields['program'].queryset = Program.objects.filter(status='active')
        # Only show users who are staff or trainers
        self.fields['trainer'].queryset = User.objects.filter(is_staff=True)
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        if start_time and end_time and start_time >= end_time:
            raise forms.ValidationError("End time must be after start time.")
        
        return cleaned_data