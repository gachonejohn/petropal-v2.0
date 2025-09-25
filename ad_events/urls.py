from django.urls import path
from ad_events import views


urlpatterns = [
    # Categories
    path('ads-events/categories/', views.CategoryListView.as_view(), name='category-list'),
    
    # General endpoints
    path('ads-events/', views.AdEventListView.as_view(), name='ad-event-list'),
    path('ads-events/<uuid:ad_event_id>/', views.AdEventDetailView.as_view(), name='ad-event-detail'),
    
    # Specific type endpoints
    path('ads-events/ads/', views.AdvertisementListView.as_view(), name='advertisement-list'),
    path('ads-events/events/', views.EventListView.as_view(), name='event-list'),
    
    # Featured items
    path('ads-events/featured/', views.FeaturedItemsView.as_view(), name='featured-items'),
    
    # Specialized endpoints
    path('ads-events/upcoming-events/', views.UpcomingEventsView.as_view(), name='upcoming-events'),
    path('ads-events/active-ads/', views.ActiveAdvertisementsView.as_view(), name='active-advertisements'),
    
    # Category and location based endpoints
    path('ads-events/category/<str:category>/', views.CategoryItemsView.as_view(), name='category-items'),
    path('ads-events/location/<str:location>/', views.LocationItemsView.as_view(), name='location-items'),
]
