from django.contrib import admin
from .models import DocumentCategory, Document, DocumentAccessLog, DocumentReview, DocumentTemplate


class DocumentAccessLogInline(admin.TabularInline):
    model = DocumentAccessLog
    extra = 0
    fields = ('user', 'access_type', 'accessed_at', 'ip_address')
    readonly_fields = ('accessed_at',)


class DocumentReviewInline(admin.TabularInline):
    model = DocumentReview
    extra = 0
    fields = ('reviewer', 'status', 'review_date', 'comments')
    readonly_fields = ('review_date',)


@admin.register(DocumentCategory)
class DocumentCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'order', 'document_count')
    list_filter = ('parent',)
    search_fields = ('name', 'description')
    ordering = ('order', 'name')
    
    fieldsets = (
        ('Category Information', {
            'fields': ('name', 'description', 'parent', 'order')
        }),
        ('Display', {
            'fields': ('icon',)
        }),
    )
    
    def document_count(self, obj):
        return obj.documents.count()
    document_count.short_description = 'Documents'


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'document_type', 'category', 'version', 'status', 'access_level', 'download_count', 'created_at')
    list_filter = ('document_type', 'status', 'access_level', 'category', 'created_at')
    search_fields = ('title', 'description', 'tags', 'keywords')
    filter_horizontal = ()
    raw_id_fields = ('owner', 'created_by', 'approved_by', 'program', 'project', 'event', 'previous_version')
    date_hierarchy = 'created_at'
    inlines = [DocumentAccessLogInline, DocumentReviewInline]
    
    fieldsets = (
        ('Document Information', {
            'fields': ('title', 'document_type', 'category', 'description')
        }),
        ('File Details', {
            'fields': ('file', 'version', 'tags', 'keywords')
        }),
        ('Access & Status', {
            'fields': ('status', 'access_level', 'is_active')
        }),
        ('Associations', {
            'fields': ('program', 'project', 'event')
        }),
        ('Ownership', {
            'fields': ('owner', 'created_by', 'approved_by', 'approval_date')
        }),
        ('Validity Period', {
            'fields': ('effective_date', 'expiry_date')
        }),
        ('Version Control', {
            'fields': ('previous_version', 'change_log')
        }),
        ('Tracking', {
            'fields': ('download_count', 'view_count', 'last_downloaded', 'last_viewed')
        }),
        ('System', {
            'fields': ('file_size', 'file_format', 'created_at', 'updated_at')
        }),
    )
    
    readonly_fields = ('file_size', 'file_format', 'created_at', 'updated_at', 'download_count', 'view_count', 'last_downloaded', 'last_viewed')


@admin.register(DocumentAccessLog)
class DocumentAccessLogAdmin(admin.ModelAdmin):
    list_display = ('document', 'user', 'access_type', 'accessed_at', 'ip_address')
    list_filter = ('access_type', 'accessed_at')
    search_fields = ('document__title', 'user__first_name', 'user__last_name', 'ip_address')
    raw_id_fields = ('document', 'user')
    date_hierarchy = 'accessed_at'
    
    fieldsets = (
        ('Access Details', {
            'fields': ('document', 'user', 'access_type')
        }),
        ('Technical Details', {
            'fields': ('ip_address', 'user_agent', 'accessed_at')
        }),
    )
    
    readonly_fields = ('accessed_at',)


@admin.register(DocumentReview)
class DocumentReviewAdmin(admin.ModelAdmin):
    list_display = ('document', 'reviewer', 'status', 'review_date')
    list_filter = ('status', 'review_date')
    search_fields = ('document__title', 'reviewer__first_name', 'reviewer__last_name', 'comments')
    raw_id_fields = ('document', 'reviewer')
    date_hierarchy = 'review_date'
    
    fieldsets = (
        ('Review Details', {
            'fields': ('document', 'reviewer', 'status')
        }),
        ('Review Content', {
            'fields': ('comments', 'changes_required')
        }),
        ('Timestamps', {
            'fields': ('review_date',)
        }),
    )
    
    readonly_fields = ('review_date',)


@admin.register(DocumentTemplate)
class DocumentTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'template_type', 'version', 'is_active', 'usage_count', 'last_used')
    list_filter = ('template_type', 'is_active')
    search_fields = ('name', 'description')
    
    fieldsets = (
        ('Template Information', {
            'fields': ('name', 'template_type', 'description', 'version', 'is_active')
        }),
        ('Files', {
            'fields': ('template_file', 'preview_image')
        }),
        ('Usage Tracking', {
            'fields': ('usage_count', 'last_used')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'usage_count', 'last_used')