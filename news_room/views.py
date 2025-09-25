from rest_framework import generics, filters, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, F
from django.utils import timezone
from datetime import timedelta
from news_room.serializers import ArticleListSerializer, ArticleDetailSerializer, CategorySerializer
from news_room.models import Article, Category


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 100

# custom filter class for articles
class ArticleFilter:
    @staticmethod
    def filter_queryset(queryset, request):
        # Filter by category
        category = request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__slug=category)
        
        # Filter by tag
        # tag = request.query_params.get('tag')
        # if tag:
        #     queryset = queryset.filter(tags__slug=tag)
        
        # Filter by country
        country = request.query_params.get('country')
        if country:
            queryset = queryset.filter(country__icontains=country)
        
        # Filter by priority
        priority = request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        # Filter by date range
        days_ago = request.query_params.get('days_ago')
        if days_ago:
            try:
                days = int(days_ago)
                since_date = timezone.now() - timedelta(days=days)
                queryset = queryset.filter(published_at__gte=since_date)
            except ValueError:
                pass
        
        # Search functionality
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(summary__icontains=search) |
                Q(content__icontains=search) 
                # Q(tags__name__icontains=search)
            ).distinct()
        
        return queryset

# list all articles with pagination and filtering
class ArticleListView(generics.ListAPIView):
    serializer_class = ArticleListSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ['published_at', 'views_count', 'likes_count']
    ordering = ['-published_at']

    def get_queryset(self):
        queryset = Article.objects.filter(
            status='published',
            published_at__isnull=False
        ).select_related('category', 'source')
        
        return ArticleFilter.filter_queryset(queryset, self.request)

# get detailed article
class ArticleDetailView(generics.RetrieveAPIView):
    serializer_class = ArticleDetailSerializer
    permission_classes = [AllowAny]
    lookup_field = 'article_id'

    def get_queryset(self):
        return Article.objects.filter(
            status='published'
        ).select_related('category', 'source')

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Increment views count
        Article.objects.filter(article_id=instance.article_id).update(views_count=F('views_count') + 1)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

# get featured articles 
class FeaturedArticlesView(generics.ListAPIView):
    serializer_class = ArticleListSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Article.objects.filter(
            status='featured',
            published_at__isnull=False
        ).select_related('category', 'source')

# get breaking news
class BreakingNewsView(generics.ListAPIView):
    serializer_class = ArticleListSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Article.objects.filter(
            priority='breaking',
            status='published',
            published_at__isnull=False
        ).select_related('category', 'source')[:5]

# get trending articles based on engagement
class TrendingArticlesView(generics.ListAPIView):
    serializer_class = ArticleListSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        # Get articles from last 7 days, ordered by engagement
        since_date = timezone.now() - timedelta(days=7)
        return Article.objects.filter(
            status='published',
            published_at__gte=since_date
        ).order_by(
            '-views_count', '-likes_count', '-shares_count'
        ).select_related('category', 'source')[:10]

# list active categories
class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]

# related articles based on category
class RelatedArticlesView(generics.ListAPIView):
    serializer_class = ArticleListSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        article_slug = self.kwargs.get('slug')
        try:
            article = Article.objects.get(slug=article_slug)
            # Get articles from same category or with similar tags
            related = Article.objects.filter(
                Q(category=article.category) 
            ).exclude(
                id=article.article_id
            ).filter(
                status='published'
            ).distinct().select_related(
                'category', 'source'
            )[:5]
            return related
        except Article.DoesNotExist:
            return Article.objects.none()


# class ArticleCommentsView(generics.ListCreateAPIView):
#     serializer_class = CommentSerializer
    
#     def get_permissions(self):
#         if self.request.method == 'POST':
#             return [IsAuthenticated()]
#         return [AllowAny()]

#     def get_queryset(self):
#         article_slug = self.kwargs.get('slug')
#         return Comment.objects.filter(
#             article__slug=article_slug,
#             parent__isnull=True,
#             is_approved=True
#         )

#     def perform_create(self, serializer):
#         article_slug = self.kwargs.get('slug')
#         article = Article.objects.get(slug=article_slug)
#         serializer.save(user=self.request.user, article=article)


# class NewsletterSubscriptionView(generics.CreateAPIView):
#     serializer_class = NewsletterSerializer
#     permission_classes = [AllowAny]

#     def create(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         if serializer.is_valid():
#             email = serializer.validated_data['email']
#             newsletter, created = Newsletter.objects.get_or_create(
#                 email=email,
#                 defaults=serializer.validated_data
#             )
#             if not created:
#                 newsletter.is_active = True
#                 newsletter.save()
            
#             return Response(
#                 {'message': 'Successfully subscribed to newsletter'},
#                 status=status.HTTP_201_CREATED
#             )
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def like_article(request, slug):
#     try:
#         article = Article.objects.get(slug=slug)
#         # Here you might want to create a Like model to track user likes
#         # For now, just increment the count
#         article.likes_count = F('likes_count') + 1
#         article.save()
#         return Response({'message': 'Article liked'})
#     except Article.DoesNotExist:
#         return Response({'error': 'Article not found'}, status=404)


# @api_view(['POST'])
# def share_article(request, slug):
#     try:
#         article = Article.objects.get(slug=slug)
#         article.shares_count = F('shares_count') + 1
#         article.save()
#         return Response({'message': 'Share counted'})
#     except Article.DoesNotExist:
#         return Response({'error': 'Article not found'}, status=404)


# advanced search
@api_view(['GET'])
@permission_classes([AllowAny])
def search_articles(request):
    query = request.query_params.get('q', '')
    if not query:
        return Response({'results': []})
    
    articles = Article.objects.filter(
        Q(title__icontains=query) |
        Q(summary__icontains=query) |
        Q(content__icontains=query) 
        # Q(author__name__icontains=query) |
        # Q(tags__name__icontains=query)
    ).filter(status='published').distinct().select_related(
        'category', 'source'
    )[:20]
    
    serializer = ArticleListSerializer(articles, many=True)
    return Response({'results': serializer.data})
