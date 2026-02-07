from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone


User = get_user_model()


class Income(models.Model):
    INCOME_TYPE = (
        ('membership_fee', 'Membership Fee'),
        ('donation', 'Donation'),
        ('grant', 'Grant'),
        ('fundraising', 'Fundraising'),
        ('project_income', 'Project Income'),
        ('other', 'Other'),
    )
    
    PAYMENT_METHOD = (
        ('cash', 'Cash'),
        ('mpesa', 'M-Pesa'),
        ('bank_transfer', 'Bank Transfer'),
        ('cheque', 'Cheque'),
        ('mobile_banking', 'Mobile Banking'),
    )
    
    description = models.CharField(max_length=200)
    income_type = models.CharField(max_length=30, choices=INCOME_TYPE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date_received = models.DateField()
    
    # Source details
    received_from = models.CharField(max_length=200)
    received_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='received_incomes')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD)
    reference_number = models.CharField(max_length=100, null=True, blank=True)
    
    # Project/program association
    program = models.ForeignKey('programs.Program', on_delete=models.SET_NULL, null=True, blank=True, related_name='incomes')
    project = models.ForeignKey('programs.Project', on_delete=models.SET_NULL, null=True, blank=True, related_name='incomes')
    
    # Documentation
    receipt_number = models.CharField(max_length=100, null=True, blank=True)
    supporting_document = models.FileField(upload_to='finance/income/', null=True, blank=True)
    
    # Approval
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_incomes')
    approval_date = models.DateField(null=True, blank=True)
    
    notes = models.TextField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date_received']
    
    def __str__(self):
        return f"{self.description} - KES {self.amount}"


class Expense(models.Model):
    EXPENSE_TYPE = (
        ('program', 'Program Expense'),
        ('administrative', 'Administrative'),
        ('staff', 'Staff Costs'),
        ('transport', 'Transport & Travel'),
        ('equipment', 'Equipment & Supplies'),
        ('training', 'Training & Workshop'),
        ('monitoring', 'Monitoring & Evaluation'),
        ('other', 'Other'),
    )
    
    PAYMENT_METHOD = (
        ('cash', 'Cash'),
        ('mpesa', 'M-Pesa'),
        ('bank_transfer', 'Bank Transfer'),
        ('cheque', 'Cheque'),
    )
    
    description = models.CharField(max_length=200)
    expense_type = models.CharField(max_length=30, choices=EXPENSE_TYPE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date_incurred = models.DateField()
    
    # Payment details
    paid_to = models.CharField(max_length=200)
    paid_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='made_expenses')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD)
    
    # Project/program association
    program = models.ForeignKey('programs.Program', on_delete=models.SET_NULL, null=True, blank=True, related_name='expenses')
    project = models.ForeignKey('programs.Project', on_delete=models.SET_NULL, null=True, blank=True, related_name='expenses')
    
    # Documentation
    invoice_number = models.CharField(max_length=100, null=True, blank=True)
    receipt = models.FileField(upload_to='finance/expenses/receipts/', null=True, blank=True)
    invoice = models.FileField(upload_to='finance/expenses/invoices/', null=True, blank=True)
    
    # Approval (Chairperson must approve according to constitution)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_expenses')
    approval_date = models.DateField(null=True, blank=True)
    requires_chairperson_approval = models.BooleanField(default=True)
    
    notes = models.TextField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date_incurred']
    
    def __str__(self):
        return f"{self.description} - KES {self.amount}"


class Grant(models.Model):
    STATUS_CHOICES = (
        ('prospect', 'Prospect'),
        ('application', 'Application Submitted'),
        ('review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('reporting', 'Reporting'),
    )
    
    grant_name = models.CharField(max_length=200)
    donor = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10, default='KES')
    
    # Timeline
    application_date = models.DateField()
    approval_date = models.DateField(null=True, blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Purpose
    purpose = models.TextField()
    program = models.ForeignKey('programs.Program', on_delete=models.SET_NULL, null=True, blank=True, related_name='grants')
    project = models.ForeignKey('programs.Project', on_delete=models.SET_NULL, null=True, blank=True, related_name='grants')
    
    # Management
    focal_person = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='managed_grants')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='prospect')
    
    # Financial tracking
    amount_received = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    amount_spent = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # Reporting
    reporting_requirements = models.TextField(null=True, blank=True)
    next_report_date = models.DateField(null=True, blank=True)
    
    # Documents
    proposal = models.FileField(upload_to='finance/grants/proposals/', null=True, blank=True)
    agreement = models.FileField(upload_to='finance/grants/agreements/', null=True, blank=True)
    reports = models.FileField(upload_to='finance/grants/reports/', null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-application_date']
    
    def __str__(self):
        return f"{self.grant_name} - {self.donor}"


class Budget(models.Model):
    BUDGET_TYPE = (
        ('annual', 'Annual Budget'),
        ('program', 'Program Budget'),
        ('project', 'Project Budget'),
        ('event', 'Event Budget'),
    )
    
    PERIOD_CHOICES = (
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annual', 'Annual'),
        ('project', 'Project Duration'),
    )
    
    name = models.CharField(max_length=200)
    budget_type = models.CharField(max_length=20, choices=BUDGET_TYPE)
    period = models.CharField(max_length=20, choices=PERIOD_CHOICES)
    
    # Association
    program = models.ForeignKey('programs.Program', on_delete=models.CASCADE, null=True, blank=True, related_name='budgets')
    project = models.ForeignKey('programs.Project', on_delete=models.CASCADE, null=True, blank=True, related_name='budgets')
    
    # Financials
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    amount_spent = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # Timeline
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Status
    status = models.CharField(max_length=20, choices=[
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('active', 'Active'),
        ('closed', 'Closed'),
    ], default='draft')
    
    # Approval
    prepared_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='prepared_budgets')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_budgets')
    approval_date = models.DateField(null=True, blank=True)
    
    notes = models.TextField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - KES {self.total_amount}"