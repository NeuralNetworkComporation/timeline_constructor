from django.contrib import admin
from .models import Timeline, TimelineEvent, TimelineComment, TimelineLike, TimelineView


@admin.register(Timeline)
class TimelineAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'created_at', 'is_public', 'events_count')
    list_filter = ('is_public', 'created_at')
    search_fields = ('title', 'description')
    date_hierarchy = 'created_at'

    def events_count(self, obj):
        return obj.events.count()

    events_count.short_description = 'Событий'


@admin.register(TimelineEvent)
class TimelineEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'timeline', 'year', 'era', 'event_type')
    list_filter = ('era', 'event_type', 'year')
    search_fields = ('title', 'description')
    list_select_related = ('timeline',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('timeline')


@admin.register(TimelineComment)
class TimelineCommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'timeline', 'created_at', 'text_preview')
    list_filter = ('created_at',)
    search_fields = ('text', 'user__username', 'timeline__title')
    date_hierarchy = 'created_at'

    def text_preview(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text

    text_preview.short_description = 'Комментарий'


@admin.register(TimelineLike)
class TimelineLikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'timeline', 'created_at')
    list_filter = ('created_at',)
    date_hierarchy = 'created_at'
