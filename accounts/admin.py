from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, MemberProfile, ExecutiveCommittee


class MemberProfileInline(admin.TabularInline):
    model = MemberProfile
    extra = 0
    # Only show fields that actually exist in MemberProfile
    fields = ('farm_size', 'trees_planted', 'conservation_practices', 
              'receive_newsletter', 'receive_sms', 'receive_email')
    readonly_fields = ('created_at', 'updated_at')


class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'get_full_name', 'user_type', 
                   'membership_type', 'phone', 'county', 'is_verified', 'is_staff')
    list_filter = ('user_type', 'membership_type', 'is_verified', 'is_active', 
                  'is_staff', 'county', 'gender', 'education_level')
    search_fields = ('username', 'email', 'first_name', 'last_name', 
                    'phone', 'id_number', 'id_number')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'id_number',
                      'date_of_birth', 'gender', 'profile_picture', 'bio')
        }),
        ('Location Information', {
            'fields': ('county', 'sub_county', 'ward', 'village', 
                      'postal_address', 'postal_code')
        }),
        ('Membership Information', {
            'fields': ('user_type', 'membership_type', 'organization_name',
                      'referral_source', 'interests', 'skills', 'join_date',
                      'is_verified', 'verification_date')
        }),
        ('Consent & Preferences', {
            'fields': ('newsletter_subscription', 'terms_accepted', 'data_consent')
        }),
        ('Executive Committee', {
            'fields': ('position', 'position_start_date'),
            'classes': ('collapse',)
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined')
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'user_type',
                      'first_name', 'last_name', 'phone', 'id_number', 'county'),
        }),
    )
    
    inlines = [MemberProfileInline]
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'Full Name'


class MemberProfileAdmin(admin.ModelAdmin):
    # REMOVED occupation and education_level - they don't exist in MemberProfile anymore
    list_display = ('user', 'farm_size', 'trees_planted', 'events_attended', 
                   'training_completed', 'receive_newsletter')
    list_filter = ('receive_newsletter', 'receive_sms', 'receive_email')
    search_fields = ('user__first_name', 'user__last_name', 'user__email')
    raw_id_fields = ('user',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Member', {
            'fields': ('user',)
        }),
        ('Agricultural Information', {
            'fields': ('farm_size', 'trees_planted', 'conservation_practices')
        }),
        ('Activity Tracking', {
            'fields': ('total_donations', 'events_attended', 'training_completed')
        }),
        ('Contact Preferences', {
            'fields': ('receive_newsletter', 'receive_sms', 'receive_email')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class ExecutiveCommitteeAdmin(admin.ModelAdmin):
    list_display = ('user', 'position', 'order', 'term_start', 'term_end', 'is_active')
    list_filter = ('position', 'is_active')
    search_fields = ('user__first_name', 'user__last_name', 'position')
    raw_id_fields = ('user',)
    list_editable = ('order', 'is_active')
    ordering = ('order',)
    
    fieldsets = (
        (None, {
            'fields': ('user', 'position', 'order', 'is_active')
        }),
        ('Term Information', {
            'fields': ('term_start', 'term_end', 'responsibilities')
        }),
        ('Special Permissions', {
            'fields': ('can_suspend_members', 'can_manage_finances', 'can_represent_legally'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(MemberProfile, MemberProfileAdmin)
admin.site.register(ExecutiveCommittee, ExecutiveCommitteeAdmin)