# urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Category endpoints
    path('post-categories/', views.CategoryListView.as_view(), name='category-list'),
    
    # Post CRUD endpoints 
    path('posts/', views.PostListView.as_view(), name='post-list'),
    path('posts/latest-listing/', views.LatestPostsView.as_view(), name='latest-posts'),
    path('posts/create/', views.PostCreateView.as_view(), name='post-create'),
    path('posts/my-posts/', views.MyPostsView.as_view(), name='my-posts'),
    path('posts/<str:post_id>/', views.PostDetailView.as_view(), name='post-detail'),
    path('posts/<str:post_id>/update/', views.PostUpdateView.as_view(), name='post-update'),
    path('posts/<str:post_id>/delete/', views.PostDeleteView.as_view(), name='post-delete'),
    
    # Additional image management endpoints 
    path('posts/<str:post_id>/upload-images/', views.PostImageUploadView.as_view(), name='post-image-upload'),
    path('posts/<str:post_id>/images/<int:image_id>/delete/', views.delete_post_image, name='delete-post-image'),
    path('posts/<str:post_id>/images/<int:image_id>/set-primary/', views.set_primary_image, name='set-primary-image'),

    # Post Interactions
    path('posts/<str:post_id>/like/', views.toggle_post_like, name='toggle_post_like'),
    path('posts/<str:post_id>/likes/', views.post_likes_list, name='post_likes_list'),
    path('posts/<str:post_id>/view/', views.record_post_view, name='record_post_view'),
    path('posts/<str:post_id>/views/', views.post_views_list, name='post_views_list'),
    path('posts/<str:post_id>/stats/', views.post_stats, name='post_stats'),

    # Comments
    path('posts/<str:post_id>/comments/', views.PostCommentsListView.as_view(), name='post_comments_list'),
    path('posts/<str:post_id>/comments/create/', views.CommentCreateView.as_view(), name='comment_create'),
    path('comments/<str:comment_id>/update/', views.CommentUpdateView.as_view(), name='comment_update'),
    path('comments/<str:comment_id>/delete/', views.CommentDeleteView.as_view(), name='comment_delete'),
    path('comments/<str:comment_id>/like/', views.toggle_comment_like, name='toggle_comment_like'),

    # Analytics (for post owners)
    path('posts/<str:post_id>/analytics/', views.my_post_analytics, name='my_post_analytics'),

    # share posts
    path('posts/<str:post_id>/share/', views.share_post, name='share-post'),
    path('posts/<str:post_id>/share-urls/', views.get_share_urls, name='get-share-urls'),
    path('posts/<str:post_id>/shares/', views.post_shares_list, name='post-shares-list'),
    path('posts/<str:post_id>/share-analytics/', views.my_post_share_analytics, name='post-share-analytics'),
    
]