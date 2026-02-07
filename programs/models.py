from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone


User = get_user_model()


class Program(models.Model):
    PROGRAM_TYPE = (
        ('agroforestry', 'Agroforestry'),
        ('climate_smart_ag', 'Climate-Smart Agriculture'),
        ('biodiversity', 'Biodiversity Conservation'),
        ('restoration', 'Ecosystem Restoration'),
        ('education', 'Environmental Education'),
        ('capacity', 'Capacity Building'),
        ('policy', 'Policy Advocacy'),
    )
    
    STATUS_CHOICES = (
        ('planning', 'Planning'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('suspended', 'Suspended'),
    )
    
    title = models.CharField(max_length=200)
    program_type = models.CharField(max_length=30, choices=PROGRAM_TYPE)
    description = models.TextField()
    objectives = models.TextField()
    
    # Location
    county = models.CharField(max_length=100, default='West Pokot')
    sub_counties = models.CharField(max_length=500, help_text="Comma-separated list of sub-counties")
    wards = models.CharField(max_length=500, help_text="Comma-separated list of wards", null=True, blank=True)
    
    # Timeline
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    duration_months = models.IntegerField(help_text="Estimated duration in months")
    
    # Budget
    estimated_budget = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    actual_spent = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # Team
    program_manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='managed_programs')
    team_members = models.ManyToManyField(User, related_name='programs_involved', blank=True)
    
    # Partnerships
    partners = models.TextField(help_text="List of partner organizations", null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planning')
    progress = models.IntegerField(default=0, help_text="Progress percentage")
    
    # Monitoring
    beneficiaries_target = models.IntegerField(default=0)
    beneficiaries_reached = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title


class Project(models.Model):
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='projects')
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    # Specifics
    trees_target = models.IntegerField(default=0, help_text="Target number of trees to plant")
    trees_planted = models.IntegerField(default=0)
    area_coverage = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Area in hectares")
    carbon_sequestration = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Estimated CO2 sequestration in tons")
    
    # Location details
    gps_coordinates = models.CharField(max_length=100, null=True, blank=True, help_text="Latitude,Longitude")
    land_owner = models.CharField(max_length=200, null=True, blank=True)
    land_size = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Land size in acres")
    
    # Timeline
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    
    # Budget
    budget = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # Team
    project_lead = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='led_projects')
    volunteers = models.ManyToManyField(User, related_name='volunteered_projects', blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=[
        ('planned', 'Planned'),
        ('approved', 'Approved'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('monitoring', 'Under Monitoring'),
    ], default='planned')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.program.title} - {self.title}"


class TreePlanting(models.Model):
    TREE_TYPE = (
        ('indigenous', 'Indigenous'),
        ('fruit', 'Fruit Tree'),
        ('timber', 'Timber Tree'),
        ('fodder', 'Fodder Tree'),
        ('medicinal', 'Medicinal Tree'),
        ('ornamental', 'Ornamental'),
    )
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tree_plantings')
    farmer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trees_planted')
    tree_type = models.CharField(max_length=20, choices=TREE_TYPE)
    species = models.CharField(max_length=100)
    quantity = models.IntegerField(default=1)
    planting_date = models.DateField()
    
    # Location
    planting_site = models.CharField(max_length=200)
    gps_coordinates = models.CharField(max_length=100, null=True, blank=True)
    
    # Monitoring
    survival_rate = models.IntegerField(default=100, help_text="Percentage")
    last_monitoring_date = models.DateField(null=True, blank=True)
    monitoring_notes = models.TextField(null=True, blank=True)
    
    # Images
    photo = models.ImageField(upload_to='trees/', null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-planting_date']
        verbose_name_plural = "Tree Plantings"
    
    def __str__(self):
        return f"{self.species} - {self.farmer.get_full_name()}"


class Training(models.Model):
    TRAINING_TYPE = (
        ('agroforestry', 'Agroforestry Practices'),
        ('climate_smart', 'Climate-Smart Agriculture'),
        ('nursery', 'Tree Nursery Management'),
        ('conservation', 'Soil & Water Conservation'),
        ('business', 'Agribusiness'),
        ('leadership', 'Community Leadership'),
    )
    
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='trainings', null=True, blank=True)
    title = models.CharField(max_length=200)
    training_type = models.CharField(max_length=30, choices=TRAINING_TYPE)
    description = models.TextField()
    
    # Details
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    location = models.CharField(max_length=200)
    
    # Participants
    trainer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='conducted_trainings')
    participants = models.ManyToManyField(User, related_name='attended_trainings', blank=True)
    max_participants = models.IntegerField(default=30)
    
    # Materials
    agenda = models.TextField(null=True, blank=True)
    materials = models.FileField(upload_to='trainings/materials/', null=True, blank=True)
    photos = models.ImageField(upload_to='trainings/photos/', null=True, blank=True)
    
    # Feedback
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    feedback_summary = models.TextField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.title} - {self.date}"