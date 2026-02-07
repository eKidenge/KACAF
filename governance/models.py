from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone


User = get_user_model()


class GeneralAssembly(models.Model):
    MEETING_TYPE = (
        ('annual', 'Annual General Meeting'),
        ('special', 'Special General Meeting'),
        ('emergency', 'Emergency Meeting'),
    )
    
    title = models.CharField(max_length=200)
    meeting_type = models.CharField(max_length=20, choices=MEETING_TYPE, default='annual')
    date = models.DateTimeField()
    location = models.CharField(max_length=200)
    agenda = models.TextField()
    chairperson = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='chaired_meetings')
    secretary = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='recorded_meetings')
    
    # Attendance
    members_present = models.ManyToManyField(User, related_name='attended_assemblies', blank=True)
    total_attendance = models.IntegerField(default=0)
    
    # Documents
    minutes_file = models.FileField(upload_to='governance/assembly/minutes/', null=True, blank=True)
    attendance_sheet = models.FileField(upload_to='governance/assembly/attendance/', null=True, blank=True)
    agenda_file = models.FileField(upload_to='governance/assembly/agendas/', null=True, blank=True)
    
    # Status
    is_quorum_met = models.BooleanField(default=False)
    quorum_required = models.IntegerField(default=67)  # 2/3 default
    status = models.CharField(max_length=20, choices=[
        ('scheduled', 'Scheduled'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], default='scheduled')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date']
        verbose_name_plural = "General Assemblies"
    
    def __str__(self):
        return f"{self.get_meeting_type_display()}: {self.title} - {self.date.strftime('%Y-%m-%d')}"


class Resolution(models.Model):
    RESOLUTION_TYPE = (
        ('advisory', 'Advisory'),
        ('binding', 'Binding'),
        ('strategic', 'Strategic'),
        ('financial', 'Financial'),
        ('governance', 'Governance'),
    )
    
    STATUS_CHOICES = (
        ('proposed', 'Proposed'),
        ('discussed', 'Under Discussion'),
        ('voted', 'Voted On'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('implemented', 'Implemented'),
    )
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    resolution_type = models.CharField(max_length=20, choices=RESOLUTION_TYPE, default='advisory')
    general_assembly = models.ForeignKey(GeneralAssembly, on_delete=models.CASCADE, related_name='resolutions')
    proposed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='proposed_resolutions')
    seconded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='seconded_resolutions')
    
    # Voting (according to constitution - advisory only)
    votes_for = models.IntegerField(default=0)
    votes_against = models.IntegerField(default=0)
    votes_abstain = models.IntegerField(default=0)
    
    # Chairperson's decision (final according to constitution)
    chairperson_decision = models.CharField(max_length=20, choices=[
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('pending', 'Pending Review'),
        ('referred', 'Referred to Committee'),
    ], default='pending')
    
    chairperson_comments = models.TextField(null=True, blank=True)
    decision_date = models.DateTimeField(null=True, blank=True)
    
    # Implementation
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='proposed')
    implementation_notes = models.TextField(null=True, blank=True)
    date_implemented = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Resolution: {self.title}"


class MembershipApplication(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('suspended', 'Suspended'),
    )
    
    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='membership_applications')
    applied_membership_type = models.CharField(max_length=20, choices=User.MEMBERSHIP_TYPE)
    
    # Application details
    motivation_letter = models.TextField()
    relevant_experience = models.TextField()
    expected_contribution = models.TextField()
    
    # Review process
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_applications')
    review_date = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(null=True, blank=True)
    
    # Chairperson's decision (final)
    chairperson_decision = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], default='pending')
    chairperson_comments = models.TextField(null=True, blank=True)
    decision_date = models.DateTimeField(null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    supporting_documents = models.FileField(upload_to='membership/applications/', null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Membership Application: {self.applicant.get_full_name()}"


class DisciplinaryAction(models.Model):
    ACTION_TYPE = (
        ('warning', 'Warning'),
        ('suspension', 'Suspension'),
        ('expulsion', 'Expulsion'),
        ('reprimand', 'Reprimand'),
    )
    
    GROUNDS_CHOICES = (
        ('misconduct', 'Misconduct'),
        ('negligence', 'Gross Negligence'),
        ('insubordination', 'Insubordination'),
        ('abuse_of_office', 'Abuse of Office'),
        ('financial_impropriety', 'Financial Impropriety'),
        ('reputation_damage', 'Damage to Organization Reputation'),
        ('constitution_violation', 'Violation of Constitution'),
    )
    
    member = models.ForeignKey(User, on_delete=models.CASCADE, related_name='disciplinary_actions')
    action_type = models.CharField(max_length=20, choices=ACTION_TYPE)
    grounds = models.CharField(max_length=30, choices=GROUNDS_CHOICES)
    description = models.TextField()
    evidence = models.TextField(null=True, blank=True)
    
    # Summary suspension (according to constitution)
    is_summary_suspension = models.BooleanField(default=False)
    suspension_start = models.DateTimeField(null=True, blank=True)
    suspension_end = models.DateTimeField(null=True, blank=True)
    
    # Issued by chairperson
    issued_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='issued_disciplinary_actions')
    issued_date = models.DateTimeField(default=timezone.now)
    
    # Appeal process
    appeal_filed = models.BooleanField(default=False)
    appeal_date = models.DateTimeField(null=True, blank=True)
    appeal_details = models.TextField(null=True, blank=True)
    
    # Review committee (ad-hoc)
    review_committee_notes = models.TextField(null=True, blank=True)
    final_decision = models.CharField(max_length=20, choices=[
        ('upheld', 'Upheld'),
        ('modified', 'Modified'),
        ('overturned', 'Overturned'),
    ], null=True, blank=True)
    
    # Final status
    status = models.CharField(max_length=20, choices=[
        ('active', 'Active'),
        ('appealed', 'Under Appeal'),
        ('resolved', 'Resolved'),
        ('cancelled', 'Cancelled'),
    ], default='active')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-issued_date']
    
    def __str__(self):
        return f"{self.get_action_type_display()} - {self.member.get_full_name()}"