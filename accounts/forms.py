from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, MemberProfile


class UserRegistrationForm(UserCreationForm):
    # Personal Information
    phone = forms.CharField(
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '07XXXXXXXX'
        })
    )
    id_number = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'National ID/Passport'
        })
    )
    date_of_birth = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    gender = forms.ChoiceField(
        choices=[('', 'Select Gender'), ('male', 'Male'), ('female', 'Female'), ('other', 'Other')],
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    occupation = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your occupation'
        })
    )
    education_level = forms.ChoiceField(
        choices=[
            ('', 'Select Education Level'),
            ('primary', 'Primary'),
            ('secondary', 'Secondary'),
            ('certificate', 'Certificate'),
            ('diploma', 'Diploma'),
            ('degree', 'Degree'),
            ('masters', 'Masters'),
            ('phd', 'PhD')
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    profile_picture = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        })
    )

    # Location Information
    county = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your county'
        })
    )
    sub_county = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Sub-county'
        })
    )
    ward = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your ward'
        })
    )
    village = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Village/Estate'
        })
    )
    postal_address = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'P.O. Box'
        })
    )
    postal_code = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Postal code'
        })
    )

    # Membership Information
    user_type = forms.ChoiceField(
        choices=[
            ('member', 'Individual Member'),
            ('farmer', 'Farmer'),
            ('youth', 'Youth'),
            ('organization', 'Organization'),
            ('executive', 'Executive Committee'),
            ('staff', 'Staff'),
            ('donor', 'Donor/Partner'),
            ('admin', 'Administrator')
        ],
        widget=forms.RadioSelect(),
        initial='member'
    )
    organization_name = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Organization name'
        })
    )
    referral_source = forms.ChoiceField(
        choices=[
            ('', 'Select how you heard about us'),
            ('social_media', 'Social Media'),
            ('friend', 'Friend/Family'),
            ('event', 'Event/Workshop'),
            ('radio', 'Radio'),
            ('newspaper', 'Newspaper'),
            ('other', 'Other')
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    interests = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Your areas of interest in agroforestry and climate action'
        })
    )
    skills = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Your relevant skills'
        })
    )

    # Consent Fields
    newsletter_subscription = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    terms_accepted = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    data_consent = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    class Meta:
        model = CustomUser
        fields = ['email', 'first_name', 'last_name']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'your@email.com'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your first name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your last name'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Style password fields
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm password'
        })
        # Remove username field if you don't want it
        if 'username' in self.fields:
            self.fields['username'].widget = forms.HiddenInput()
            self.fields['username'].required = False

    def save(self, commit=True):
        user = super().save(commit=False)
        
        # Set all the fields from form to CustomUser
        user.phone = self.cleaned_data.get('phone')
        user.id_number = self.cleaned_data.get('id_number')
        user.date_of_birth = self.cleaned_data.get('date_of_birth')
        user.gender = self.cleaned_data.get('gender')
        user.occupation = self.cleaned_data.get('occupation')
        user.education_level = self.cleaned_data.get('education_level')
        user.profile_picture = self.cleaned_data.get('profile_picture')
        user.county = self.cleaned_data.get('county')
        user.sub_county = self.cleaned_data.get('sub_county')
        user.ward = self.cleaned_data.get('ward')
        user.village = self.cleaned_data.get('village')
        user.postal_address = self.cleaned_data.get('postal_address')
        user.postal_code = self.cleaned_data.get('postal_code')
        user.user_type = self.cleaned_data.get('user_type')
        user.organization_name = self.cleaned_data.get('organization_name')
        user.referral_source = self.cleaned_data.get('referral_source')
        user.interests = self.cleaned_data.get('interests')
        user.skills = self.cleaned_data.get('skills')
        user.newsletter_subscription = self.cleaned_data.get('newsletter_subscription', False)
        user.terms_accepted = self.cleaned_data.get('terms_accepted', False)
        user.data_consent = self.cleaned_data.get('data_consent', False)
        
        # Set username from email if username is hidden
        if not user.username:
            user.username = self.cleaned_data.get('email').split('@')[0]
        
        if commit:
            user.save()
        return user