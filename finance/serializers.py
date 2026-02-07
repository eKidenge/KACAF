from rest_framework import serializers
from .models import Income, Expense, Grant, Budget
from accounts.serializers import UserSerializer


class IncomeSerializer(serializers.ModelSerializer):
    received_by = UserSerializer(read_only=True)
    approved_by = UserSerializer(read_only=True)
    
    class Meta:
        model = Income
        fields = '__all__'
        read_only_fields = ['received_by', 'approved_by', 'approval_date']


class ExpenseSerializer(serializers.ModelSerializer):
    paid_by = UserSerializer(read_only=True)
    approved_by = UserSerializer(read_only=True)
    
    class Meta:
        model = Expense
        fields = '__all__'
        read_only_fields = ['paid_by', 'approved_by', 'approval_date']


class GrantSerializer(serializers.ModelSerializer):
    focal_person = UserSerializer(read_only=True)
    
    class Meta:
        model = Grant
        fields = '__all__'


class BudgetSerializer(serializers.ModelSerializer):
    prepared_by = UserSerializer(read_only=True)
    approved_by = UserSerializer(read_only=True)
    
    class Meta:
        model = Budget
        fields = '__all__'
        read_only_fields = ['prepared_by', 'approved_by', 'approval_date']


class FinancialReportSerializer(serializers.Serializer):
    start_date = serializers.DateField()
    end_date = serializers.DateField()


class BudgetApprovalSerializer(serializers.Serializer):
    comments = serializers.CharField(required=False, allow_blank=True)