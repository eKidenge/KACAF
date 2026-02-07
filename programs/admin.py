from django.contrib import admin
from .models import Program, Project, TreePlanting, Training


class ProjectInline(admin.TabularInline):
    model = Project
    extra = 0
    fields = ('title', 'status', 'trees_target', 'trees_planted', 'start_date')
    readonly_fields = ('created_at',)


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ('title', 'program_type', 'county', 'status', 'progress', 'start_date', 'program_manager')
    list_filter = ('program_type', 'status', 'county')
    search_fields = ('title', 'description', 'objectives')
    filter_horizontal = ('team_members',)
    date_hierarchy = 'start_date'
    inlines = [ProjectInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'program_type', 'description', 'objectives')
        }),
        ('Location', {
            'fields': ('county', 'sub_counties', 'wards')
        }),
        ('Timeline', {
            'fields': ('start_date', 'end_date', 'duration_months')
        }),
        ('Budget', {
            'fields': ('estimated_budget', 'actual_spent')
        }),
        ('Team & Partners', {
            'fields': ('program_manager', 'team_members', 'partners')
        }),
        ('Status & Progress', {
            'fields': ('status', 'progress', 'beneficiaries_target', 'beneficiaries_reached')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')


class TreePlantingInline(admin.TabularInline):
    model = TreePlanting
    extra = 0
    fields = ('farmer', 'tree_type', 'species', 'quantity', 'planting_date')
    raw_id_fields = ('farmer',)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'program', 'status', 'trees_target', 'trees_planted', 'start_date', 'project_lead')
    list_filter = ('status', 'program')
    search_fields = ('title', 'description')
    filter_horizontal = ('volunteers',)
    raw_id_fields = ('program', 'project_lead')
    date_hierarchy = 'start_date'
    inlines = [TreePlantingInline]
    
    fieldsets = (
        ('Project Details', {
            'fields': ('program', 'title', 'description')
        }),
        ('Targets', {
            'fields': ('trees_target', 'trees_planted', 'area_coverage', 'carbon_sequestration')
        }),
        ('Location', {
            'fields': ('gps_coordinates', 'land_owner', 'land_size')
        }),
        ('Timeline', {
            'fields': ('start_date', 'end_date')
        }),
        ('Budget', {
            'fields': ('budget',)
        }),
        ('Team', {
            'fields': ('project_lead', 'volunteers')
        }),
        ('Status', {
            'fields': ('status', 'created_at', 'updated_at')
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')


@admin.register(TreePlanting)
class TreePlantingAdmin(admin.ModelAdmin):
    list_display = ('species', 'tree_type', 'farmer', 'quantity', 'planting_date', 'survival_rate', 'project')
    list_filter = ('tree_type', 'planting_date')
    search_fields = ('species', 'farmer__first_name', 'farmer__last_name', 'planting_site')
    raw_id_fields = ('project', 'farmer')
    date_hierarchy = 'planting_date'
    
    fieldsets = (
        ('Planting Details', {
            'fields': ('project', 'farmer', 'tree_type', 'species', 'quantity', 'planting_date')
        }),
        ('Location', {
            'fields': ('planting_site', 'gps_coordinates')
        }),
        ('Monitoring', {
            'fields': ('survival_rate', 'last_monitoring_date', 'monitoring_notes', 'photo')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Training)
class TrainingAdmin(admin.ModelAdmin):
    list_display = ('title', 'training_type', 'date', 'location', 'trainer', 'max_participants')
    list_filter = ('training_type', 'date')
    search_fields = ('title', 'description', 'location')
    filter_horizontal = ('participants',)
    raw_id_fields = ('program', 'trainer')
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Training Details', {
            'fields': ('program', 'title', 'training_type', 'description')
        }),
        ('Schedule', {
            'fields': ('date', 'start_time', 'end_time', 'location')
        }),
        ('Participants', {
            'fields': ('trainer', 'participants', 'max_participants')
        }),
        ('Materials', {
            'fields': ('agenda', 'materials', 'photos')
        }),
        ('Feedback', {
            'fields': ('average_rating', 'feedback_summary')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')