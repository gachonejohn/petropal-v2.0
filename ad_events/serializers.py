from rest_framework import serializers
from .models import AdEvent, Category


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = [
            'category_id', 'name', 'slug', 'description',
            'is_active', 'order',
        ]


class AdEventListSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    category = CategorySerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    is_upcoming = serializers.BooleanField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = AdEvent
        fields = [
            'ad_event_id', 'title', 'type', 'type_display', 'category',
            'banner_image', 'location', 'start_date', 'end_date',
            'status', 'status_display', 'link', 'is_featured', 'is_active',
            'is_upcoming', 'is_expired', 'created_at', 'updated_at',
        ]


class AdEventDetailSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    category = CategorySerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    is_upcoming = serializers.BooleanField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = AdEvent
        fields = [
            'ad_event_id', 'title', 'type', 'type_display', 'category',
            'description', 'link', 'banner_image', 'location',
            'start_date', 'end_date', 'status', 'status_display',
            'is_featured', 'is_active', 'is_upcoming', 'is_expired',
            'created_at', 'updated_at',
        ]

# Serializers specific for advertisements 
class AdvertisementSerializer(AdEventListSerializer):
    class Meta(AdEventListSerializer.Meta):
        pass

# serializers specific for events
class EventSerializer(AdEventListSerializer):
    class Meta(AdEventListSerializer.Meta):
        pass