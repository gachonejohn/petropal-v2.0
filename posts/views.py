from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django.db import transaction
from posts.models import Post, PostImage, Category, PostComment, CommentLike, PostLike, PostView, PostShare
from .serializers import (
    PostCreateSerializer, PostUpdateSerializer, PostDetailSerializer,
    PostListSerializer, PostImageUploadSerializer, CategorySerializer,
    CommentCreateSerializer, CommentUpdateSerializer, CommentDetailSerializer,
    PostLikeSerializer, PostViewSerializer, PostStatsSerializer, SharePostSerializer, PostShareSerializer
)
from django.utils import timezone
from datetime import timedelta
from django.db import models

from django.urls import reverse
from urllib.parse import quote

from django.db.models import Case, When, Value, CharField
from django.db.models import Count
from datetime import datetime


FRONTEND_BASE_URL = "http://localhost:3000"


# get all categories
class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]

# Create a new post with images 
class PostCreateView(generics.CreateAPIView):
    serializer_class = PostCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def create(self, request, *args, **kwargs):
        # Handle multiple images from form data
        images = request.FILES.getlist('images')
        
        # Create dict directly without copying file objects to avoid pickle error
        data = dict(request.data.items())
        if images:
            data['images'] = images
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            post = serializer.save()
            
            # Return the created post with all details
            response_serializer = PostDetailSerializer(
                post, 
                context={'request': request}
            )
            
            return Response(
                {
                    'success': True,
                    'message': 'Post created successfully',
                    'data': response_serializer.data
                },
                status=status.HTTP_201_CREATED
            )

