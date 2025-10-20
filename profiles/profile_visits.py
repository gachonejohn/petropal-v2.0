from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from profiles.models import ProfileVisit
from rest_framework.response import Response


""" not necessary but is a requirement with the current frontend structure
    to have both endpoints even if they point to the same function """
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_profile_visit_analytics(request):
    """Get profile visit analytics for current user"""
    user = request.user
    
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    
    visits_queryset = ProfileVisit.objects.filter(
        profile_owner=user,
        created_at__gte=start_date
    )
    
    total_visits = visits_queryset.count()
    
    authenticated_visitors = visits_queryset.exclude(visitor=None).values('visitor').distinct().count()
    anonymous_ips = visits_queryset.filter(visitor=None).values('visitor_ip').distinct().count()
    unique_visitors = authenticated_visitors + anonymous_ips
    
    authenticated_visits = visits_queryset.exclude(visitor=None).count()
    anonymous_visits = visits_queryset.filter(visitor=None).count()
    
    daily_visits = visits_queryset.extra(
        select={'day': 'date(created_at)'}
    ).values('day').annotate(
        count=Count('visit_id')
    ).order_by('day')
    
    recent_visitors = visits_queryset.exclude(visitor=None).select_related('visitor').order_by('-created_at')[:5]
    recent_visitor_data = []
    
    for visit in recent_visitors:
        recent_visitor_data.append({
            'visitor_name': visit.visitor.full_name,
            # 'visitor_username': visit.visitor.username,
            'visit_date': visit.created_at
        })
    
    return Response({
        'profile_visits': {
            'total_visits': total_visits,
            'unique_visitors': unique_visitors,
            'authenticated_visits': authenticated_visits,
            'anonymous_visits': anonymous_visits,
            'description': 'Track how many users have viewed your profile.'
        },
        'daily_visits': list(daily_visits),
        'recent_visitors': recent_visitor_data,
        'date_range': f'Last {days} days'
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_profile_visit_count(request):
    """Get visit count for current user"""
    user = request.user
    
    now = timezone.now()
    
    # Last 24 hours
    yesterday = now - timedelta(days=1)
    last_24h = ProfileVisit.objects.filter(
        profile_owner=user,
        created_at__gte=yesterday
    ).count()
    
    # Last 7 days
    week_ago = now - timedelta(days=7)
    last_7_days = ProfileVisit.objects.filter(
        profile_owner=user,
        created_at__gte=week_ago
    ).count()
    
    # Last 30 days
    month_ago = now - timedelta(days=30)
    last_30_days = ProfileVisit.objects.filter(
        profile_owner=user,
        created_at__gte=month_ago
    ).count()
    
    # All time
    all_time = ProfileVisit.objects.filter(profile_owner=user).count()
    
    return Response({
        'last_24_hours': last_24h,
        'last_7_days': last_7_days,
        'last_30_days': last_30_days,
        'all_time': all_time
    })




@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_recent_profile_visit_analytics(request):
    """Get profile visit analytics for current user"""
    user = request.user
    
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    
    # Base queryset
    visits_queryset = ProfileVisit.objects.filter(
        profile_owner=user,
        created_at__gte=start_date
    )
    
    total_visits = visits_queryset.count()
    
    authenticated_visitors = visits_queryset.exclude(visitor=None).values('visitor').distinct().count()
    anonymous_ips = visits_queryset.filter(visitor=None).values('visitor_ip').distinct().count()
    unique_visitors = authenticated_visitors + anonymous_ips
    
    authenticated_visits = visits_queryset.exclude(visitor=None).count()
    anonymous_visits = visits_queryset.filter(visitor=None).count()
    
    daily_visits = visits_queryset.extra(
        select={'day': 'date(created_at)'}
    ).values('day').annotate(
        count=Count('visit_id')
    ).order_by('day')
    
    recent_visitors = visits_queryset.exclude(
        visitor=None
    ).select_related(
        'visitor',
        'visitor__profile'
    ).order_by('-created_at')[:5]
    
    recent_visitor_data = []
    for visit in recent_visitors:
        visitor_data = {
            'visitor_acc_id': str(visit.visitor.acc_id),
            'visitor_name': visit.visitor.full_name,
            'visit_date': visit.created_at
        }
        
        if hasattr(visit.visitor, 'profile') and visit.visitor.profile:
            visitor_data['visitor_profile_id'] = str(visit.visitor.profile.profile_id)
            visitor_data['visitor_profile_picture'] = (
                request.build_absolute_uri(visit.visitor.profile.profile_picture.url)
                if visit.visitor.profile.profile_picture
                else None
            )
        else:
            visitor_data['visitor_profile_id'] = None
            visitor_data['visitor_profile_picture'] = None
        
        recent_visitor_data.append(visitor_data)
    
    return Response({
        'profile_visits': {
            'total_visits': total_visits,
            'unique_visitors': unique_visitors,
            'authenticated_visits': authenticated_visits,
            'anonymous_visits': anonymous_visits,
            'description': 'Track how many users have viewed your profile.'
        },
        # 'daily_visits': list(daily_visits),
        'recent_visitors': recent_visitor_data,
        'date_range': f'Last {days} days'
    })