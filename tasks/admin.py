from django.contrib import admin
from .models import Task, Comment, AuditLog, Tag, UserProfile


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display  = ['title', 'assigned_to', 'status', 'priority', 'deadline', 'created_at']
    list_filter   = ['status', 'priority', 'tags']
    search_fields = ['title', 'description']
    filter_horizontal = ['tags']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['task', 'author', 'created_at']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display   = ['task', 'user', 'action', 'timestamp']
    list_filter    = ['action']
    readonly_fields = ['task', 'user', 'action', 'detail', 'timestamp']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'color']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'department']
    list_filter  = ['role']
