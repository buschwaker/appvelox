from django.contrib import admin

from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """Управление жанрами админом."""
    list_display = (
        'author',
        'title',
        'is_done',
        'is_failed',
        'deadline_on',
        'done_at',
    )
    search_fields = (
        'title',
    )
