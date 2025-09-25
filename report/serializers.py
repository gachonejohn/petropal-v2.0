from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from report.models import ReportCategory, Report, Report
from profiles.models import UserProfile
from posts.models import Post

class ReportCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportCategory
        fields = [ 'report_category_id','name', 'display_name', 'description']

class CreateReportSerializer(serializers.ModelSerializer):
    reported_item_type = serializers.CharField(write_only=True)  # 'post' or 'profile'
    reported_item_id = serializers.CharField(write_only=True)
    category_name = serializers.CharField(write_only=True)
    
    class Meta:
        model = Report
        fields = ['category_name', 'reason', 'reported_item_type', 'reported_item_id']
    
    def validate(self, data):
        # Validate reported item exists
        item_type = data['reported_item_type'].lower()
        item_id = data['reported_item_id']
        
        if item_type == 'post':
            try:
                Post.objects.get(post_id=item_id)
                content_type = ContentType.objects.get_for_model(Post)
                data['object_id'] = item_id
            except Post.DoesNotExist:
                raise serializers.ValidationError("Post not found")
                
        elif item_type == 'profile':
            try:
                profile = UserProfile.objects.get(profile_id=item_id)
                content_type = ContentType.objects.get_for_model(UserProfile)
                data['object_id'] = str(item_id)
            except UserProfile.DoesNotExist:
                raise serializers.ValidationError("Profile not found")
        else:
            raise serializers.ValidationError("Invalid item type. Must be 'post' or 'profile'")
        
        data['content_type'] = content_type
        
        # Validate category
        try:
            category = ReportCategory.objects.get(name=data['category_name'], is_active=True)
            data['category'] = category
        except ReportCategory.DoesNotExist:
            raise serializers.ValidationError("Invalid report category")
        
        return data
    
    def create(self, validated_data):
        # Remove our custom fields
        validated_data.pop('reported_item_type')
        validated_data.pop('reported_item_id')
        validated_data.pop('category_name')
        
        # Set reporter from request context
        validated_data['reporter'] = self.context['request'].user
        
        return super().create(validated_data)

class ReportDetailSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.display_name', read_only=True)
    reported_item_title = serializers.CharField(read_only=True)
    reported_by_name = serializers.CharField(read_only=True)
    reported_item_type = serializers.SerializerMethodField()
    
    class Meta:
        model = Report
        fields = [
            'report_id', 'category_name', 'reason', 'status', 'priority',
            'reported_item_title', 'reported_item_type', 'reported_by_name',
            'action_taken', 'admin_notes', 'created_at', 'updated_at'
        ]
    
    def get_reported_item_type(self, obj):
        return obj.content_type.model.title()

class AdminReportSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.display_name', read_only=True)
    reported_item_title = serializers.CharField(read_only=True)
    reported_by_name = serializers.CharField(read_only=True)
    reported_item_type = serializers.SerializerMethodField()
    reviewed_by_name = serializers.CharField(source='reviewed_by.full_name', read_only=True)
    
    class Meta:
        model = Report
        fields = [
            'report_id', 'category_name', 'reason', 'status', 'priority',
            'reported_item_title', 'reported_item_type', 'reported_by_name',
            'action_taken', 'admin_notes', 'reviewed_by_name', 'reviewed_at',
            'created_at', 'updated_at'
        ]
    
    def get_reported_item_type(self, obj):
        return obj.content_type.model.title()