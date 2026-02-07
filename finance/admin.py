from django.contrib import admin
from .models import Income, Expense, Grant, Budget


@admin.register(Income)
class IncomeAdmin(admin.ModelAdmin):
    list_display = ('description', 'income_type', 'amount', 'date_received', 'received_from', 'approved_by', 'program')
    list_filter = ('income_type', 'date_received', 'payment_method', 'approved_by')
    search_fields = ('description', 'received_from', 'reference_number', 'receipt_number')
    date_hierarchy = 'date_received'
    raw_id_fields = ('program', 'project', 'received_by', 'approved_by')
    
    fieldsets = (
        ('Income Details', {
            'fields': ('description', 'income_type', 'amount', 'date_received')
        }),
        ('Source', {
            'fields': ('received_from', 'received_by', 'payment_method', 'reference_number')
        }),
        ('Association', {
            'fields': ('program', 'project')
        }),
        ('Documentation', {
            'fields': ('receipt_number', 'supporting_document')
        }),
        ('Approval', {
            'fields': ('approved_by', 'approval_date')
        }),
        ('Notes', {
            'fields': ('notes', 'created_at', 'updated_at')
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def save_model(self, request, obj, form, change):
        if not obj.approved_by and request.user.user_type == 'executive':
            obj.approved_by = request.user
            obj.approval_date = timezone.now().date()
        super().save_model(request, obj, form, change)


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('description', 'expense_type', 'amount', 'date_incurred', 'paid_to', 'approved_by', 'requires_chairperson_approval')
    list_filter = ('expense_type', 'date_incurred', 'payment_method', 'requires_chairperson_approval')
    search_fields = ('description', 'paid_to', 'invoice_number')
    date_hierarchy = 'date_incurred'
    raw_id_fields = ('program', 'project', 'paid_by', 'approved_by')
    
    fieldsets = (
        ('Expense Details', {
            'fields': ('description', 'expense_type', 'amount', 'date_incurred')
        }),
        ('Payment Details', {
            'fields': ('paid_to', 'paid_by', 'payment_method')
        }),
        ('Association', {
            'fields': ('program', 'project')
        }),
        ('Documentation', {
            'fields': ('invoice_number', 'receipt', 'invoice')
        }),
        ('Approval', {
            'fields': ('approved_by', 'approval_date', 'requires_chairperson_approval')
        }),
        ('Notes', {
            'fields': ('notes', 'created_at', 'updated_at')
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Grant)
class GrantAdmin(admin.ModelAdmin):
    list_display = ('grant_name', 'donor', 'amount', 'status', 'start_date', 'end_date', 'focal_person')
    list_filter = ('status', 'donor', 'start_date')
    search_fields = ('grant_name', 'donor', 'purpose')
    date_hierarchy = 'application_date'
    raw_id_fields = ('program', 'project', 'focal_person')
    
    fieldsets = (
        ('Grant Information', {
            'fields': ('grant_name', 'donor', 'amount', 'currency')
        }),
        ('Timeline', {
            'fields': ('application_date', 'approval_date', 'start_date', 'end_date')
        }),
        ('Purpose', {
            'fields': ('purpose', 'program', 'project')
        }),
        ('Management', {
            'fields': ('focal_person', 'status')
        }),
        ('Financial Tracking', {
            'fields': ('amount_received', 'amount_spent', 'balance')
        }),
        ('Reporting', {
            'fields': ('reporting_requirements', 'next_report_date')
        }),
        ('Documents', {
            'fields': ('proposal', 'agreement', 'reports')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('name', 'budget_type', 'total_amount', 'amount_spent', 'balance', 'status', 'start_date', 'end_date')
    list_filter = ('budget_type', 'status', 'period')
    search_fields = ('name', 'notes')
    date_hierarchy = 'start_date'
    raw_id_fields = ('program', 'project', 'prepared_by', 'approved_by')
    
    fieldsets = (
        ('Budget Information', {
            'fields': ('name', 'budget_type', 'period')
        }),
        ('Association', {
            'fields': ('program', 'project')
        }),
        ('Financials', {
            'fields': ('total_amount', 'amount_spent', 'balance')
        }),
        ('Timeline', {
            'fields': ('start_date', 'end_date')
        }),
        ('Status & Approval', {
            'fields': ('status', 'prepared_by', 'approved_by', 'approval_date')
        }),
        ('Notes', {
            'fields': ('notes', 'created_at', 'updated_at')
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')