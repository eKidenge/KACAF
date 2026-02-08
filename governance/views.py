from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .models import GeneralAssembly, Resolution, MembershipApplication, DisciplinaryAction
from .serializers import (
    GeneralAssemblySerializer, ResolutionSerializer,
    MembershipApplicationSerializer, DisciplinaryActionSerializer,
    VoteSerializer, ResolutionDecisionSerializer
)
from .permissions import IsChairperson, IsExecutiveMember, IsSubjectOfDisciplinaryAction


User = get_user_model()


class GeneralAssemblyViewSet(viewsets.ModelViewSet):
    queryset = GeneralAssembly.objects.all()
    serializer_class = GeneralAssemblySerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsChairperson]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    @action(detail=True, methods=['post'])
    def register_attendance(self, request, pk=None):
        assembly = self.get_object()
        user = request.user
        
        if user not in assembly.members_present.all():
            assembly.members_present.add(user)
            assembly.total_attendance = assembly.members_present.count()
            assembly.save()
            return Response({'message': 'Attendance registered successfully.'}, status=status.HTTP_200_OK)
        return Response({'message': 'Already registered.'}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        upcoming = GeneralAssembly.objects.filter(status='scheduled').order_by('date')
        serializer = self.get_serializer(upcoming, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def past(self, request):
        past = GeneralAssembly.objects.filter(status='completed').order_by('-date')
        serializer = self.get_serializer(past, many=True)
        return Response(serializer.data)


class ResolutionViewSet(viewsets.ModelViewSet):
    queryset = Resolution.objects.all()
    serializer_class = ResolutionSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsExecutiveMember]
        elif self.action in ['vote', 'propose']:
            permission_classes = [permissions.IsAuthenticated]
        elif self.action == 'make_decision':
            permission_classes = [permissions.IsAuthenticated, IsChairperson]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        serializer.save(proposed_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def vote(self, request, pk=None):
        resolution = self.get_object()
        serializer = VoteSerializer(data=request.data)
        
        if serializer.is_valid():
            vote_type = serializer.validated_data['vote_type']
            
            if vote_type == 'for':
                resolution.votes_for += 1
            elif vote_type == 'against':
                resolution.votes_against += 1
            elif vote_type == 'abstain':
                resolution.votes_abstain += 1
            
            resolution.save()
            return Response({'message': 'Vote recorded (advisory).'}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsChairperson])
    def make_decision(self, request, pk=None):
        resolution = self.get_object()
        serializer = ResolutionDecisionSerializer(data=request.data)
        
        if serializer.is_valid():
            resolution.chairperson_decision = serializer.validated_data['decision']
            resolution.chairperson_comments = serializer.validated_data.get('comments', '')
            resolution.decision_date = timezone.now()
            
            if serializer.validated_data['decision'] == 'approved':
                resolution.status = 'approved'
            elif serializer.validated_data['decision'] == 'rejected':
                resolution.status = 'rejected'
            
            resolution.save()
            return Response({'message': 'Decision recorded.'}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MembershipApplicationViewSet(viewsets.ModelViewSet):
    serializer_class = MembershipApplicationSerializer
    
    def get_permissions(self):
        if self.action in ['create']:
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ['update', 'partial_update', 'destroy', 'review']:
            permission_classes = [permissions.IsAuthenticated, IsExecutiveMember]
        elif self.action == 'make_decision':
            permission_classes = [permissions.IsAuthenticated, IsChairperson]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.user_type == 'executive':
            return MembershipApplication.objects.all()
        return MembershipApplication.objects.filter(applicant=user)
    
    def perform_create(self, serializer):
        serializer.save(applicant=self.request.user)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsExecutiveMember])
    def review(self, request, pk=None):
        application = self.get_object()
        application.reviewed_by = request.user
        application.review_date = timezone.now()
        application.review_notes = request.data.get('review_notes', '')
        application.save()
        
        return Response({'message': 'Review submitted.'}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsChairperson])
    def make_decision(self, request, pk=None):
        application = self.get_object()
        decision = request.data.get('decision')
        comments = request.data.get('comments', '')
        
        if decision in ['approved', 'rejected']:
            application.chairperson_decision = decision
            application.chairperson_comments = comments
            application.decision_date = timezone.now()
            application.status = decision
            
            if decision == 'approved':
                # Update user's membership
                applicant = application.applicant
                applicant.membership_type = application.applied_membership_type
                applicant.is_verified = True
                applicant.verification_date = timezone.now()
                applicant.save()
            
            application.save()
            return Response({'message': f'Application {decision}.'}, status=status.HTTP_200_OK)
        
        return Response({'error': 'Invalid decision.'}, status=status.HTTP_400_BAD_REQUEST)


class DisciplinaryActionViewSet(viewsets.ModelViewSet):
    serializer_class = DisciplinaryActionSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsChairperson]
        elif self.action in ['appeal', 'my_actions']:
            permission_classes = [permissions.IsAuthenticated, IsSubjectOfDisciplinaryAction]
        else:
            permission_classes = [permissions.IsAuthenticated, IsExecutiveMember]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.user_type == 'executive':
            return DisciplinaryAction.objects.all()
        return DisciplinaryAction.objects.filter(member=user)
    
    def perform_create(self, serializer):
        serializer.save(issued_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def appeal(self, request, pk=None):
        action = self.get_object()
        
        if action.member != request.user:
            return Response({'error': 'Not authorized.'}, status=status.HTTP_403_FORBIDDEN)
        
        action.appeal_filed = True
        action.appeal_date = timezone.now()
        action.appeal_details = request.data.get('appeal_details', '')
        action.status = 'appealed'
        action.save()
        
        return Response({'message': 'Appeal filed.'}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def my_actions(self, request):
        actions = DisciplinaryAction.objects.filter(member=request.user)
        serializer = self.get_serializer(actions, many=True)
        return Response(serializer.data)


# ------------------------------------------------------------
# Web Interface Views (for template rendering)
# ------------------------------------------------------------

@login_required
def membership_application_create(request):
    """Web form for creating a membership application"""
    # You can add context data here if needed
    context = {
        'user': request.user,
        'action': 'create',
    }
    # Use the existing template
    return render(request, 'governance/membership/application_form.html', context)


@login_required
def membership_dashboard(request):
    """Membership dashboard"""
    # Get user's membership applications
    user_applications = MembershipApplication.objects.filter(applicant=request.user)
    
    context = {
        'user': request.user,
        'applications': user_applications,
        'total_applications': user_applications.count(),
        'pending_applications': user_applications.filter(status='pending').count(),
        'approved_applications': user_applications.filter(status='approved').count(),
    }
    # Use the existing template
    return render(request, 'governance/membership/application_list.html', context)


def assembly_create(request):
    """
    Render the 'Create Assembly' page.
    """
    return render(request, 'governance/assembly/assembly_create.html')

