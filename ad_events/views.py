from rest_framework import generics, filters
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db import models
from ad_events.models import AdEvent, Category
from ad_events.serializers import (
    AdEventListSerializer, 
    AdEventDetailSerializer,
    AdvertisementSerializer,
    EventSerializer,
    CategorySerializer
)

# lists all active categories
class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering = ['order', 'name']

# lists all active ads and events
class AdEventListView(generics.ListAPIView):
    queryset = AdEvent.objects.filter(status='active').select_related('category')
    serializer_class = AdEventListSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['type', 'category', 'location', 'is_featured']
    search_fields = ['title', 'description', 'location']
    ordering_fields = ['created_at', 'start_date', 'end_date', 'title']
    ordering = ['-created_at']

# detailed view of a specific ad or event
class AdEventDetailView(generics.RetrieveAPIView):
    queryset = AdEvent.objects.filter(status='active').select_related('category')
    serializer_class = AdEventDetailSerializer
    permission_classes = [AllowAny]
    lookup_field = 'ad_event_id'

# list all ads only
class AdvertisementListView(generics.ListAPIView):
    queryset = AdEvent.objects.filter(type='advertisement', status='active').select_related('category')
    serializer_class = AdvertisementSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'location', 'is_featured']
    search_fields = ['title', 'description', 'location']
    ordering_fields = ['created_at', 'start_date', 'end_date', 'title']
    ordering = ['-created_at']

# list all events only
class EventListView(generics.ListAPIView):
    queryset = AdEvent.objects.filter(type='event', status='active').select_related('category')
    serializer_class = EventSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'location', 'is_featured']
    search_fields = ['title', 'description', 'location']
    ordering_fields = ['created_at', 'start_date', 'end_date', 'title']
    ordering = ['-created_at']

# list featured items (ads or events)
class FeaturedItemsView(generics.ListAPIView):
    queryset = AdEvent.objects.filter(status='active', is_featured=True).select_related('category')
    serializer_class = AdEventListSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.OrderingFilter]
    ordering = ['-created_at']

# list upcoming events only
class UpcomingEventsView(generics.ListAPIView):
    serializer_class = EventSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'location']
    search_fields = ['title', 'description', 'location']
    ordering_fields = ['start_date', 'created_at', 'title']
    ordering = ['start_date']

    def get_queryset(self):
        today = timezone.now().date()
        return AdEvent.objects.filter(
            type='event',
            status='active',
            start_date__gt=today
        ).select_related('category')

# list currently active advertisements within a date range
class ActiveAdvertisementsView(generics.ListAPIView):
    serializer_class = AdvertisementSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'location', 'is_featured']
    search_fields = ['title', 'description', 'location']
    ordering_fields = ['created_at', 'start_date', 'end_date', 'title']
    ordering = ['-created_at']

    def get_queryset(self):
        today = timezone.now().date()
        return AdEvent.objects.filter(
            type='advertisement',
            status='active'
        ).filter(
            models.Q(start_date__isnull=True) | models.Q(start_date__lte=today)
        ).filter(
            models.Q(end_date__isnull=True) | models.Q(end_date__gte=today)
        ).select_related('category')

# list all items by category
class CategoryItemsView(generics.ListAPIView):
    serializer_class = AdEventListSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'location']
    ordering_fields = ['created_at', 'start_date', 'end_date', 'title']
    ordering = ['-created_at']

    def get_queryset(self):
        category_param = self.kwargs.get('category')
        
        # Try to get category by slug first, then by ID, then by name
        try:
            if category_param.isdigit():
                category = Category.objects.get(id=category_param, is_active=True)
            else:
                category = Category.objects.get(slug=category_param, is_active=True)
        except Category.DoesNotExist:
            try:
                category = Category.objects.get(name__iexact=category_param, is_active=True)
            except Category.DoesNotExist:
                return AdEvent.objects.none()
        
        return AdEvent.objects.filter(
            category=category,
            status='active'
        ).select_related('category')

# list all items by location
class LocationItemsView(generics.ListAPIView):
    serializer_class = AdEventListSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['type', 'category', 'is_featured']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'start_date', 'end_date', 'title']
    ordering = ['-created_at']

    def get_queryset(self):
        location = self.kwargs.get('location')
        return AdEvent.objects.filter(
            location__icontains=location,
            status='active'
        ).select_related('category')