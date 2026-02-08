from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Count
from .models import Program, Project, TreePlanting, Training
from .serializers import (
    ProgramSerializer, ProjectSerializer, 
    TreePlantingSerializer, TrainingSerializer,
    ProgramProgressSerializer
)


class ProgramViewSet(viewsets.ModelViewSet):
    queryset = Program.objects.all()
    serializer_class = ProgramSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        stats = {
            'total_programs': Program.objects.count(),
            'active_programs': Program.objects.filter(status='active').count(),
            'total_beneficiaries_target': Program.objects.aggregate(Sum('beneficiaries_target'))['beneficiaries_target__sum'] or 0,
            'total_beneficiaries_reached': Program.objects.aggregate(Sum('beneficiaries_reached'))['beneficiaries_reached__sum'] or 0,
            'programs_by_type': Program.objects.values('program_type').annotate(count=Count('id')),
        }
        return Response(stats)
    
    @action(detail=True, methods=['get'])
    def projects(self, request, pk=None):
        program = self.get_object()
        projects = program.projects.all()
        serializer = ProjectSerializer(projects, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['patch'])
    def update_progress(self, request, pk=None):
        program = self.get_object()
        serializer = ProgramProgressSerializer(data=request.data)
        
        if serializer.is_valid():
            program.progress = serializer.validated_data['progress']
            program.beneficiaries_reached = serializer.validated_data['beneficiaries_reached']
            program.actual_spent = serializer.validated_data['actual_spent']
            program.save()
            
            return Response({'message': 'Progress updated successfully.'}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    
    def get_queryset(self):
        program_id = self.request.query_params.get('program', None)
        if program_id:
            return Project.objects.filter(program_id=program_id)
        return Project.objects.all()
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    @action(detail=True, methods=['get'])
    def tree_plantings(self, request, pk=None):
        project = self.get_object()
        tree_plantings = project.tree_plantings.all()
        serializer = TreePlantingSerializer(tree_plantings, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        project = self.get_object()
        stats = {
            'trees_planted': project.tree_plantings.aggregate(Sum('quantity'))['quantity__sum'] or 0,
            'unique_farmers': project.tree_plantings.values('farmer').distinct().count(),
            'species_count': project.tree_plantings.values('species').distinct().count(),
            'total_area': project.area_coverage,
            'carbon_sequestration': project.carbon_sequestration,
        }
        return Response(stats)


class TreePlantingViewSet(viewsets.ModelViewSet):
    serializer_class = TreePlantingSerializer
    
    def get_queryset(self):
        user = self.request.user
        project_id = self.request.query_params.get('project', None)
        
        if project_id:
            return TreePlanting.objects.filter(project_id=project_id)
        elif not user.is_staff:
            return TreePlanting.objects.filter(farmer=user)
        return TreePlanting.objects.all()
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        serializer.save(farmer=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_trees(self, request):
        trees = TreePlanting.objects.filter(farmer=request.user)
        serializer = self.get_serializer(trees, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['patch'])
    def update_survival(self, request, pk=None):
        tree_planting = self.get_object()
        survival_rate = request.data.get('survival_rate')
        notes = request.data.get('monitoring_notes', '')
        
        if survival_rate is not None:
            tree_planting.survival_rate = survival_rate
            tree_planting.monitoring_notes = notes
            tree_planting.last_monitoring_date = timezone.now().date()
            tree_planting.save()
            return Response({'message': 'Survival rate updated.'}, status=status.HTTP_200_OK)
        
        return Response({'error': 'Survival rate required.'}, status=status.HTTP_400_BAD_REQUEST)


class TrainingViewSet(viewsets.ModelViewSet):
    queryset = Training.objects.all()
    serializer_class = TrainingSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    @action(detail=True, methods=['post'])
    def register(self, request, pk=None):
        training = self.get_object()
        user = request.user
        
        if training.participants.count() >= training.max_participants:
            return Response({'error': 'Training is full.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if user not in training.participants.all():
            training.participants.add(user)
            return Response({'message': 'Registered successfully.'}, status=status.HTTP_200_OK)
        
        return Response({'message': 'Already registered.'}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        upcoming = Training.objects.filter(date__gte=timezone.now().date()).order_by('date')
        serializer = self.get_serializer(upcoming, many=True)
        return Response(serializer.data)


# ------------------------------------------------------------
# Web Interface Views (for template rendering)
# ------------------------------------------------------------

@login_required
def program_list(request):
    """Web view for listing all programs"""
    # Get all programs, filter by status if specified
    status_filter = request.GET.get('status', 'active')
    
    if status_filter == 'active':
        programs = Program.objects.filter(status='active')
    elif status_filter == 'completed':
        programs = Program.objects.filter(status='completed')
    else:
        programs = Program.objects.all()
    
    # Calculate overall statistics
    total_programs = Program.objects.count()
    active_programs = Program.objects.filter(status='active').count()
    total_beneficiaries_reached = Program.objects.aggregate(total=Sum('beneficiaries_reached'))['total'] or 0
    
    # Get program statistics by type
    program_stats = Program.objects.values('program_type').annotate(
        count=Count('id'),
        total_budget=Sum('budget'),
        total_reached=Sum('beneficiaries_reached')
    )
    
    context = {
        'user': request.user,
        'programs': programs.order_by('-created_at'),
        'total_programs': total_programs,
        'active_programs': active_programs,
        'total_beneficiaries_reached': total_beneficiaries_reached,
        'program_stats': program_stats,
        'status_filter': status_filter,
        'current_year': timezone.now().year,
    }
    return render(request, 'programs/program_list.html', context)


@login_required
def program_dashboard(request):
    """Web view for program dashboard with overview and statistics"""
    # Get recent programs
    recent_programs = Program.objects.all().order_by('-created_at')[:5]
    
    # Get active projects
    active_projects = Project.objects.filter(status='active').order_by('-start_date')[:5]
    
    # Get upcoming trainings
    upcoming_trainings = Training.objects.filter(
        date__gte=timezone.now().date()
    ).order_by('date')[:5]
    
    # Calculate key metrics
    total_trees_planted = TreePlanting.objects.aggregate(total=Sum('quantity'))['total'] or 0
    total_training_participants = Training.objects.aggregate(total=Count('participants'))['total'] or 0
    total_area_coverage = Project.objects.aggregate(total=Sum('area_coverage'))['total'] or 0
    
    # Get program completion rates
    completed_programs = Program.objects.filter(status='completed').count()
    active_programs = Program.objects.filter(status='active').count()
    completion_rate = (completed_programs / (completed_programs + active_programs) * 100) if (completed_programs + active_programs) > 0 else 0
    
    context = {
        'user': request.user,
        'recent_programs': recent_programs,
        'active_projects': active_projects,
        'upcoming_trainings': upcoming_trainings,
        'total_trees_planted': total_trees_planted,
        'total_training_participants': total_training_participants,
        'total_area_coverage': total_area_coverage,
        'completion_rate': round(completion_rate, 1),
        'active_programs_count': active_programs,
        'completed_programs_count': completed_programs,
        'current_year': timezone.now().year,
        'current_month': timezone.now().month,
    }
    return render(request, 'programs/program_dashboard.html', context)

@login_required
def program_create(request):
    """Web view for creating a new program"""
    from .forms import ProgramForm  # make sure you have a form

    if request.method == "POST":
        form = ProgramForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('programs:program_list')
    else:
        form = ProgramForm()
    
    context = {'form': form}
    return render(request, 'programs/program_create.html', context)
