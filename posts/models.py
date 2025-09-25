import uuid
import os
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MaxLengthValidator
from django.utils import timezone

Account = get_user_model()

# generate 8 character unique ID
def generate_custom_id():
    return str(uuid.uuid4()).replace('-', '')[:8].upper()

def post_image_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4().hex}.{ext}"
    return os.path.join('post_images', filename)

class Category(models.Model):
    category_id = models.CharField(
        primary_key=True, 
        max_length=8, 
        unique=True, 
        editable=False,
        default=generate_custom_id
    )
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'categories'
        verbose_name_plural = 'Categories'
    
    def __str__(self):
        return self.name

# default image for posts
def get_default_post_image():
    return 'defaults/default-post.jpg'

class Post(models.Model):
    post_id = models.CharField(
        primary_key=True, 
        max_length=8, 
        unique=True, 
        editable=False,
        default=generate_custom_id
    )
    user = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='posts')
    title = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    # price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price = models.CharField(max_length=50, null=True, blank=True)
    description = models.TextField(
        validators=[MaxLengthValidator(400)],
        help_text="Maximum 400 characters"
    )
    default_image = models.ImageField(
        upload_to='defaults/', 
        default=get_default_post_image,
        help_text="System default image when user uploads no images"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'posts'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.post_id} - {self.title}"
    
    def save(self, *args, **kwargs):
        # Auto-fill location from user profile if not provided
        if not self.location and hasattr(self.user, 'profile'):
            self.location = self.user.profile.location
        
        if not self.post_id:
            self.post_id = generate_custom_id()
        
        super().save(*args, **kwargs)
    
    def get_user_display_name(self):
        if hasattr(self.user, 'profile') and self.user.profile:
            # Check for company name first, then full name from profile
            if self.user.profile.company_name:
                return self.user.profile.company_name.strip()
        
        # Fallback to account level full_name
        if self.user.full_name:
            return self.user.full_name.strip()
        
        # Final fallback to email
        return self.user.email
    
    # get default image URL
    def get_default_image_url(self):
        if self.default_image:
            return self.default_image.url
        return '/static/images/default-post.jpg'  # Fallback static image
    
    # post interactions mixin
    def get_likes_count(self):
        return self.likes.count()
    
    def get_views_count(self):
        return self.views.count()
    
    def get_comments_count(self):
        return self.comments.filter(parent=None, is_active=True).count()
    
    def get_total_comments_count(self):
        return self.comments.filter(is_active=True).count()
    
    def is_liked_by_user(self, user):
        if not user or not user.is_authenticated:
            return False
        return self.likes.filter(user=user).exists()
    
    def toggle_like(self, user):
        if not user or not user.is_authenticated:
            return False, "User must be authenticated"
        
        like, created = PostLike.objects.get_or_create(post=self, user=user)
        if not created:
            like.delete()
            return False, "Post unliked"
        return True, "Post liked"
    
    def record_view(self, user=None, ip_address=None, user_agent=None):
        # Avoid duplicate views from same user within 1 hour
        from django.utils import timezone
        from datetime import timedelta
        
        one_hour_ago = timezone.now() - timedelta(hours=1)
        
        if user and user.is_authenticated:
            # Check if user already viewed this post in the last hour
            recent_view = self.views.filter(
                user=user,
                viewed_at__gte=one_hour_ago
            ).exists()
            
            if not recent_view:
                PostView.objects.create(
                    post=self,
                    user=user,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                return True
        else:
            # For anonymous users, check by IP
            if ip_address:
                recent_view = self.views.filter(
                    ip_address=ip_address,
                    user=None,
                    viewed_at__gte=one_hour_ago
                ).exists()
                
                if not recent_view:
                    PostView.objects.create(
                        post=self,
                        ip_address=ip_address,
                        user_agent=user_agent
                    )
                    return True
        
        return False  # View not recorded (duplicate)

class PostImage(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to=post_image_upload_path)
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'post_images'
        ordering = ['order', 'uploaded_at']
    
    def __str__(self):
        return f"Image for {self.post.post_id}"






# track user likes on posts
class PostLike(models.Model):
    like_id = models.CharField(
        primary_key=True, 
        max_length=8, 
        unique=True, 
        editable=False,
        default=generate_custom_id
       )   
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='post_likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'post_likes'
        unique_together = ('post', 'user')  # Prevent duplicate likes
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} likes {self.post.post_id}"


# track post views/visits
class PostView(models.Model):
    visit_id = models.CharField(
        primary_key=True, 
        max_length=8, 
        unique=True, 
        editable=False,
        default=generate_custom_id
    )
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='views')
    user = models.ForeignKey(
        Account, 
        on_delete=models.CASCADE, 
        related_name='post_views',
        null=True, 
        blank=True  # Allow anonymous views
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    viewed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'post_views'
        ordering = ['-viewed_at']
    
    def __str__(self):
        user_display = self.user.email if self.user else f"Anonymous ({self.ip_address})"
        return f"{user_display} viewed {self.post.post_id}"

# post comments with reply
class PostComment(models.Model):
    comment_id = models.CharField(
        primary_key=True,
        max_length=8,
        unique=True,
        editable=False,
        default=generate_custom_id
    )
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='post_comments')
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='replies'
    )
    content = models.TextField(
        validators=[MaxLengthValidator(500)],
        help_text="Maximum 500 characters"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'post_comments'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Comment {self.comment_id} on {self.post.post_id}"
    
    def save(self, *args, **kwargs):
        if not self.comment_id:
            self.comment_id = str(uuid.uuid4()).replace('-', '')[:8].upper()
        super().save(*args, **kwargs)
    
    @property
    def is_reply(self):
        return self.parent is not None
    
    # get display name for the user
    def get_user_display_name(self):
        if hasattr(self.user, 'profile') and self.user.profile:
            if self.user.profile.company_name:
                return self.user.profile.company_name.strip()
        
        if self.user.full_name:
            return self.user.full_name.strip()
        
        return self.user.email

# track comment likes
class CommentLike(models.Model):
    comment_like_id = models.CharField(
        primary_key=True,
        max_length=8,
        unique=True,
        editable=False,
        default=generate_custom_id
    )
    comment = models.ForeignKey(PostComment, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='comment_likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'comment_likes'
        unique_together = ('comment', 'user')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} likes comment {self.comment.comment_id}"




class PostShare(models.Model):
    SHARE_METHODS = [
        # ('email', 'Email'),
        ('whatsapp', 'WhatsApp'),
        ('facebook', 'Facebook'),
        ('share_x', 'Share X'),
        ('linkedin', 'LinkedIn'),
        ('telegram', 'Telegram'),
        ('copy_link', 'Copy Link'),
        ('direct_link', 'Direct Link'),
    ]
    
    share_id = models.CharField(
        primary_key=True,
        max_length=8,
        unique=True,
        editable=False,
        default=generate_custom_id
    )
    post = models.ForeignKey('Post', on_delete=models.CASCADE, related_name='shares')
    user = models.ForeignKey(Account, on_delete=models.CASCADE, null=True, blank=True)
    share_method = models.CharField(max_length=20, choices=SHARE_METHODS)
    # recipient_email = models.EmailField(null=True, blank=True)  # For email shares
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    shared_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'post_shares'
        indexes = [
            models.Index(fields=['post', '-shared_at']),
            models.Index(fields=['user', '-shared_at']),
            models.Index(fields=['share_method']),
        ]
    
    def __str__(self):
        return f"{self.post.title} shared via {self.share_method}"