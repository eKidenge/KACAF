from django.contrib import admin
from .models import Event, EventRegistration, EventPhoto, EventResource


class EventRegistrationInline(admin.TabularInline):
    model = EventRegistration
    extra = 0
    fields = ('participant', 'status', 'payment_status', 'attended')
    raw_id_fields = ('participant',)


class EventPhotoInline(admin.TabularInline):
    model = EventPhoto
    extra = 0
    fields = ('photo', 'title', 'caption', 'is_featured')
    readonly_fields = ('uploaded_at',)


class EventResourceInline(admin.TabularInline):
    model = EventResource
    extra = 0
    fields = ('title', 'resource_type', 'file', 'is_public')
    readonly_fields = ('uploaded_at', 'download_count')


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_type', 'start_datetime', 'location', 'status', 'is_public', 'total_registrations')
    list_filter = ('event_type', 'status', 'is_public', 'is_featured', 'start_datetime')
    search_fields = ('title', 'description', 'location', 'agenda')
    filter_horizontal = ('gallery',)
    date_hierarchy = 'start_datetime'
    inlines = [EventRegistrationInline, EventPhotoInline, EventResourceInline]
    
    fieldsets = (
        ('Event Information', {
            'fields': ('title', 'event_type', 'description', 'status', 'is_public', 'is_featured')
        }),
        ('Date & Time', {
            'fields': ('start_datetime', 'end_datetime')
        }),
        ('Location', {
            'fields': ('location', 'gps_coordinates', 'address')
        }),
        ('Organizer Details', {
            'fields': ('organizer', 'coordinator', 'contact_person', 'contact_phone', 'contact_email')
        }),
        ('Registration', {
            'fields': ('requires_registration', 'registration_deadline', 'max_participants', 'min_participants', 'registration_fee')
        }),
        ('Logistics', {
            'fields': ('agenda', 'requirements', 'materials_provided', 'transport_arranged', 'meals_provided', 'accommodation_provided')
        }),
        ('Budget', {
            'fields': ('budget', 'actual_cost')
        }),
        ('Media', {
            'fields': ('banner_image',)
        }),
        ('Statistics', {
            'fields': ('total_registrations', 'total_attendance')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'published_at')
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'total_registrations', 'total_attendance')
    
    def save_model(self, request, obj, form, change):
        if obj.status == 'published' and not obj.published_at:
            obj.published_at = timezone.now()
        super().save_model(request, obj, form, change)


@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = ('participant', 'event', 'status', 'payment_status', 'attended', 'registration_date')
    list_filter = ('status', 'payment_status', 'attended', 'event__event_type')
    search_fields = ('participant__first_name', 'participant__last_name', 'event__title')
    raw_id_fields = ('event', 'participant')
    date_hierarchy = 'registration_date'
    
    fieldsets = (
        ('Registration Details', {
            'fields': ('event', 'participant', 'status', 'registration_date', 'confirmation_date')
        }),
        ('Attendance', {
            'fields': ('check_in_time', 'check_out_time', 'attended')
        }),
        ('Payment', {
            'fields': ('payment_status', 'amount_paid', 'payment_method', 'payment_reference', 'payment_date')
        }),
        ('Additional Information', {
            'fields': ('dietary_requirements', 'special_needs', 'emergency_contact', 'emergency_phone')
        }),
        ('Feedback', {
            'fields': ('rating', 'feedback', 'notes')
        }),
    )
    
    readonly_fields = ('registration_date',)


@admin.register(EventPhoto)
class EventPhotoAdmin(admin.ModelAdmin):
    list_display = ('title', 'event', 'uploaded_by', 'uploaded_at', 'is_featured')
    list_filter = ('is_featured', 'uploaded_at')
    search_fields = ('title', 'caption', 'event__title')
    raw_id_fields = ('event', 'uploaded_by')
    date_hierarchy = 'uploaded_at'
    
    fieldsets = (
        ('Photo Details', {
            'fields': ('event', 'title', 'caption', 'photo')
        }),
        ('Metadata', {
            'fields': ('uploaded_by', 'uploaded_at', 'is_featured')
        }),
    )
    
    readonly_fields = ('uploaded_at',)


@admin.register(EventResource)
class EventResourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'event', 'resource_type', 'uploaded_by', 'uploaded_at', 'is_public', 'download_count')
    list_filter = ('resource_type', 'is_public', 'uploaded_at')
    search_fields = ('title', 'description', 'event__title')
    raw_id_fields = ('event', 'uploaded_by')
    date_hierarchy = 'uploaded_at'
    
    fieldsets = (
        ('Resource Details', {
            'fields': ('event', 'title', 'resource_type', 'description', 'file')
        }),
        ('Access', {
            'fields': ('is_public', 'download_count')
        }),
        ('Metadata', {
            'fields': ('uploaded_by', 'uploaded_at')
        }),
    )
    
    readonly_fields = ('uploaded_at', 'download_count')