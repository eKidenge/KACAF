from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, MemberProfile, ExecutiveCommittee


class MemberProfileInline(admin.TabularInline):
    model = MemberProfile
    extra = 0


class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'get_full_name', 'user_type', 'membership_type', 'is_active', 'is_staff')
    list_filter = ('user_type', 'membership_type', 'is_active', 'is_staff', 'county')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone', 'id_number')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 'phone', 'date_of_birth', 'profile_picture')}),
        ('Membership Info', {'fields': ('user_type', 'membership_type', 'id_number', 'county', 'sub_county', 'ward', 'village', 'bio')}),
        ('Executive Info', {'fields': ('position', 'position_start_date')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined', 'join_date', 'verification_date')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'user_type', 'first_name', 'last_name', 'phone'),
        }),
    )
    
    inlines = [MemberProfileInline]
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'Full Name'


class MemberProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'occupation', 'education_level', 'farm_size', 'trees_planted')
    list_filter = ('education_level',)
    search_fields = ('user__first_name', 'user__last_name', 'user__email', 'occupation')
    raw_id_fields = ('user',)


class ExecutiveCommitteeAdmin(admin.ModelAdmin):
    list_display = ('user', 'position', 'term_start', 'term_end', 'is_active')
    list_filter = ('position', 'is_active')
    search_fields = ('user__first_name', 'user__last_name', 'position')
    raw_id_fields = ('user',)
    list_editable = ('is_active',)


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(MemberProfile, MemberProfileAdmin)
admin.site.register(ExecutiveCommittee, ExecutiveCommitteeAdmin)