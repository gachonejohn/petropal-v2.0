from rest_framework import serializers
from django.conf import settings
from posts.models import Post, PostImage, Category, PostComment, CommentLike, PostLike, PostView, PostShare

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['category_id', 'name', 'slug', 'description', 'is_active']

class PostImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = PostImage
        fields = ['id', 'image', 'image_url', 'is_primary', 'order']
    
    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None

class PostImageUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostImage
        fields = ['image', 'is_primary', 'order']

class PostCreateSerializer(serializers.ModelSerializer):
    location = serializers.CharField(required=False, allow_blank=True)
    # price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    price = serializers.CharField(required=False, allow_blank=True)
    images = serializers.ListField(
        child=serializers.ImageField(),
        required=False,
        allow_empty=True,
        write_only=True
    )
    
    class Meta:
        model = Post
        fields = ['title', 'category', 'location', 'price', 'description', 'images']
    
    def validate_description(self, value):
        if len(value) > 400:
            raise serializers.ValidationError("Description cannot exceed 400 characters.")
        return value
    
    def validate_images(self, value):
        if len(value) > 5:  # Limit to 5 images max
            raise serializers.ValidationError("Maximum 5 images allowed per post.")
        return value
    
    def create(self, validated_data):
        user = self.context['request'].user
        images_data = validated_data.pop('images', [])
        
        # Auto-fill location from user profile if not provided
        if not validated_data.get('location') and hasattr(user, 'profile'):
            validated_data['location'] = user.profile.location
        
        validated_data['user'] = user
        
        # Create the post
        post = super().create(validated_data)
        
        # Create images if provided
        for i, image in enumerate(images_data):
            PostImage.objects.create(
                post=post,
                image=image,
                is_primary=i == 0,  # First image is primary
                order=i
            )
        
        return post

class PostUpdateSerializer(serializers.ModelSerializer):
    location = serializers.CharField(required=False, allow_blank=True)
    # price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    price = serializers.CharField(required=False, allow_blank=True)
    images = serializers.ListField(
        child=serializers.ImageField(),
        required=False,
        allow_empty=True,
        write_only=True
    )
    remove_images = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True,
        write_only=True,
        help_text="List of image IDs to remove"
    )
    
    class Meta:
        model = Post
        fields = ['title', 'category', 'location', 'price', 'description', 'images', 'remove_images']
    
    def validate_description(self, value):
        if len(value) > 400:
            raise serializers.ValidationError("Description cannot exceed 400 characters.")
        return value
    
    def validate_images(self, value):
        if len(value) > 5:
            raise serializers.ValidationError("Maximum 5 images allowed per post.")
        return value
    
    def update(self, instance, validated_data):
        images_data = validated_data.pop('images', [])
        remove_images = validated_data.pop('remove_images', [])
        
        # Update basic post fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Remove specified images
        if remove_images:
            PostImage.objects.filter(
                id__in=remove_images,
                post=instance
            ).delete()
        
        # Add new images
        if images_data:
            existing_count = instance.images.count()
            for i, image in enumerate(images_data):
                PostImage.objects.create(
                    post=instance,
                    image=image,
                    is_primary=existing_count == 0 and i == 0,  # Set as primary if no existing images
                    order=existing_count + i
                )
        
        return instance

