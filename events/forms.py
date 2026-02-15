from django import forms
from django.utils import timezone
from .models import Event, EventRegistration, EventPhoto, EventResource

class EventForm(forms.ModelForm):
    """Form for creating and editing events"""
    
    class Meta:
        model = Event
        fields = [
            'title', 'event_type', 'description',
            'start_datetime', 'end_datetime', 'location', 'gps_coordinates', 'address',
            'contact_person', 'contact_phone', 'contact_email',
            'max_participants', 'min_participants', 'requires_registration',
            'registration_deadline', 'registration_fee',
            'status', 'is_public', 'is_featured',
            'agenda', 'requirements', 'materials_provided',
            'transport_arranged', 'meals_provided', 'accommodation_provided',
            'budget', 'actual_cost',
            'banner_image'
        ]
        widgets = {
            'start_datetime': forms.DateTimeInput(
                attrs={'type': 'datetime-local', 'class': 'form-control'},
                format='%Y-%m-%dT%H:%M'
            ),
            'end_datetime': forms.DateTimeInput(
                attrs={'type': 'datetime-local', 'class': 'form-control'},
                format='%Y-%m-%dT%H:%M'
            ),
            'registration_deadline': forms.DateTimeInput(
                attrs={'type': 'datetime-local', 'class': 'form-control'},
                format='%Y-%m-%dT%H:%M'
            ),
            'description': forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
            'agenda': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'requirements': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'materials_provided': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'gps_coordinates': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 1.2345, 36.7890'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '07XXXXXXXX'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'max_participants': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'min_participants': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'registration_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'budget': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'actual_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'event_type': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'requires_registration': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'transport_arranged': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'meals_provided': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'accommodation_provided': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'banner_image': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default values for new events
        if not self.instance.pk:
            self.fields['status'].initial = 'draft'
            self.fields['requires_registration'].initial = True
            self.fields['is_public'].initial = True
            self.fields['max_participants'].initial = 50
            self.fields['min_participants'].initial = 1
    
    def clean(self):
        cleaned_data = super().clean()
        start_datetime = cleaned_data.get('start_datetime')
        end_datetime = cleaned_data.get('end_datetime')
        registration_deadline = cleaned_data.get('registration_deadline')
        requires_registration = cleaned_data.get('requires_registration')
        
        # Validate dates
        if start_datetime and end_datetime:
            if start_datetime >= end_datetime:
                raise forms.ValidationError('End date/time must be after start date/time')
        
        # Validate registration deadline
        if requires_registration and registration_deadline and start_datetime:
            if registration_deadline >= start_datetime:
                raise forms.ValidationError('Registration deadline must be before the event start date')
        
        # Validate GPS coordinates format
        gps_coordinates = cleaned_data.get('gps_coordinates')
        if gps_coordinates:
            try:
                lat, lng = gps_coordinates.replace(' ', '').split(',')
                float(lat)
                float(lng)
            except (ValueError, AttributeError):
                raise forms.ValidationError('GPS coordinates must be in format: latitude, longitude (e.g., 1.2345, 36.7890)')
        
        return cleaned_data


class EventRegistrationForm(forms.ModelForm):
    """Form for event registration"""
    
    class Meta:
        model = EventRegistration
        fields = [
            'dietary_requirements', 'special_needs',
            'emergency_contact', 'emergency_phone'
        ]
        widgets = {
            'dietary_requirements': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'special_needs': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'emergency_contact': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '07XXXXXXXX'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event', None)
        super().__init__(*args, **kwargs)


class EventPhotoForm(forms.ModelForm):
    """Form for uploading event photos"""
    
    class Meta:
        model = EventPhoto
        fields = ['title', 'caption', 'photo', 'is_featured']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'caption': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class EventResourceForm(forms.ModelForm):
    """Form for uploading event resources"""
    
    class Meta:
        model = EventResource
        fields = ['title', 'resource_type', 'description', 'file', 'is_public']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'resource_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class EventFilterForm(forms.Form):
    """Form for filtering events in list view"""
    
    event_type = forms.ChoiceField(
        choices=[('', 'All Types')] + list(Event.EVENT_TYPE),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + list(Event.STATUS_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search events...'})
    )