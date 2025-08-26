from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from report.models import ReportCategory, Report
from profiles.models import UserProfile
from posts.models import Post

from report.serializers import (
    ReportCategorySerializer, 
    CreateReportSerializer,
    ReportDetailSerializer,
    AdminReportSerializer
)

# list all active report categories
class ReportCategoryListView(generics.ListAPIView):
    queryset = ReportCategory.objects.filter(is_active=True)
    serializer_class = ReportCategorySerializer
    permission_classes = [permissions.AllowAny]

# create a new report
class CreateReportView(generics.CreateAPIView):
    serializer_class = CreateReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        # Check if user already reported this item
        item_type = request.data.get('reported_item_type', '').lower()
        item_id = request.data.get('reported_item_id')
        
        if item_type == 'post':
            content_type = ContentType.objects.get_for_model(Post)
        elif item_type == 'profile':
            content_type = ContentType.objects.get_for_model(UserProfile)
        else:
            return Response(
                {'error': 'Invalid item type'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        existing_report = Report.objects.filter(
            reporter=request.user,
            content_type=content_type,
            object_id=item_id
        ).first()
        
        if existing_report:
            return Response(
                {
                    'error': 'You have already reported this item',
                    'existing_report_id': existing_report.report_id
                },
                status=status.HTTP_409_CONFLICT
            )
        
        return super().create(request, *args, **kwargs)

# # list reports made by current authenticated user
# class UserReportsListView(generics.ListAPIView):
#     serializer_class = ReportDetailSerializer
#     permission_classes = [permissions.IsAuthenticated]
    
#     def get_queryset(self):
#         return Report.objects.filter(reporter=self.request.user)

# retrieve details of a specific report -- applies to admin view
class ReportDetailView(generics.RetrieveAPIView):
    serializer_class = ReportDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'report_id'
    
    def get_queryset(self):
        # Users can only view their own reports unless they're staff
        if self.request.user.is_staff:
            return Report.objects.all()
        return Report.objects.filter(reporter=self.request.user)

# Admin Views (for staff users) - list and filter reports
class AdminReportListView(generics.ListAPIView):
    serializer_class = AdminReportSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get_queryset(self):
        queryset = Report.objects.all()
        
        # Filter parameters
        status_filter = self.request.query_params.get('status')
        priority_filter = self.request.query_params.get('priority')
        category_filter = self.request.query_params.get('category')
        item_type_filter = self.request.query_params.get('type')
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if priority_filter:
            queryset = queryset.filter(priority=priority_filter)
        if category_filter:
            queryset = queryset.filter(category__name=category_filter)
        if item_type_filter:
            if item_type_filter.lower() == 'post':
                content_type = ContentType.objects.get_for_model(Post)
                queryset = queryset.filter(content_type=content_type)
            elif item_type_filter.lower() == 'profile':
                content_type = ContentType.objects.get_for_model(UserProfile)
                queryset = queryset.filter(content_type=content_type)
        
        return queryset


# admin can update report status, action taken, admin notes, priority
@api_view(['PATCH'])
@permission_classes([permissions.IsAdminUser])
def update_report_status(request, report_id):
    report = get_object_or_404(Report, report_id=report_id)
    
    status_update = request.data.get('status')
    action_taken = request.data.get('action_taken')
    admin_notes = request.data.get('admin_notes', '')
    priority = request.data.get('priority')
    
    if status_update and status_update in [choice[0] for choice in Report.STATUS_CHOICES]:
        report.status = status_update
        if status_update in ['resolved', 'dismissed']:
            report.reviewed_by = request.user
            report.reviewed_at = timezone.now()
    
    if action_taken and action_taken in [choice[0] for choice in Report.ACTION_CHOICES]:
        report.action_taken = action_taken
    
    if admin_notes:
        report.admin_notes = admin_notes
    
    if priority and priority in [1, 2, 3]:
        report.priority = priority
    
    report.save()
    
    #login to perform action goes here (suspend user, remove post, etc.)
    
    return Response({
        'message': 'Report updated successfully',
        'report': AdminReportSerializer(report).data
    })

# get details of the reported item (post or profile)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_reported_item_details(request, report_id):
    report = get_object_or_404(Report, report_id=report_id)
    
    # Check permissions
    if not request.user.is_staff and report.reporter != request.user:
        return Response(
            {'error': 'Permission denied'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    reported_object = report.reported_object
    
    if isinstance(reported_object, Post):
        data = {
            'type': 'post',
            'id': reported_object.post_id,
            'title': reported_object.title,
            'description': reported_object.description,
            'author': reported_object.get_user_display_name(),
            'created_at': reported_object.created_at,
            'is_active': reported_object.is_active
        }
    elif isinstance(reported_object, UserProfile):
        data = {
            'type': 'profile',
            'id': str(reported_object.profile_id),
            'company_name': reported_object.company_name,
            'about_bio': reported_object.about_bio,
            'location': reported_object.location,
            'user_email': reported_object.user.email,
            'created_at': reported_object.created_at,
            'is_active': reported_object.user.state == 1
        }
    else:
        return Response(
            {'error': 'Unknown reported item type'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    return Response(data)
