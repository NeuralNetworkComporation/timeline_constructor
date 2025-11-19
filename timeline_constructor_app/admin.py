from django.contrib import admin
from .models import Timeline, TimelineEvent

@admin.register(Timeline)
class TimelineAdmin(admin.ModelAdmin):
    list_display = ['title', 'created_by', 'created_at', 'is_public']
    list_filter = ['is_public', 'created_at']
    search_fields = ['title', 'description']

@admin.register(TimelineEvent)
class TimelineEventAdmin(admin.ModelAdmin):
    list_display = ['title', 'timeline', 'year', 'era']
    list_filter = ['era', 'year']
    search_fields = ['title', 'description']