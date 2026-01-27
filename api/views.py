from rest_framework import generics, permissions, status
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, extend_schema_view

from api.choices import ReportStatusEnum

from .models import Report, ReportStatus, Vote, Comment, UserRole
from rest_framework import viewsets

from .permissions import IsOwnerOrReadOnly, IsModerator
from .serializers import CommentSerializer, ReportDetailSerializer, ReportSerializer, SignUpSerializer, SignInSerializer, MeSerializer, VoteSerializer, ChangeStatusSerializer, ReportStatusSerializer

class SignUpView(generics.CreateAPIView):
    serializer_class = SignUpSerializer
    permission_classes = (permissions.AllowAny,)

@extend_schema(
    auth = [{"bearerAuth": []}]
)
class SignInView(generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = SignInSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        password = serializer.validated_data.get("password")
        email = serializer.validated_data.get("email")
        user = authenticate(password=password, email=email)
        if user is None:
            return Response({"error": "Invalid credentials"}, status=400)
        
        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh)
        })

class MeView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MeSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user

@extend_schema_view(
    list=extend_schema(auth=[{"bearerAuth": []}]),
    retrieve=extend_schema(auth=[{"bearerAuth": []}]),
)
class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.all()
    parser_classes = (MultiPartParser, FormParser)

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ReportDetailSerializer
        return ReportSerializer
    
    def get_queryset(self):
        queryset = Report.objects.all().order_by('-created_at').prefetch_related('votes', 'author', 'statuses')
        if self.action == 'retrieve':
            queryset = queryset.prefetch_related('comments')
        return queryset

    def get_permissions(self):
        if self.action == 'change_status':
            return [IsModerator()]

        if self.action == 'me':
            return [permissions.IsAuthenticated()]
        
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.AllowAny()]
        
        return [permissions.IsAuthenticated(), IsOwnerOrReadOnly()]

    def perform_create(self, serializer):
        report = serializer.save(author=self.request.user)
        ReportStatus.objects.create(report=report, status_name=ReportStatusEnum.NEW.value, modified_by=self.request.user)

    @action(detail=False, methods=['get'])
    def me(self, request):
        reports = Report.objects.filter(author=request.user).order_by("-created_at")
        serializer = self.get_serializer(reports, many=True)
        return Response(serializer.data)

    @extend_schema(request=ChangeStatusSerializer, responses=ReportSerializer)
    @action(detail=True, methods=['post'], permission_classes=[IsModerator])
    def change_status(self, request, pk=None):
        report = self.get_object()
        serializer = ChangeStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data['status']
        latest_status = report.statuses.order_by('-created_at').first()
        if latest_status and latest_status.status_name == new_status:
            return Response(
                {"detail": "Report already has this status."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        ReportStatus.objects.create(
            report=report,
            status_name=serializer.validated_data['status'],
            moderator_comment=serializer.validated_data.get('comment', ""),
            modified_by=request.user
        )
        
        if 'assigned_unit' in serializer.validated_data:
            report.assigned_unit = serializer.validated_data['assigned_unit']
            report.save()
        
        # Clear prefetch cache to ensure the new status is returned in the response
        if hasattr(report, '_prefetched_objects_cache'):
            report._prefetched_objects_cache = {}

        return Response(ReportSerializer(report).data)
    
    @extend_schema(responses=ReportStatusSerializer(many=True))
    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        report = self.get_object()
        # Statuses are already ordered by -created_at in model Meta
        serializer = ReportStatusSerializer(report.statuses.all(), many=True)
        return Response(serializer.data)

class VoteViewSet(viewsets.ModelViewSet):
    queryset = Vote.objects.all()
    serializer_class = VoteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        report_id = self.kwargs.get('pk')
        return get_object_or_404(
            Vote,
            report_id=report_id,
            created_by=self.request.user
        )

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        is_official = False
        # Check if user is moderator and if they sent the flag
        if self.request.user.role == UserRole.MODERATOR:
            is_official = self.request.data.get('is_official_response', False)
            if isinstance(is_official, str):
                is_official = is_official.lower() == 'true'

        serializer.save(
            created_by=self.request.user,
            is_official_response=is_official
        )
