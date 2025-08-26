from django.contrib import admin
from django.utils.html import format_html
from news_room.models import Article, Category, Source


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'article_count', 'is_active', 'created_at']
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    
    def article_count(self, obj):
        return obj.article_set.count()
    article_count.short_description = 'Articles'


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'category', 'status', 'priority', 
        'published_at', 'views_count', 'is_breaking_badge'
    ]
    list_filter = [
        'status', 'priority', 'category', 'published_at', 
        'created_at', 'country'
    ]
    search_fields = ['title', 'summary', 'content']
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'published_at'
    # raw_id_fields = ['author']
    # filter_horizontal = ['tags']
    
    fieldsets = (
        ('Content', {
            'fields': ('title', 'slug', 'summary', 'content')
        }),
        ('Media', {
            'fields': ('featured_image', 'featured_image_caption', 'video_url')
        }),
        ('Metadata', {
            'fields': ('category', 'source','status', 'priority')
        }),
        ('Location', {
            'fields': ('country', 'region')
        }),
        ('SEO', {
            'fields': ('meta_description', 'meta_keywords'),
            'classes': ('collapse',)
        }),
        ('External', {
            'fields': ('original_url', 'external_id'),
            'classes': ('collapse',)
        })
    )
    
    def is_breaking_badge(self, obj):
        if obj.priority == 'breaking':
            return format_html('<span style="color: red; font-weight: bold;">🚨 BREAKING</span>')
        return ''
    is_breaking_badge.short_description = 'Breaking'


# @admin.register(Author)
# class AuthorAdmin(admin.ModelAdmin):
#     list_display = ['name', 'email', 'is_verified', 'article_count']
#     search_fields = ['name', 'email']
#     list_filter = ['is_verified', 'created_at']
    
#     def article_count(self, obj):
#         return obj.article_set.count()
#     article_count.short_description = 'Articles'


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ['name', 'website', 'is_verified', 'is_active']
    list_filter = ['is_verified', 'is_active']
    search_fields = ['name', 'website']


# @admin.register(Comment)
# class CommentAdmin(admin.ModelAdmin):
#     list_display = ['user', 'article', 'content_preview', 'is_approved', 'created_at']
#     list_filter = ['is_approved', 'created_at']
#     search_fields = ['content', 'user__username']
    
#     def content_preview(self, obj):
#         return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
#     content_preview.short_description = 'Content Preview'


# admin.site.register(Tag)
# admin.site.register(Newsletter)
