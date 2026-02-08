from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Income, Expense, Grant, Budget
from django.contrib import messages
from django.shortcuts import redirect
from .serializers import (
    IncomeSerializer, ExpenseSerializer, 
    GrantSerializer, BudgetSerializer,
    FinancialReportSerializer, BudgetApprovalSerializer
)
from .permissions import IsTreasurer, IsChairperson, IsFinancialManager


class IncomeViewSet(viewsets.ModelViewSet):
    serializer_class = IncomeSerializer
    
    def get_queryset(self):
        # Filter by date range if provided
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        queryset = Income.objects.all()
        
        if start_date:
            queryset = queryset.filter(date_received__gte=start_date)
        if end_date:
            queryset = queryset.filter(date_received__lte=end_date)
        
        return queryset
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsFinancialManager]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        # Get summary by type
        summary = Income.objects.values('income_type').annotate(
            total_amount=Sum('amount'),
            count=Count('id')
        ).order_by('-total_amount')
        
        total = Income.objects.aggregate(total=Sum('amount'))['total'] or 0
        
        return Response({
            'summary': summary,
            'total_income': total
        })
    
    @action(detail=False, methods=['get'])
    def by_period(self, request):
        # Monthly income for the current year
        current_year = timezone.now().year
        monthly = Income.objects.filter(
            date_received__year=current_year
        ).values('date_received__month').annotate(
            total=Sum('amount')
        ).order_by('date_received__month')
        
        return Response(monthly)


