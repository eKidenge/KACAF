from django.shortcuts import get_object_or_404
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