class PostDetailSerializer(serializers.ModelSerializer):
    images = PostImageSerializer(many=True, read_only=True)
    category = CategorySerializer(read_only=True)
    user_name = serializers.SerializerMethodField()
    user_email = serializers.EmailField(source='user.email', read_only=True)
    has_default_image = serializers.SerializerMethodField()
    primary_image = serializers.SerializerMethodField()
    default_image_url = serializers.SerializerMethodField()

    # Interaction fields
    likes_count = serializers.SerializerMethodField()
    views_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()
    
    class Meta:
        model = Post
        fields = [
            'post_id', 'title', 'category', 'location', 'price', 
            'description', 'images', 'user_name', 'user_email',
            'has_default_image', 'primary_image', 'default_image_url',             
            'likes_count', 'views_count', 'comments_count', 'user_id', 'is_liked',
            'comments', 'is_active', 'created_at', 'updated_at'
        ]
    
    def get_user_name(self, obj):
        return obj.get_user_display_name()
    
    def get_has_default_image(self, obj):
        return not obj.images.exists()
    
    def get_default_image_url(self, obj):
        request = self.context.get('request')
        default_url = obj.get_default_image_url()
        if request and default_url:
            return request.build_absolute_uri(default_url)
        return default_url
    
    def get_primary_image(self, obj):
        primary_image = obj.images.filter(is_primary=True).first()
        if primary_image:
            return PostImageSerializer(primary_image, context=self.context).data
        elif obj.images.exists():
            return PostImageSerializer(obj.images.first(), context=self.context).data
        
        # Return system default image info when no user images
        return {
            'image_url': self.get_default_image_url(obj),
            'is_primary': True,
            'is_system_default': True
        }
    
    def get_likes_count(self, obj):
        return obj.likes.count()
    
    def get_views_count(self, obj):
        return obj.views.count()
    
    def get_comments_count(self, obj):
        return obj.comments.filter(parent=None, is_active=True).count()
    
    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False
    
    def get_comments(self, obj):
        # Only return main comments (not replies)
        main_comments = obj.comments.filter(parent=None, is_active=True).order_by('-created_at')
        return CommentDetailSerializer(main_comments, many=True, context=self.context).data

class PostListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    primary_image = serializers.SerializerMethodField()
    user_name = serializers.SerializerMethodField()
    default_image_url = serializers.SerializerMethodField()

    # Interaction fields
    likes_count = serializers.SerializerMethodField()
    views_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    
    class Meta:
        model = Post
        fields = [
            'post_id', 'title', 'description', 'category', 'location', 'price',
            'primary_image', 'user_name', 'default_image_url',
            'likes_count', 'views_count', 'comments_count', 'user_id', 'is_liked', 'created_at'
        ]
    
    def get_user_name(self, obj):
        return obj.get_user_display_name()
    
    def get_default_image_url(self, obj):
        request = self.context.get('request')
        default_url = obj.get_default_image_url()
        if request and default_url:
            return request.build_absolute_uri(default_url)
        return default_url
    
    def get_primary_image(self, obj):
        primary_image = obj.images.filter(is_primary=True).first()
        if primary_image:
            return PostImageSerializer(primary_image, context=self.context).data
        elif obj.images.exists():
            return PostImageSerializer(obj.images.first(), context=self.context).data
        
        # Return system default image info when no user images
        return {
            'image_url': self.get_default_image_url(obj),
            'is_primary': True,
            'is_system_default': True
        }
    def get_likes_count(self, obj):
        return obj.likes.count()
    
    def get_views_count(self, obj):
        return obj.views.count()
    
    def get_comments_count(self, obj):
        return obj.comments.filter(parent=None, is_active=True).count()
    
    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False
    




# Comment Serializers
class CommentLikeSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    
    class Meta:
        model = CommentLike
        fields = ['user_name', 'created_at']
    
    def get_user_name(self, obj):
        if hasattr(obj.user, 'profile') and obj.user.profile:
            if obj.user.profile.company_name:
                return obj.user.profile.company_name.strip()
        
        if obj.user.full_name:
            return obj.user.full_name.strip()
        
        return obj.user.email

class CommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostComment
        fields = ['content', 'parent']
    
    def validate_content(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Comment must be at least 3 characters long.")
        if len(value) > 500:
            raise serializers.ValidationError("Comment cannot exceed 500 characters.")
        return value.strip()
    
    def validate_parent(self, value):
        if value:
            # Ensure parent comment belongs to the same post
            post = self.context.get('post')
            if post and value.post != post:
                raise serializers.ValidationError("Parent comment must belong to the same post.")
            
            # Prevent deeply nested replies (max 1 level)
            if value.parent is not None:
                raise serializers.ValidationError("Cannot reply to a reply. Please reply to the main comment.")
        
        return value
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        validated_data['post'] = self.context['post']
        return super().create(validated_data)

class CommentUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostComment
        fields = ['content']
    
    def validate_content(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Comment must be at least 3 characters long.")
        if len(value) > 500:
            raise serializers.ValidationError("Comment cannot exceed 500 characters.")
        return value.strip()

class CommentDetailSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    user_email = serializers.EmailField(source='user.email', read_only=True)
    likes_count = serializers.SerializerMethodField()
    replies_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()
    
    class Meta:
        model = PostComment
        fields = [
            'comment_id', 'content', 'user_name', 'user_email',
            'likes_count', 'replies_count', 'is_liked', 'is_reply',
            'can_edit', 'can_delete', 'replies', 'created_at', 'updated_at'
        ]
    
    def get_user_name(self, obj):
        return obj.get_user_display_name()
    
    def get_likes_count(self, obj):
        return obj.likes.count()
    
    def get_replies_count(self, obj):
        return obj.replies.filter(is_active=True).count()
    
    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False
    
    def get_can_edit(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.user == request.user
        return False
    
    def get_can_delete(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # User can delete their own comments or post owner can delete comments on their post
            return obj.user == request.user or obj.post.user == request.user
        return False
    
    def get_replies(self, obj):
        if not obj.is_reply:  # Only show replies for main comments
            replies = obj.replies.filter(is_active=True).order_by('created_at')
            return CommentDetailSerializer(replies, many=True, context=self.context).data
        return []

# Post Like Serializer
class PostLikeSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    
    class Meta:
        model = PostLike
        fields = ['user_name', 'created_at']
    
    def get_user_name(self, obj):
        if hasattr(obj.user, 'profile') and obj.user.profile:
            if obj.user.profile.company_name:
                return obj.user.profile.company_name.strip()
        
        if obj.user.full_name:
            return obj.user.full_name.strip()
        
        return obj.user.email

# Post View Serializer
class PostViewSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    
    class Meta:
        model = PostView
        fields = ['user_name', 'ip_address', 'viewed_at']
    
    def get_user_name(self, obj):
        if obj.user:
            if hasattr(obj.user, 'profile') and obj.user.profile:
                if obj.user.profile.company_name:
                    return obj.user.profile.company_name.strip()
            
            if obj.user.full_name:
                return obj.user.full_name.strip()
            
            return obj.user.email
        return "Anonymous"

# Stats Serializer
class PostStatsSerializer(serializers.Serializer):
    likes_count = serializers.IntegerField()
    views_count = serializers.IntegerField()
    comments_count = serializers.IntegerField()
    total_comments_count = serializers.IntegerField()
    is_liked = serializers.BooleanField()




# share post
class PostShareSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    post_title = serializers.CharField(source='post.title', read_only=True)
    
    class Meta:
        model = PostShare
        fields = [
            'share_id', 'post_title', 'user_name', 'share_method', 
            'recipient_email', 'shared_at'
        ]
    
    def get_user_name(self, obj):
        if obj.user:
            if hasattr(obj.user, 'profile') and obj.user.profile and obj.user.profile.company_name:
                return obj.user.profile.company_name.strip()
            if obj.user.full_name:
                return obj.user.full_name.strip()
            return obj.user.email
        return "Anonymous"

class SharePostSerializer(serializers.Serializer):
    SHARE_METHODS = [
        ('whatsapp', 'WhatsApp'),
        ('facebook', 'Facebook'),
        ('share_x', 'share_x'),
        ('linkedin', 'LinkedIn'),
        ('telegram', 'Telegram'),
        ('copy_link', 'Copy Link'),
        ('direct_link', 'Direct Link'),
    ]
    
    share_method = serializers.ChoiceField(choices=SHARE_METHODS)
    message = serializers.CharField(required=False, allow_blank=True, max_length=500)

class ShareStatsSerializer(serializers.Serializer):
    total_shares = serializers.IntegerField()
    shares_by_method = serializers.DictField()
    recent_shares = serializers.IntegerField()
    share_trend = serializers.ListField()