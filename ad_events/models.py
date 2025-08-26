from django.db import models
from django.utils import timezone
import uuid

# model to categorize ads and events
class Category(models.Model):
    category_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0, help_text="Display order (lower numbers appear first)")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ad_event_categories'
        ordering = ['order', 'name']
        verbose_name_plural = 'Categories'
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

# advertisement and event model
class AdEvent(models.Model):
    TYPE_CHOICES = [
        ('advertisement', 'Advertisement'),
        ('event', 'Event'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('expired', 'Expired'),
        ('draft', 'Draft'),
    ]

    ad_event_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='items')
    description = models.TextField(null=True, blank=True)
    
    # Optional link field (for external links)
    link = models.URLField(max_length=500, null=True, blank=True)
    
    # Image/Banner upload
    banner_image = models.ImageField(upload_to='banners/%Y/%m/', null=True, blank=True)
    
    # Location and dates
    location = models.CharField(max_length=255, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    
    # Status and admin fields
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    is_featured = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ad_events'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['type', 'status']),
            models.Index(fields=['category']),
            models.Index(fields=['start_date', 'end_date']),
            models.Index(fields=['location']),
        ]
    
    def __str__(self):
        return f"{self.get_type_display()}: {self.title}"
    
    @property
    # check if the ad/event is active
    def is_active(self):
        if self.status != 'active':
            return False
        
        # Check if category is active
        if self.category and not self.category.is_active:
            return False
        
        if self.start_date and self.start_date > timezone.now().date():
            return False
            
        if self.end_date and self.end_date < timezone.now().date():
            return False
            
        return True
    
    @property
    # check if the event is upcoming
    def is_upcoming(self):
        if self.type != 'event' or not self.start_date:
            return False
        return self.start_date > timezone.now().date()
    
    @property
    # check if the ad/event is expired
    def is_expired(self):
        if not self.end_date:
            return False
        return self.end_date < timezone.now().date()