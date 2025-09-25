from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.auth import get_user_model
import uuid


Account = get_user_model()

# report category model
class ReportCategory(models.Model):
    CATEGORY_CHOICES = [
        ('fraud', 'Fraud'),
        ('harassment', 'Harassment'),
        ('misinformation', 'Misinformation'),
        ('hateful_speech', 'Hateful Speech'),
        ('self_harm', 'Self-harm'),
        ('scam', 'Scam'),
        ('sexual_content', 'Sexual Content'),
        ('infringement', 'Infringement'),
        ('spam', 'Spam'),
        ('illegal_goods', 'Illegal goods and services'),
        ('impersonation', 'Impersonation'),
        ('other', 'Other'),
    ]
    report_category_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, choices=CATEGORY_CHOICES, unique=True)
    display_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'report_categories'
        verbose_name_plural = 'Report Categories'
    
    def __str__(self):
        return self.display_name

# main report model
class Report(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('under_review', 'Under Review'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
        ('escalated', 'Escalated'),
    ]
    
    ACTION_CHOICES = [
        ('none', 'No Action'),
        ('warning', 'Send Warning'),
        ('content_removal', 'Content Removal'),
        ('account_suspension', 'Account Suspension'),
        ('account_deactivation', 'Account Deactivation'),
        ('other', 'Other Action'),
    ]
    
    report_id = models.CharField(max_length=20, unique=True, editable=False)
    reporter = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='reports_made')
    category = models.ForeignKey(ReportCategory, on_delete=models.SET_NULL, null=True)
    reason = models.TextField(max_length=500, blank=True)
    
    # Generic relationship to handle both Posts and UserProfiles
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=100)
    reported_object = GenericForeignKey('content_type', 'object_id')
    
    # Report status and handling
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.IntegerField(default=1, help_text="1=Low, 2=Medium, 3=High")
    
    # Admin handling
    reviewed_by = models.ForeignKey(
        Account, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='reports_reviewed',
        limit_choices_to={'is_staff': True}
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    action_taken = models.CharField(max_length=20, choices=ACTION_CHOICES, default='none')
    admin_notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'reports'
        ordering = ['-created_at']
        unique_together = ['reporter', 'content_type', 'object_id']  # Prevent duplicate reports
    
    def save(self, *args, **kwargs):
        if not self.report_id:
            # Generate report ID like LST-451, USR-691
            if self.content_type.model == 'post':
                prefix = 'LST'
            elif self.content_type.model == 'userprofile':
                prefix = 'USR'
            else:
                prefix = 'RPT'
            
            import random
            self.report_id = f"{prefix}-{random.randint(100, 999)}"
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.report_id} - {self.category.display_name if self.category else 'No Category'}"
    
    @property
    # get title or name of reported item
    def reported_item_title(self):
        if hasattr(self.reported_object, 'title'):
            return self.reported_object.title
        elif hasattr(self.reported_object, 'company_name') and self.reported_object.company_name:
            return self.reported_object.company_name
        elif hasattr(self.reported_object, 'user') and hasattr(self.reported_object.user, 'full_name'):
            return self.reported_object.user.full_name or self.reported_object.user.email
        return "Unknown Item"
    
    @property
    # get display name of reporter
    def reported_by_name(self):
        if hasattr(self.reporter, 'profile') and self.reporter.profile:
            if self.reporter.profile.company_name:
                return self.reporter.profile.company_name
        return self.reporter.full_name or self.reporter.email