from rest_framework import serializers
from news_room.models import Article, Category, Source


class CategorySerializer(serializers.ModelSerializer):
    articles_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'articles_count']

    def get_articles_count(self, obj):
        return obj.article_set.filter(status='published').count()



class SourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Source
        fields = ['source_id', 'name', 'website', 'logo', 'is_verified']


# class AuthorSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Author
#         fields = ['id', 'name', 'bio', 'avatar', 'twitter', 'linkedin', 'is_verified']


# article list - summary view
class ArticleListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    source = SourceSerializer(read_only=True)
    # author = AuthorSerializer(read_only=True)
    # tags = TagSerializer(many=True, read_only=True)
    reading_time = serializers.ReadOnlyField()
    time_ago = serializers.ReadOnlyField()
    is_breaking = serializers.ReadOnlyField()

    class Meta:
        model = Article
        fields = [
            'article_id', 'title', 'slug','summary', 'featured_image',
            'category', 'source', 'original_url',
            'published_at', 'views_count',
            'likes_count', 'shares_count', 'reading_time', 'time_ago', 'priority',
            'is_breaking', 'country', 'region'
        ]


# article detail view with full content
class ArticleDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    source = SourceSerializer(read_only=True)
    # author = AuthorSerializer(read_only=True)
    # tags = TagSerializer(many=True, read_only=True)
    reading_time = serializers.ReadOnlyField()
    time_ago = serializers.ReadOnlyField()
    is_breaking = serializers.ReadOnlyField()
    # comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = [
            'article_id', 'title', 'slug', 'summary', 'content',
            'featured_image', 'featured_image_caption', 'video_url',
            'category', 'source', 'original_url', 'published_at',
            'views_count', 'likes_count', 'shares_count', 'reading_time',
            'time_ago', 'priority', 'is_breaking', 'country', 'region',
            'meta_description', 'meta_keywords',
        ]

    # def get_comments_count(self, obj):
    #     return obj.comments.filter(is_approved=True).count()


# class CommentSerializer(serializers.ModelSerializer):
#     user = serializers.StringRelatedField(read_only=True)
#     replies = serializers.SerializerMethodField()

#     class Meta:
#         model = Comment
#         fields = [
#             'id', 'user', 'content', 'likes_count', 'created_at',
#             'updated_at', 'replies'
#         ]

#     def get_replies(self, obj):
#         if obj.parent is None:
#             replies = Comment.objects.filter(parent=obj, is_approved=True)
#             return CommentSerializer(replies, many=True).data
#         return []


# class NewsletterSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Newsletter
#         fields = ['email', 'subscribed_categories']
