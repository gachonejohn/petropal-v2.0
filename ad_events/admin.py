from django.contrib import admin
from .models import AdEvent, Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = [
        'name', 
        'slug', 
        'is_active', 
        'order',
        'created_at'
    ]
    
    list_filter = [
        'is_active', 
        'created_at'
    ]
    
    search_fields = [
        'name', 
        'description'
    ]
    
    list_editable = [
        'is_active', 
        'order'
    ]
    
    prepopulated_fields = {
        'slug': ('name',)
    }
    
    readonly_fields = [
        'created_at', 
        'updated_at'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description')
        }),
        ('Display Settings', {
            'fields': ('order',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ['order', 'name']
    
    actions = ['mark_as_active', 'mark_as_inactive']
    
    def mark_as_active(self, request, queryset):
        queryset.update(is_active=True)
    mark_as_active.short_description = "Mark selected categories as active"
    
    def mark_as_inactive(self, request, queryset):
        queryset.update(is_active=False)
    mark_as_inactive.short_description = "Mark selected categories as inactive"


@admin.register(AdEvent)
class AdEventAdmin(admin.ModelAdmin):
    list_display = [
        'title', 
        'type', 
        'category', 
        'location', 
        'status', 
        'is_featured',
        'start_date', 
        'end_date',
        'created_at'
    ]
    
    list_filter = [
        'type', 
        'category', 
        'status', 
        'is_featured',
        'location',
        'created_at',
        'start_date',
        'end_date'
    ]
    
    search_fields = [
        'title', 
        'description', 
        'location'
    ]
    
    list_editable = [
        'status', 
        'is_featured'
    ]
    
    readonly_fields = [
        'created_at', 
        'updated_at',
        'is_active',
        'is_upcoming',
        'is_expired'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'type', 'category', 'description', 'link')
        }),
        ('Media', {
            'fields': ('banner_image',)
        }),
        ('Location & Dates', {
            'fields': ('location', 'start_date', 'end_date')
        }),
        ('Status & Features', {
            'fields': ('status', 'is_featured')
        }),
        ('Computed Properties', {
            'fields': ('is_active', 'is_upcoming', 'is_expired'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category')
    
    actions = ['mark_as_active', 'mark_as_suspended', 'mark_as_featured', 'mark_as_not_featured']
    
    def mark_as_active(self, request, queryset):
        queryset.update(status='active')
    mark_as_active.short_description = "Mark selected items as active"
    
    def mark_as_suspended(self, request, queryset):
        queryset.update(status='suspended')
    mark_as_suspended.short_description = "Mark selected items as suspended"
    
    def mark_as_featured(self, request, queryset):
        queryset.update(is_featured=True)
    mark_as_featured.short_description = "Mark selected items as featured"
    
    def mark_as_not_featured(self, request, queryset):
        queryset.update(is_featured=False)
    mark_as_not_featured.short_description = "Remove featured status from selected items"
    
    # Custom filter to show only items from active categories
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "category":
            kwargs["queryset"] = Category.objects.filter(is_active=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)