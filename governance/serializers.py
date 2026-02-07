from rest_framework import serializers
from .models import GeneralAssembly, Resolution, MembershipApplication, DisciplinaryAction
from accounts.serializers import UserSerializer


class GeneralAssemblySerializer(serializers.ModelSerializer):
    chairperson = UserSerializer(read_only=True)
    secretary = UserSerializer(read_only=True)
    
    class Meta:
        model = GeneralAssembly
        fields = '__all__'


class ResolutionSerializer(serializers.ModelSerializer):
    proposed_by = UserSerializer(read_only=True)
    seconded_by = UserSerializer(read_only=True)
    
    class Meta:
        model = Resolution
        fields = '__all__'
        read_only_fields = ['votes_for', 'votes_against', 'votes_abstain', 
                           'chairperson_decision', 'chairperson_comments', 'decision_date']


class MembershipApplicationSerializer(serializers.ModelSerializer):
    applicant = UserSerializer(read_only=True)
    
    class Meta:
        model = MembershipApplication
        fields = '__all__'
        read_only_fields = ['applicant', 'reviewed_by', 'review_date', 'review_notes',
                           'chairperson_decision', 'chairperson_comments', 'decision_date', 'status']


class DisciplinaryActionSerializer(serializers.ModelSerializer):
    member = UserSerializer(read_only=True)
    issued_by = UserSerializer(read_only=True)
    
    class Meta:
        model = DisciplinaryAction
        fields = '__all__'
        read_only_fields = ['issued_by', 'issued_date', 'appeal_filed', 'appeal_date',
                           'review_committee_notes', 'final_decision']


class VoteSerializer(serializers.Serializer):
    vote_type = serializers.ChoiceField(choices=['for', 'against', 'abstain'])


class ResolutionDecisionSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=['approved', 'rejected', 'pending', 'referred'])
    comments = serializers.CharField(required=False, allow_blank=True)