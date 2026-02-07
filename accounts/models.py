from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ('member', 'Member'),
        ('executive', 'Executive Committee'),
        ('staff', 'Staff'),
        ('donor', 'Donor/Partner'),
        ('admin', 'Administrator'),
    )
    
    MEMBERSHIP_TYPE = (
        ('ordinary', 'Ordinary Member'),
        ('executive', 'Executive Member'),
        ('honorary', 'Honorary Member'),
    )
    
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='member')
    membership_type = models.CharField(max_length=20, choices=MEMBERSHIP_TYPE, null=True, blank=True)
    phone = models.CharField(max_length=15, null=True, blank=True)
    id_number = models.CharField(max_length=20, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    county = models.CharField(max_length=100, default='West Pokot')
    sub_county = models.CharField(max_length=100, null=True, blank=True)
    ward = models.CharField(max_length=100, null=True, blank=True)
    village = models.CharField(max_length=100, null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    join_date = models.DateField(default=timezone.now)
    is_verified = models.BooleanField(default=False)
    verification_date = models.DateField(null=True, blank=True)
    
    # Executive Committee Position (if applicable)
    position = models.CharField(max_length=100, null=True, blank=True)
    position_start_date = models.DateField(null=True, blank=True)
    
    class Meta:
        ordering = ['-date_joined']
    
    def __str__(self):
        return f"{self.get_full_name()} - {self.get_user_type_display()}"


class MemberProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='member_profile')
    occupation = models.CharField(max_length=100, null=True, blank=True)
    education_level = models.CharField(max_length=100, null=True, blank=True)
    farm_size = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # in acres
    trees_planted = models.IntegerField(default=0)
    conservation_practices = models.TextField(null=True, blank=True)
    skills = models.TextField(null=True, blank=True)
    interests = models.TextField(null=True, blank=True)
    
    # Contact preferences
    receive_newsletter = models.BooleanField(default=True)
    receive_sms = models.BooleanField(default=True)
    receive_email = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Profile: {self.user.get_full_name()}"


class ExecutiveCommittee(models.Model):
    POSITIONS = (
        ('chairperson', 'Chairperson'),
        ('vice_chairperson', 'Vice Chairperson'),
        ('secretary', 'Secretary'),
        ('assistant_secretary', 'Assistant Secretary'),
        ('treasurer', 'Treasurer'),
        ('organizing_secretary', 'Organizing Secretary'),
        ('committee_member', 'Committee Member'),
    )
    
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='executive_role')
    position = models.CharField(max_length=50, choices=POSITIONS)
    order = models.IntegerField(help_text="Order of precedence")
    responsibilities = models.TextField()
    term_start = models.DateField()
    term_end = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Special permissions (according to constitution)
    can_suspend_members = models.BooleanField(default=False)
    can_manage_finances = models.BooleanField(default=False)
    can_represent_legally = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order']
        verbose_name_plural = "Executive Committee"
    
    def __str__(self):
        return f"{self.get_position_display()}: {self.user.get_full_name()}"