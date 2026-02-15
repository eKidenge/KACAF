# programs/views.py
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.http import HttpResponse
from django.db.models import Sum, Count, Q
from .models import Program, Project, TreePlanting, Training
from .serializers import (
    ProgramSerializer, ProjectSerializer, 
    TreePlantingSerializer, TrainingSerializer,
    ProgramProgressSerializer
)
from .forms import ProgramForm, TreePlantingForm

# ============================================================
# API VIEWS (REST Framework) - URL: /api/programs/*
# ============================================================

class ProgramViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Program CRUD operations
    URL: /api/programs/programs/
    """
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
        """API endpoint for program statistics"""
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
        """API endpoint for program projects"""
        program = self.get_object()
        projects = program.projects.all()
        serializer = ProjectSerializer(projects, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['patch'])
    def update_progress(self, request, pk=None):
        """API endpoint to update program progress"""
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
    """
    API endpoint for Project CRUD operations
    URL: /api/programs/projects/
    """
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
        """API endpoint for project tree plantings"""
        project = self.get_object()
        tree_plantings = project.tree_plantings.all()
        serializer = TreePlantingSerializer(tree_plantings, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """API endpoint for project statistics"""
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
    """
    API endpoint for TreePlanting CRUD operations
    URL: /api/programs/tree-plantings/
    """
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
        """API endpoint for current user's tree plantings"""
        trees = TreePlanting.objects.filter(farmer=request.user)
        serializer = self.get_serializer(trees, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['patch'])
    def update_survival(self, request, pk=None):
        """API endpoint to update tree survival rate"""
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
    """
    API endpoint for Training CRUD operations
    URL: /api/programs/trainings/
    """
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
        """API endpoint to register for training"""
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
        """API endpoint for upcoming trainings"""
        upcoming = Training.objects.filter(date__gte=timezone.now().date()).order_by('date')
        serializer = self.get_serializer(upcoming, many=True)
        return Response(serializer.data)


# ============================================================
# WEB VIEWS (Template rendering) - URL: /programs/*
# ============================================================

