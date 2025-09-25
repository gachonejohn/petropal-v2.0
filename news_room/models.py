from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import URLValidator
import uuid

# news categories like price updates, government policies, etc.
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    # color = models.CharField(max_length=7, default='#007bff')  
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name


# class Tag(models.Model):
#     name = models.CharField(max_length=50, unique=True)
#     slug = models.SlugField(max_length=50, unique=True)
#     created_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         ordering = ['name']

#     def __str__(self):
#         return self.name



# news sources like TrendsAfrica, BBC, CNN, etc.
class Source(models.Model):
    source_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    website = models.URLField(validators=[URLValidator()])
    logo = models.ImageField(upload_to='news_source_logos/', blank=True, null=True)
    description = models.TextField(blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


# class Author(models.Model):
#     name = models.CharField(max_length=100)
#     bio = models.TextField(blank=True)
#     avatar = models.ImageField(upload_to='author_avatars/', blank=True, null=True)
#     email = models.EmailField(blank=True)
#     twitter = models.CharField(max_length=100, blank=True)
#     linkedin = models.URLField(blank=True)
#     is_verified = models.BooleanField(default=False)
#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return self.name


# main Article model representing news articles
class Article(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
        ('featured', 'Featured'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('breaking', 'Breaking News'),
    ]

    article_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    # subtitle = models.CharField(max_length=300, blank=True)
    summary = models.TextField(max_length=500, blank=True)
    content = models.TextField(max_length=3500, blank=True)
    
    # Media
    featured_image = models.ImageField(upload_to='articles/images/', blank=True, null=True)
    featured_image_caption = models.CharField(max_length=255, blank=True)
    video_url = models.URLField(blank=True)
    
    # Relationships
    # author = models.ForeignKey(Author, on_delete=models.SET_NULL, null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    source = models.ForeignKey(Source, on_delete=models.SET_NULL, null=True, blank=True)
    # tags = models.ManyToManyField(Tag, blank=True)
    
    # Metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Engagement
    views_count = models.PositiveIntegerField(default=0)
    likes_count = models.PositiveIntegerField(default=0)
    shares_count = models.PositiveIntegerField(default=0)
    
    # SEO
    meta_description = models.CharField(max_length=160, blank=True)
    meta_keywords = models.CharField(max_length=255, blank=True)
    
    # Location (for geo-targeted news)
    country = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)
    
    # External
    original_url = models.URLField(blank=True)
    external_id = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ['-published_at', '-created_at']
        indexes = [
            models.Index(fields=['status', 'published_at']),
            models.Index(fields=['category', 'published_at']),
            models.Index(fields=['priority', 'published_at']),
            models.Index(fields=['country', 'published_at']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    # estimated reading time in minutes
    @property
    def reading_time(self):
        word_count = len(self.content.split())
        return max(1, word_count // 200)  # Average 200 words per minute

    @property
    def is_breaking(self):
        return self.priority == 'breaking'

    # human readable time since publication
    @property
    def time_ago(self):
        if not self.published_at:
            return "Not published"
        
        now = timezone.now()
        diff = now - self.published_at
        
        if diff.days > 0:
            return f"{diff.days}d ago"
        elif diff.seconds > 3600:
            return f"{diff.seconds // 3600}h ago"
        else:
            return f"{diff.seconds // 60}m ago"


# class Comment(models.Model):
#     article = models.ForeignKey(Article, related_name='comments', on_delete=models.CASCADE)
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)
#     content = models.TextField()
#     likes_count = models.PositiveIntegerField(default=0)
#     is_approved = models.BooleanField(default=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     class Meta:
#         ordering = ['-created_at']

#     def __str__(self):
#         return f"Comment by {self.user.username} on {self.article.title}"


# class Newsletter(models.Model):
#     email = models.EmailField(unique=True)
#     is_active = models.BooleanField(default=True)
#     subscribed_categories = models.ManyToManyField(Category, blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return self.email