class PostImageUploadView(generics.CreateAPIView):
    serializer_class = PostImageUploadSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def create(self, request, *args, **kwargs):
        post_id = kwargs.get('post_id')
        post = get_object_or_404(Post, post_id=post_id, user=request.user)
        
        # Handle multiple images
        images = request.FILES.getlist('image')
        if not images:
            return Response(
                {'error': 'No images provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        uploaded_images = []
        
        with transaction.atomic():
            for i, image in enumerate(images):
                # Set first image as primary if no primary image exists
                is_primary = i == 0 and not post.images.filter(is_primary=True).exists()
                
                post_image = PostImage.objects.create(
                    post=post,
                    image=image,
                    is_primary=is_primary,
                    order=i
                )
                
                serializer = PostImageUploadSerializer(post_image, context={'request': request})
                uploaded_images.append(serializer.data)
        
        return Response(
            {
                'success': True,
                'message': f'{len(uploaded_images)} image(s) uploaded successfully',
                'data': uploaded_images
            },
            status=status.HTTP_201_CREATED
        )

class PostDetailView(generics.RetrieveAPIView):
    queryset = Post.objects.filter(is_active=True)
    serializer_class = PostDetailSerializer
    lookup_field = 'post_id'
    permission_classes = [permissions.AllowAny]

# Update post - 
class PostUpdateView(generics.UpdateAPIView):
    serializer_class = PostUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    lookup_field = 'post_id'
    
    def get_queryset(self):
        return Post.objects.filter(user=self.request.user, is_active=True)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Handle multiple images from form data
        images = request.FILES.getlist('images')
        
        # FIXED: Create dict directly without copying file objects to avoid pickle error
        data = dict(request.data.items())
        if images:
            data['images'] = images
        
        # Handle remove_images parameter (comma-separated string to list)
        remove_images = request.data.get('remove_images', '')
        if remove_images:
            if isinstance(remove_images, str):
                data['remove_images'] = [int(x.strip()) for x in remove_images.split(',') if x.strip()]
            else:
                data['remove_images'] = remove_images
        
        serializer = self.get_serializer(instance, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            updated_post = serializer.save()
            
            # Return updated post with all details
            response_serializer = PostDetailSerializer(
                updated_post,
                context={'request': request}
            )
            
            return Response(
                {
                    'success': True,
                    'message': 'Post updated successfully',
                    'data': response_serializer.data
                }
            )

# latest listings (8)
class LatestPostsView(generics.ListAPIView):
    queryset = Post.objects.filter(is_active=True).order_by('-created_at')[:8]
    serializer_class = PostListSerializer
    permission_classes = [permissions.AllowAny]

class PostListView(generics.ListAPIView):
    queryset = Post.objects.filter(is_active=True)
    serializer_class = PostListSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Optional filtering
        category = self.request.query_params.get('category')
        location = self.request.query_params.get('location')
        search = self.request.query_params.get('search')
        
        if category:
            queryset = queryset.filter(category__slug=category)
        if location:
            queryset = queryset.filter(location__icontains=location)
        if search:
            queryset = queryset.filter(title__icontains=search)
        
        return queryset


# user's own posts
class MyPostsView(generics.ListAPIView):
    serializer_class = PostListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Post.objects.filter(user=self.request.user, is_active=True)

class PostDeleteView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'post_id'
    
    def get_queryset(self):
        return Post.objects.filter(user=self.request.user, is_active=True)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        
        return Response(
            {
                'success': True,
                'message': 'Post deleted successfully'
            },
            status=status.HTTP_200_OK
        )

@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def delete_post_image(request, post_id, image_id):
    post = get_object_or_404(Post, post_id=post_id, user=request.user)
    image = get_object_or_404(PostImage, id=image_id, post=post)
    
    # If deleting primary image, set another image as primary
    if image.is_primary:
        next_image = post.images.exclude(id=image_id).first()
        if next_image:
            next_image.is_primary = True
            next_image.save()
    
    image.delete()
    
    return Response(
        {
            'success': True,
            'message': 'Image deleted successfully'
        },
        status=status.HTTP_200_OK
    )

@api_view(['PATCH'])
@permission_classes([permissions.IsAuthenticated])
def set_primary_image(request, post_id, image_id):
    post = get_object_or_404(Post, post_id=post_id, user=request.user)
    
    # Remove primary status from all images
    post.images.update(is_primary=False)
    
    # Set the specified image as primary
    image = get_object_or_404(PostImage, id=image_id, post=post)
    image.is_primary = True
    image.save()
    
    return Response(
        {
            'success': True,
            'message': 'Primary image updated successfully'
        },
        status=status.HTTP_200_OK
    )







# poss interactions views
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def get_user_agent(request):
    return request.META.get('HTTP_USER_AGENT', '')

# Generate share URLs for different platforms
def generate_share_urls(post, request, message=""):
    # Use frontend/app route instead of API route:
    post_url = f"{FRONTEND_BASE_URL}/posts/{post.post_id}/"
    post_title = post.title
    from urllib.parse import quote
    encoded_title = quote(post_title)
    encoded_url = quote(post_url)
    encoded_message = quote(message) if message else quote(f"Check out this post: {post_title}")

    share_urls = {
        'direct_link': post_url,
        'whatsapp': f"https://wa.me/?text={encoded_message}%20{encoded_url}",
        'facebook': f"https://www.facebook.com/sharer/sharer.php?u={encoded_url}",
        'share_x': f"https://x.com/intent/tweet?text={encoded_message}&url={encoded_url}",
        'linkedin': f"https://www.linkedin.com/sharing/share-offsite/?url={encoded_url}",
        'telegram': f"https://t.me/share/url?url={encoded_url}&text={encoded_message}",
    }
    return share_urls

# POST LIKE/UNLIKE VIEWS
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def toggle_post_like(request, post_id):
    post = get_object_or_404(Post, post_id=post_id, is_active=True)
    
    like, created = PostLike.objects.get_or_create(post=post, user=request.user)
    
    if created:
        return Response({
            'success': True,
            'message': 'Post liked successfully',
            'is_liked': True,
            'likes_count': post.likes.count()
        }, status=status.HTTP_201_CREATED)
    else:
        like.delete()
        return Response({
            'success': True,
            'message': 'Post unliked successfully',
            'is_liked': False,
            'likes_count': post.likes.count()
        }, status=status.HTTP_200_OK)

@api_view(['GET'])
# List all likes for a post
@permission_classes([permissions.AllowAny])
def post_likes_list(request, post_id):
    post = get_object_or_404(Post, post_id=post_id, is_active=True)
    likes = post.likes.all().order_by('-created_at')
    
    serializer = PostLikeSerializer(likes, many=True)
    
    return Response({
        'success': True,
        'data': {
            'likes_count': likes.count(),
            'likes': serializer.data
        }
    })

# POST VIEW TRACKING
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def record_post_view(request, post_id):
    post = get_object_or_404(Post, post_id=post_id, is_active=True)
    
    user = request.user if request.user.is_authenticated else None
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    
    # Check for recent views to avoid duplicates
    one_hour_ago = timezone.now() - timedelta(hours=1)
    
    if user:
        # Check if authenticated user already viewed this post recently
        recent_view = post.views.filter(
            user=user,
            viewed_at__gte=one_hour_ago
        ).exists()
        
        if recent_view:
            return Response({
                'success': True,
                'message': 'View recorded',
                'views_count': post.views.count()
            })
    else:
        # Check if anonymous user (by IP) already viewed this post recently
        recent_view = post.views.filter(
            ip_address=ip_address,
            user=None,
            viewed_at__gte=one_hour_ago
        ).exists()
        
        if recent_view:
            return Response({
                'success': True,
                'message': 'View recorded',
                'views_count': post.views.count()
            })
    
    # Record the view
    PostView.objects.create(
        post=post,
        user=user,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return Response({
        'success': True,
        'message': 'View recorded successfully',
        'views_count': post.views.count()
    }, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def post_views_list(request, post_id):
    post = get_object_or_404(Post, post_id=post_id, is_active=True)
    
    # Only post owner can see detailed view information
    if request.user.is_authenticated and request.user == post.user:
        views = post.views.all().order_by('-viewed_at')[:50]  # Limit to last 50 views
        serializer = PostViewSerializer(views, many=True)
        
        return Response({
            'success': True,
            'data': {
                'views_count': post.views.count(),
                'recent_views': serializer.data
            }
        })
    else:
        # Public users only see count
        return Response({
            'success': True,
            'data': {
                'views_count': post.views.count()
            }
        })

# COMMENT VIEWS
class PostCommentsListView(generics.ListAPIView):
    serializer_class = CommentDetailSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        post_id = self.kwargs['post_id']
        post = get_object_or_404(Post, post_id=post_id, is_active=True)
        # Only return main comments (not replies)
        return post.comments.filter(parent=None, is_active=True).order_by('-created_at')
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'success': True,
            'data': {
                'comments_count': queryset.count(),
                'comments': serializer.data
            }
        })

class CommentCreateView(generics.CreateAPIView):
    serializer_class = CommentCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        post_id = kwargs.get('post_id')
        post = get_object_or_404(Post, post_id=post_id, is_active=True)
        
        serializer = self.get_serializer(
            data=request.data,
            context={'request': request, 'post': post}
        )
        serializer.is_valid(raise_exception=True)
        
        comment = serializer.save()
        
        response_serializer = CommentDetailSerializer(
            comment,
            context={'request': request}
        )
        
        return Response({
            'success': True,
            'message': 'Comment created successfully',
            'data': response_serializer.data
        }, status=status.HTTP_201_CREATED)

# Update a comment - owner
class CommentUpdateView(generics.UpdateAPIView):
    serializer_class = CommentUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'comment_id'
    
    def get_queryset(self):
        return PostComment.objects.filter(user=self.request.user, is_active=True)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        updated_comment = serializer.save()
        
        response_serializer = CommentDetailSerializer(
            updated_comment,
            context={'request': request}
        )
        
        return Response({
            'success': True,
            'message': 'Comment updated successfully',
            'data': response_serializer.data
        })

# Delete a comment - owner or post owner
class CommentDeleteView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'comment_id'
    
    def get_queryset(self):
        # User can delete their own comments or comments on their posts
        return PostComment.objects.filter(
            models.Q(user=self.request.user) | models.Q(post__user=self.request.user),
            is_active=True
        )
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        
        return Response({
            'success': True,
            'message': 'Comment deleted successfully'
        }, status=status.HTTP_200_OK)

# COMMENT LIKE/UNLIKE
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def toggle_comment_like(request, comment_id):
    comment = get_object_or_404(PostComment, comment_id=comment_id, is_active=True)
    
    like, created = CommentLike.objects.get_or_create(comment=comment, user=request.user)
    
    if created:
        return Response({
            'success': True,
            'message': 'Comment liked successfully',
            'is_liked': True,
            'likes_count': comment.likes.count()
        }, status=status.HTTP_201_CREATED)
    else:
        like.delete()
        return Response({
            'success': True,
            'message': 'Comment unliked successfully',
            'is_liked': False,
            'likes_count': comment.likes.count()
        }, status=status.HTTP_200_OK)

# POST STATS
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def post_stats(request, post_id):
    post = get_object_or_404(Post, post_id=post_id, is_active=True)
    
    stats_data = {
        'likes_count': post.likes.count(),
        'views_count': post.views.count(),
        'comments_count': post.comments.filter(parent=None, is_active=True).count(),
        'total_comments_count': post.comments.filter(is_active=True).count(),
        'is_liked': False
    }
    
    if request.user.is_authenticated:
        stats_data['is_liked'] = post.likes.filter(user=request.user).exists()
    
    serializer = PostStatsSerializer(stats_data)
    
    return Response({
        'success': True,
        'data': serializer.data
    })


# ANALYTICS FOR POST OWNERS
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def my_post_analytics(request, post_id):
    post = get_object_or_404(Post, post_id=post_id, user=request.user, is_active=True)

    # Parse query params
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    try:
        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        else:
            # Default to last 30 days
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=29)
    except Exception:
        return Response({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)

    days = (end_date - start_date).days + 1
    engagement_trend = []
    for i in range(days):
        date = start_date + timedelta(days=i)
        views = post.views.filter(viewed_at__date=date).count()
        likes = post.likes.filter(created_at__date=date).count()
        comments = post.comments.filter(is_active=True, created_at__date=date).count()
        engagement_trend.append({
            'date': date.isoformat(),
            'views': views,
            'likes': likes,
            'comments': comments,
            'total': views + likes + comments,
        })

    # Basic stats
    likes_count = post.likes.count()
    views_count = post.views.count()
    comments_count = post.comments.filter(is_active=True).count()

    # Recent activity (in selected range)
    recent_likes = post.likes.filter(created_at__gte=start_date, created_at__lte=end_date).count()
    recent_views = post.views.filter(viewed_at__gte=start_date, viewed_at__lte=end_date).count()
    recent_comments = post.comments.filter(
        created_at__gte=start_date,
        created_at__lte=end_date,
        is_active=True
    ).count()

    # Top commenters
    top_commenters = PostComment.objects.filter(
        post=post,
        is_active=True,
        created_at__gte=start_date,
        created_at__lte=end_date,
    ).annotate(
        company_name=Case(
            When(user__profile__company_name__isnull=False, then=Value('user__profile__company_name')),
            default=Value('user__full_name'),
            output_field=CharField()
        ),
        display_name=Case(
            When(user__profile__company_name__isnull=False, then=Value('user__profile__company_name')),
            default=Value('user__full_name'),
            output_field=CharField()
        ),
    ).values(
        'user__email',
        'display_name'
    ).annotate(
        comment_count=Case(
            When(is_active=True, then=Value(1)),
            default=Value(0),
            output_field=CharField()
        )
    ).order_by('-comment_count')[:5]

    engagement_rate = round((recent_likes + recent_comments) / max(recent_views, 1) * 100, 2) if recent_views > 0 else 0

    analytics_data = {
        'total_stats': {
            'likes_count': likes_count,
            'views_count': views_count,
            'comments_count': comments_count
        },
        'recent_activity': {
            'recent_likes': recent_likes,
            'recent_views': recent_views,
            'recent_comments': recent_comments
        },
        'top_commenters': list(top_commenters),
        'engagement_rate': engagement_rate,
        'engagement_trend': engagement_trend,
    }

    return Response({
        'success': True,
        'data': analytics_data
    })



# Share Post 
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def share_post(request, post_id):
    post = get_object_or_404(Post, post_id=post_id, is_active=True)
    
    serializer = SharePostSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    share_method = serializer.validated_data['share_method']
    message = serializer.validated_data.get('message', '')
    
    user = request.user if request.user.is_authenticated else None
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    
    # Check for spam prevention (limit shares per IP/user per hour)
    one_hour_ago = timezone.now() - timedelta(hours=1)
    
    if user:
        recent_shares = PostShare.objects.filter(
            user=user,
            shared_at__gte=one_hour_ago
        ).count()
        share_limit = 50  # Authenticated users get higher limit
    else:
        recent_shares = PostShare.objects.filter(
            ip_address=ip_address,
            user=None,
            shared_at__gte=one_hour_ago
        ).count()
        share_limit = 10  # Anonymous users get lower limit
    
    if recent_shares >= share_limit:
        return Response({
            'success': False,
            'error': 'Share limit exceeded. Please try again later.'
        }, status=status.HTTP_429_TOO_MANY_REQUESTS)
    
    # Create share record
    post_share = PostShare.objects.create(
        post=post,
        user=user,
        share_method=share_method,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    # Generate share URLs for social media and messaging platforms
    share_urls = generate_share_urls(post, request, message)
    
    response_data = {
        'success': True,
        'message': 'Post shared successfully',
        'share_id': post_share.share_id,
        'shares_count': post.shares.count(),
        'share_url': share_urls.get(share_method, share_urls['direct_link'])
    }
    
    return Response(response_data, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_share_urls(request, post_id):
    post = get_object_or_404(Post, post_id=post_id, is_active=True)
    
    message = request.GET.get('message', '')
    share_urls = generate_share_urls(post, request, message)
    
    return Response({
        'success': True,
        'data': {
            'post_title': post.title,
            'share_urls': share_urls,
            'shares_count': post.shares.count()
        }
    })

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def post_shares_list(request, post_id):
    post = get_object_or_404(Post, post_id=post_id, is_active=True)
    
    # Basic stats available to everyone
    shares_count = post.shares.count()
    
    # Detailed information only for post owner
    if request.user.is_authenticated and request.user == post.user:
        shares = post.shares.all().order_by('-shared_at')[:50]  # Last 50 shares
        serializer = PostShareSerializer(shares, many=True)
        
        # Share method breakdown
        shares_by_method = {}
        for share in post.shares.values('share_method').annotate(count=models.Count('share_id')):
            shares_by_method[share['share_method']] = share['count']
        
        return Response({
            'success': True,
            'data': {
                'shares_count': shares_count,
                'shares_by_method': shares_by_method,
                'recent_shares': serializer.data
            }
        })
    else:
        # Public users only see count
        return Response({
            'success': True,
            'data': {
                'shares_count': shares_count
            }
        })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def my_post_share_analytics(request, post_id):
    
    post = get_object_or_404(Post, post_id=post_id, user=request.user, is_active=True)

    # Parse query params
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    try:
        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        else:
            # Default: last 7 days
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=6)
    except Exception:
        return Response({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)

    days = (end_date - start_date).days + 1
    share_trend = []
    for i in range(days):
        date = start_date + timedelta(days=i)
        day_shares = post.shares.filter(shared_at__date=date).count()
        share_trend.append({
            'date': date.isoformat(),
            'shares': day_shares
        })

    # Basic stats
    total_shares = post.shares.count()
    recent_shares = post.shares.filter(shared_at__gte=start_date, shared_at__lte=end_date).count()

    # Shares by method
    shares_by_method = {}
    for share in post.shares.values('share_method').annotate(count=models.Count('share_id')):
        method_display = dict(PostShare.SHARE_METHODS).get(share['share_method'], share['share_method'])
        shares_by_method[method_display] = share['count']

    # Top sharing platforms
    top_platforms = post.shares.values('share_method').annotate(
        count=models.Count('share_id')
    ).order_by('-count')[:5]

    social_shares = post.shares.exclude(share_method__in=['copy_link', 'direct_link']).count()
    link_shares = post.shares.filter(share_method__in=['copy_link', 'direct_link']).count()

    analytics_data = {
        'total_shares': total_shares,
        'recent_shares': recent_shares,
        'shares_by_method': shares_by_method,
        'share_trend': share_trend,
        'top_platforms': [
            {
                'method': dict(PostShare.SHARE_METHODS).get(item['share_method'], item['share_method']),
                'count': item['count']
            }
            for item in top_platforms
        ],
        'share_stats': {
            'social_shares': social_shares,
            'link_shares': link_shares
        },
        'engagement_metrics': {
            'shares_per_view': round(total_shares / max(post.views.count(), 1) * 100, 2),
            'shares_per_like': round(total_shares / max(post.likes.count(), 1) * 100, 2)
        }
    }

    return Response({
        'success': True,
        'data': analytics_data
    })