@login_required
def web_program_list(request):
    """
    Web view for listing all programs (HTML template)
    URL: /programs/
    """
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
    
    # Get program statistics by type - FIXED: budget -> estimated_budget
    program_stats = Program.objects.values('program_type').annotate(
        count=Count('id'),
        total_budget=Sum('estimated_budget'),  # Changed from 'budget' to 'estimated_budget'
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
    return render(request, 'programs/program/program_list.html', context)


@login_required
def web_program_dashboard(request):
    """
    Web view for program dashboard (HTML template)
    URL: /programs/dashboard/
    """
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
    total_programs = completed_programs + active_programs
    completion_rate = (completed_programs / total_programs * 100) if total_programs > 0 else 0
    
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
def web_program_create(request):
    """
    Web view for creating a new program (HTML template)
    URL: /programs/create/
    """
    if request.method == "POST":
        form = ProgramForm(request.POST, request.FILES)
        if form.is_valid():
            program = form.save(commit=False)
            program.created_by = request.user
            program.save()
            messages.success(request, "Program created successfully!")
            return redirect('programs:web_program_list')
    else:
        form = ProgramForm()
    
    context = {
        'form': form,
        'current_year': timezone.now().year,
    }
    return render(request, 'programs/program_create.html', context)


@login_required
def web_program_detail(request, pk):
    """
    Web view for viewing a single program (HTML template)
    URL: /programs/<int:pk>/
    """
    program = get_object_or_404(Program, pk=pk)
    
    # Get related projects
    projects = program.projects.all()
    
    # Get related trainings
    trainings = program.trainings.all().order_by('-date')
    
    # Calculate program statistics
    total_projects = projects.count()
    active_projects = projects.filter(status='active').count()
    completed_projects = projects.filter(status='completed').count()
    
    # Calculate budget utilization
    budget_utilization = 0
    if program.estimated_budget and program.estimated_budget > 0:
        budget_utilization = (program.actual_spent / program.estimated_budget * 100) if program.actual_spent else 0
    
    context = {
        'user': request.user,
        'program': program,
        'projects': projects,
        'trainings': trainings,
        'total_projects': total_projects,
        'active_projects': active_projects,
        'completed_projects': completed_projects,
        'budget_utilization': round(budget_utilization, 1),
        'current_year': timezone.now().year,
    }
    return render(request, 'programs/program_detail.html', context)


@login_required
def web_program_edit(request, pk):
    """
    Web view for editing a program (HTML template)
    URL: /programs/<int:pk>/edit/
    """
    program = get_object_or_404(Program, pk=pk)
    
    # Check permission - only admin or program manager can edit
    if not (request.user.is_staff or request.user == program.program_manager):
        messages.error(request, "You don't have permission to edit this program.")
        return redirect('programs:web_program_detail', pk=pk)
    
    if request.method == "POST":
        form = ProgramForm(request.POST, request.FILES, instance=program)
        if form.is_valid():
            form.save()
            messages.success(request, "Program updated successfully!")
            return redirect('programs:web_program_detail', pk=pk)
    else:
        form = ProgramForm(instance=program)
    
    context = {
        'form': form,
        'program': program,
        'current_year': timezone.now().year,
    }
    return render(request, 'programs/program_edit.html', context)


# ------------------------------------------------------------
# Member Tree Planting Web Views
# ------------------------------------------------------------

@login_required
def web_my_trees(request):
    """
    Web view for members to see their tree planting history
    URL: /programs/my-trees/
    """
    # Get all tree plantings by the current user
    trees = TreePlanting.objects.filter(farmer=request.user).order_by('-planting_date')
    
    # Calculate statistics
    total_trees = trees.aggregate(total=Sum('quantity'))['total'] or 0
    total_species = trees.values('species').distinct().count()
    
    # Get trees by species
    trees_by_species = trees.values('species').annotate(
        total=Sum('quantity'),
    ).order_by('-total')
    
    # Add average survival rate to each species
    for species in trees_by_species:
        species_trees = trees.filter(species=species['species'])
        avg_survival = species_trees.aggregate(avg=Sum('survival_rate') / Count('id'))['avg'] or 0
        species['avg_survival'] = round(avg_survival, 1)
    
    # Get monthly planting data for charts
    current_year = timezone.now().year
    monthly_data = []
    for month in range(1, 13):
        month_total = trees.filter(
            planting_date__year=current_year,
            planting_date__month=month
        ).aggregate(total=Sum('quantity'))['total'] or 0
        monthly_data.append({
            'month': month,
            'total': month_total
        })
    
    # Get projects the user has participated in
    projects = Project.objects.filter(
        tree_plantings__farmer=request.user
    ).distinct()
    
    context = {
        'user': request.user,
        'trees': trees,
        'total_trees': total_trees,
        'total_species': total_species,
        'trees_by_species': trees_by_species,
        'monthly_data': monthly_data,
        'projects': projects,
        'current_year': current_year,
    }
    return render(request, 'programs/my_trees.html', context)


@login_required
def web_tree_detail(request, pk):
    """
    Web view for viewing details of a specific tree planting record
    URL: /programs/trees/<int:pk>/
    """
    tree = get_object_or_404(TreePlanting, pk=pk, farmer=request.user)
    
    context = {
        'user': request.user,
        'tree': tree,
    }
    return render(request, 'programs/tree_detail.html', context)


@login_required
def web_add_tree_planting(request):
    """
    Web view for adding a new tree planting record
    URL: /programs/trees/add/
    """
    if request.method == "POST":
        form = TreePlantingForm(request.POST, request.FILES)
        if form.is_valid():
            tree_planting = form.save(commit=False)
            tree_planting.farmer = request.user
            tree_planting.save()
            messages.success(request, "Tree planting record added successfully!")
            return redirect('programs:web_my_trees')
    else:
        form = TreePlantingForm()
    
    # Get projects available for the user to plant trees in
    available_projects = Project.objects.filter(status='active')
    
    context = {
        'form': form,
        'available_projects': available_projects,
        'current_year': timezone.now().year,
    }
    return render(request, 'programs/add_tree_planting.html', context)


@login_required
def web_update_tree_survival(request, pk):
    """
    Web view for updating survival rate of a tree planting
    URL: /programs/trees/<int:pk>/update-survival/
    """
    tree = get_object_or_404(TreePlanting, pk=pk, farmer=request.user)
    
    if request.method == "POST":
        survival_rate = request.POST.get('survival_rate')
        monitoring_notes = request.POST.get('monitoring_notes', '')
        
        if survival_rate:
            tree.survival_rate = survival_rate
            tree.monitoring_notes = monitoring_notes
            tree.last_monitoring_date = timezone.now().date()
            tree.save()
            messages.success(request, "Tree survival rate updated successfully!")
            return redirect('programs:web_tree_detail', pk=pk)
    
    context = {
        'user': request.user,
        'tree': tree,
    }
    return render(request, 'programs/update_tree_survival.html', context)


# ============================================================
# Alias for backward compatibility (optional)
# ============================================================
# If you have existing code that references the old function names,
# uncomment these lines:
# program_list = web_program_list
# program_dashboard = web_program_dashboard
# program_create = web_program_create
# program_detail = web_program_detail
# program_edit = web_program_edit
# my_trees = web_my_trees
# tree_detail = web_tree_detail
# add_tree_planting = web_add_tree_planting
# update_tree_survival = web_update_tree_survival

@login_required
def program_report(request, pk):
    """
    Web view to generate/download a program report.
    URL: /programs/<int:pk>/report/
    """
    program = get_object_or_404(Program, pk=pk)

    # Example: simple text report (can be replaced with PDF/Excel)
    report_content = f"""
    Program Report: {program.name}
    Type: {program.program_type}
    Status: {program.status}
    Estimated Budget: {program.estimated_budget}
    Actual Spent: {program.actual_spent}
    Beneficiaries Target: {program.beneficiaries_target}
    Beneficiaries Reached: {program.beneficiaries_reached}
    Total Projects: {program.projects.count()}
    Total Trainings: {program.trainings.count()}
    """

    response = HttpResponse(report_content, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename=program_{program.id}_report.txt'
    return response

@login_required
def web_program_join(request, pk):
    """
    Web view for a user to join a program
    URL: /programs/<int:pk>/join/
    """
    program = get_object_or_404(Program, pk=pk)

    # Add user to team_members if not already added
    if request.user not in program.team_members.all():
        program.team_members.add(request.user)
        messages.success(request, f"You have successfully joined the program '{program.name}'!")
    else:
        messages.info(request, f"You are already a member of '{program.name}'.")

    # Redirect back to the program detail page
    return redirect('programs:web_program_detail', pk=pk)


# Here’s a ready-to-use public dashboard view in programs/views.py that matches your template:
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Sum, Count
from programs.models import Program, Project, TreePlanting
from events.models import Event
from testimonials.models import Testimonial
from partners.models import Partner
from django.contrib.auth import get_user_model

User = get_user_model()

def public_dashboard(request):
    """Public dashboard for KACAF, visible without login."""

    # Featured programs (e.g., latest 3 active)
    #featured_programs = Program.objects.filter(status='active').order_by('-created_at')[:3]
    featured_programs = Program.objects.filter(status__iexact='active').order_by('-created_at')[:3]


    # Total counts for impact counters
    total_trees_planted = TreePlanting.objects.aggregate(total=Sum('quantity'))['total'] or 0
    total_members = User.objects.count()
    total_area_coverage = Project.objects.aggregate(total=Sum('area_coverage'))['total'] or 0
    #carbon_sequestered = TreePlanting.objects.aggregate(total=Sum('carbon_sequestered'))['total'] or 0
    carbon_sequestered = Project.objects.aggregate(total=Sum('carbon_sequestration'))['total'] or 0
    total_beneficiaries = Program.objects.aggregate(total=Sum('beneficiaries_reached'))['total'] or 0

    # Upcoming events (next 3)
    upcoming_events = Event.objects.filter(start_datetime__gte=timezone.now()).order_by('start_datetime')[:3]

    # Testimonials (latest 3)
    testimonials = Testimonial.objects.order_by('-created_at')[:3]

    # Partners
    partners = Partner.objects.all()

    context = {
        'featured_programs': featured_programs,
        'total_trees_planted': total_trees_planted,
        'total_members': total_members,
        'total_area_coverage': total_area_coverage,
        'carbon_sequestered': carbon_sequestered,
        'total_beneficiaries': total_beneficiaries,
        'upcoming_events': upcoming_events,
        'testimonials': testimonials,
        'partners': partners,
    }

    return render(request, 'dashboard/public_dashboard.html', context)


