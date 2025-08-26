from django.urls import path
from report import views

urlpatterns = [   
    # Public endpoints
    path('reports/categories/', views.ReportCategoryListView.as_view(), name='report-categories'),
    path('reports/create/', views.CreateReportView.as_view(), name='create-report'),
    # path('reports/my-reports/', views.UserReportsListView.as_view(), name='user-reports'),
    path('reports/<str:report_id>/', views.ReportDetailView.as_view(), name='report-detail'),

    # get details of the reported item (post or profile) -- applies to admin
    path('reports/<str:report_id>/item/', views.get_reported_item_details, name='reported-item-details'),

    # Admin endpoints
    path('admin/reports/', views.AdminReportListView.as_view(), name='admin-reports'),
    path('admin/reports/<str:report_id>/update/', views.update_report_status, name='update-report-status'), 
    
]