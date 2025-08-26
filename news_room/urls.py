from django.urls import path
from news_room import views

urlpatterns = [
   # Articles
    path('industry-news/', views.ArticleListView.as_view(), name='article-list'),
    path('industry-news/<uuid:article_id>/', views.ArticleDetailView.as_view(), name='article-detail'),
    # path('articles/<slug:slug>/comments/', views.ArticleCommentsView.as_view(), name='article-comments'),
    path('industry-news/<uuid:article_id>/related/', views.RelatedArticlesView.as_view(), name='related-articles'),
    # path('articles/<str:article_id>/like/', views.like_article, name='like-article'),
    # path('articles/<str:article_id>/share/', views.share_article, name='share-article'),
    
    # Special article lists
    path('industry-news/featured/', views.FeaturedArticlesView.as_view(), name='featured-articles'),
    path('industry-news/breaking/', views.BreakingNewsView.as_view(), name='breaking-news'),
    path('industry-news/trending/', views.TrendingArticlesView.as_view(), name='trending-articles'),
    
    # Categories
    path('industry-news/categories/', views.CategoryListView.as_view(), name='category-list'),
    
    # Search
    path('industry-news/search/', views.search_articles, name='search-articles'),
    
    # Newsletter
    # path('newsletter/subscribe/', views.NewsletterSubscriptionView.as_view(), name='newsletter-subscribe'),
]