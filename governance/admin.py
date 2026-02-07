from django.contrib import admin
from .models import GeneralAssembly, Resolution, MembershipApplication, DisciplinaryAction


class ResolutionInline(admin.TabularInline):
    model = Resolution
    extra = 0
    fields = ('title', 'resolution_type', 'status', 'chairperson_decision')
    readonly_fields = ('created_at',)


@admin.register(GeneralAssembly)
class GeneralAssemblyAdmin(admin.ModelAdmin):
    list_display = ('title', 'meeting_type', 'date', 'location', 'chairperson', 'status', 'is_quorum_met')
    list_filter = ('meeting_type', 'status', 'date')
    search_fields = ('title', 'agenda', 'location')
    date_hierarchy = 'date'
    filter_horizontal = ('members_present',)
    inlines = [ResolutionInline]
    
    fieldsets = (
        ('Meeting Details', {
            'fields': ('title', 'meeting_type', 'date', 'location', 'agenda')
        }),
        ('Officials', {
            'fields': ('chairperson', 'secretary')
        }),
        ('Attendance', {
            'fields': ('members_present', 'total_attendance', 'is_quorum_met', 'quorum_required')
        }),
        ('Documents', {
            'fields': ('minutes_file', 'attendance_sheet', 'agenda_file')
        }),
        ('Status', {
            'fields': ('status', 'created_at', 'updated_at')
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Resolution)
class ResolutionAdmin(admin.ModelAdmin):
    list_display = ('title', 'resolution_type', 'general_assembly', 'status', 'chairperson_decision', 'created_at')
    list_filter = ('resolution_type', 'status', 'chairperson_decision', 'general_assembly')
    search_fields = ('title', 'description')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Resolution Details', {
            'fields': ('title', 'description', 'resolution_type', 'general_assembly')
        }),
        ('Proposal', {
            'fields': ('proposed_by', 'seconded_by')
        }),
        ('Voting (Advisory)', {
            'fields': ('votes_for', 'votes_against', 'votes_abstain')
        }),
        ('Chairperson Decision', {
            'fields': ('chairperson_decision', 'chairperson_comments', 'decision_date')
        }),
        ('Implementation', {
            'fields': ('status', 'implementation_notes', 'date_implemented')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')


@admin.register(MembershipApplication)
class MembershipApplicationAdmin(admin.ModelAdmin):
    list_display = ('applicant', 'applied_membership_type', 'status', 'chairperson_decision', 'created_at')
    list_filter = ('status', 'chairperson_decision', 'applied_membership_type')
    search_fields = ('applicant__first_name', 'applicant__last_name', 'applicant__email', 'motivation_letter')
    date_hierarchy = 'created_at'
    list_editable = ('status', 'chairperson_decision')
    
    fieldsets = (
        ('Applicant Info', {
            'fields': ('applicant', 'applied_membership_type')
        }),
        ('Application Details', {
            'fields': ('motivation_letter', 'relevant_experience', 'expected_contribution', 'supporting_documents')
        }),
        ('Review Process', {
            'fields': ('reviewed_by', 'review_date', 'review_notes')
        }),
        ('Chairperson Decision', {
            'fields': ('chairperson_decision', 'chairperson_comments', 'decision_date')
        }),
        ('Status', {
            'fields': ('status', 'created_at', 'updated_at')
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def save_model(self, request, obj, form, change):
        if obj.chairperson_decision == 'approved' and obj.status == 'approved':
            # Update user's membership type
            obj.applicant.membership_type = obj.applied_membership_type
            obj.applicant.is_verified = True
            obj.applicant.verification_date = timezone.now()
            obj.applicant.save()
        super().save_model(request, obj, form, change)


@admin.register(DisciplinaryAction)
class DisciplinaryActionAdmin(admin.ModelAdmin):
    list_display = ('member', 'action_type', 'grounds', 'issued_by', 'issued_date', 'status')
    list_filter = ('action_type', 'grounds', 'status', 'is_summary_suspension')
    search_fields = ('member__first_name', 'member__last_name', 'description', 'evidence')
    date_hierarchy = 'issued_date'
    
    fieldsets = (
        ('Member & Action', {
            'fields': ('member', 'action_type', 'grounds', 'description', 'evidence')
        }),
        ('Suspension Details', {
            'fields': ('is_summary_suspension', 'suspension_start', 'suspension_end')
        }),
        ('Issuance', {
            'fields': ('issued_by', 'issued_date')
        }),
        ('Appeal Process', {
            'fields': ('appeal_filed', 'appeal_date', 'appeal_details')
        }),
        ('Review & Final Decision', {
            'fields': ('review_committee_notes', 'final_decision', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')