class ExpenseViewSet(viewsets.ModelViewSet):
    serializer_class = ExpenseSerializer
    
    def get_queryset(self):
        # Filter by approval status if provided
        requires_approval = self.request.query_params.get('requires_approval')
        queryset = Expense.objects.all()
        
        if requires_approval == 'true':
            queryset = queryset.filter(requires_chairperson_approval=True, approved_by__isnull=True)
        
        return queryset
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'approve']:
            permission_classes = [permissions.IsAuthenticated, IsFinancialManager]
        elif self.action == 'chairperson_approve':
            permission_classes = [permissions.IsAuthenticated, IsChairperson]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        expense = self.get_object()
        
        if expense.approved_by:
            return Response({'error': 'Expense already approved.'}, status=status.HTTP_400_BAD_REQUEST)
        
        expense.approved_by = request.user
        expense.approval_date = timezone.now().date()
        
        if expense.requires_chairperson_approval and request.user.user_type != 'executive':
            return Response({'error': 'Chairperson approval required.'}, status=status.HTTP_403_FORBIDDEN)
        
        expense.save()
        return Response({'message': 'Expense approved.'}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def pending_approval(self, request):
        pending = Expense.objects.filter(
            requires_chairperson_approval=True,
            approved_by__isnull=True
        )
        serializer = self.get_serializer(pending, many=True)
        return Response(serializer.data)


class GrantViewSet(viewsets.ModelViewSet):
    queryset = Grant.objects.all()
    serializer_class = GrantSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsFinancialManager]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        active_grants = Grant.objects.filter(status='active')
        serializer = self.get_serializer(active_grants, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def reporting_due(self, request):
        due_grants = Grant.objects.filter(
            next_report_date__lte=timezone.now().date() + timezone.timedelta(days=30),
            status='active'
        )
        serializer = self.get_serializer(due_grants, many=True)
        return Response(serializer.data)


class BudgetViewSet(viewsets.ModelViewSet):
    serializer_class = BudgetSerializer
    
    def get_queryset(self):
        budget_type = self.request.query_params.get('type')
        status_filter = self.request.query_params.get('status')
        
        queryset = Budget.objects.all()
        
        if budget_type:
            queryset = queryset.filter(budget_type=budget_type)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsFinancialManager]
        elif self.action == 'approve':
            permission_classes = [permissions.IsAuthenticated, IsChairperson]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        budget = self.get_object()
        serializer = BudgetApprovalSerializer(data=request.data)
        
        if serializer.is_valid():
            budget.status = 'approved'
            budget.approved_by = request.user
            budget.approval_date = timezone.now().date()
            budget.notes = serializer.validated_data.get('comments', '')
            budget.save()
            
            return Response({'message': 'Budget approved.'}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def financial_report(self, request):
        serializer = FinancialReportSerializer(data=request.query_params)
        
        if serializer.is_valid():
            start_date = serializer.validated_data['start_date']
            end_date = serializer.validated_data['end_date']
            
            incomes = Income.objects.filter(
                date_received__range=[start_date, end_date]
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            expenses = Expense.objects.filter(
                date_incurred__range=[start_date, end_date]
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            # Get expenses by type
            expenses_by_type = Expense.objects.filter(
                date_incurred__range=[start_date, end_date]
            ).values('expense_type').annotate(total=Sum('amount'))
            
            # Get income by type
            income_by_type = Income.objects.filter(
                date_received__range=[start_date, end_date]
            ).values('income_type').annotate(total=Sum('amount'))
            
            return Response({
                'period': f"{start_date} to {end_date}",
                'total_income': incomes,
                'total_expenses': expenses,
                'net_balance': incomes - expenses,
                'expenses_by_type': expenses_by_type,
                'income_by_type': income_by_type,
                'grant_summary': Grant.objects.filter(status='active').aggregate(
                    total_awarded=Sum('amount'),
                    total_spent=Sum('amount_spent'),
                    total_balance=Sum('balance')
                ),
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ------------------------------------------------------------
# Web Interface Views (for template rendering)
# ------------------------------------------------------------

@login_required
def transaction_list(request):
    """Web view for listing transactions (income and expenses)"""
    # Get recent transactions
    recent_incomes = Income.objects.all().order_by('-date_received')[:10]
    recent_expenses = Expense.objects.all().order_by('-date_incurred')[:10]
    
    # Calculate totals
    total_income = Income.objects.aggregate(total=Sum('amount'))['total'] or 0
    total_expenses = Expense.objects.aggregate(total=Sum('amount'))['total'] or 0
    net_balance = total_income - total_expenses
    
    # Get pending approvals
    pending_expenses = Expense.objects.filter(
        requires_chairperson_approval=True,
        approved_by__isnull=True
    ).count()
    
    context = {
        'user': request.user,
        'recent_incomes': recent_incomes,
        'recent_expenses': recent_expenses,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'net_balance': net_balance,
        'pending_expenses': pending_expenses,
        'current_year': timezone.now().year,
        'current_month': timezone.now().month,
    }
    return render(request, 'finance/transaction_list.html', context)


@login_required
def budget_dashboard(request):
    """Web view for budget dashboard"""
    # Get current year budgets
    current_year = timezone.now().year
    current_budgets = Budget.objects.filter(
        year=current_year,
        status='approved'
    )
    
    # Calculate totals
    total_budget = current_budgets.aggregate(total=Sum('allocated_amount'))['total'] or 0
    total_spent = current_budgets.aggregate(total=Sum('spent_amount'))['total'] or 0
    remaining_budget = total_budget - total_spent
    
    # Get budgets by type
    budgets_by_type = current_budgets.values('budget_type').annotate(
        allocated=Sum('allocated_amount'),
        spent=Sum('spent_amount')
    )
    
    # Get active grants
    active_grants = Grant.objects.filter(status='active')
    total_grant_amount = active_grants.aggregate(total=Sum('amount'))['total'] or 0
    total_grant_spent = active_grants.aggregate(total=Sum('amount_spent'))['total'] or 0
    total_grant_balance = total_grant_amount - total_grant_spent
    
    context = {
        'user': request.user,
        'current_budgets': current_budgets,
        'total_budget': total_budget,
        'total_spent': total_spent,
        'remaining_budget': remaining_budget,
        'budgets_by_type': budgets_by_type,
        'active_grants': active_grants,
        'total_grant_amount': total_grant_amount,
        'total_grant_spent': total_grant_spent,
        'total_grant_balance': total_grant_balance,
        'current_year': current_year,
        'budget_utilization_percentage': (total_spent / total_budget * 100) if total_budget > 0 else 0,
    }
    return render(request, 'finance/budget_dashboard.html', context)

def income_create(request):
    # Replace with your real form handling logic later
    return render(request, 'finance/income/income_create.html')

@login_required
def expense_create(request):
    # Replace with real form handling later
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.created_by = request.user
            expense.save()
            messages.success(request, "Expense recorded successfully.")
            return redirect('finance:transaction_list')
    else:
        form = ExpenseForm()
    
    return render(request, 'finance/expense/expense_create.html', {'form': form})

from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

@login_required
def grant_create(request):
    # TODO: Replace with real form handling logic
    if request.method == 'POST':
        form = GrantForm(request.POST)
        if form.is_valid():
            grant = form.save(commit=False)
            grant.created_by = request.user
            grant.save()
            messages.success(request, "Grant created successfully.")
            return redirect('finance:transaction_list')
    else:
        form = GrantForm()
    
    return render(request, 'finance/grant/grant_create.html', {'form': form})
