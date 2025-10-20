from datetime import timedelta
from django.utils import timezone

def get_time_ago(dt):
    """
    Calculate time ago from a datetime object.
    Returns a human-readable string like "5 minutes ago", "2 hours ago", etc.
    consistent across the application.
    """
    if not dt:
        return ""
    
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.utc)
    
    now = timezone.now()
    
    # Calculate difference
    diff = now - dt
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return "just now"
    elif seconds < 3600:  # Less than 1 hour
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif seconds < 86400:  # Less than 1 day
        hours = int(seconds / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif seconds < 604800:  # Less than 1 week
        days = int(seconds / 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"
    elif seconds < 2592000:  # Less than 30 days
        weeks = int(seconds / 604800)
        return f"{weeks} week{'s' if weeks != 1 else ''} ago"
    elif seconds < 31536000:  # Less than 1 year
        months = int(seconds / 2592000)
        return f"{months} month{'s' if months != 1 else ''} ago"
    else:
        years = int(seconds / 31536000)
        return f"{years} year{'s' if years != 1 else ''} ago"