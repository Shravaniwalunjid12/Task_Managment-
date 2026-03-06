from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Tag(models.Model):
    name  = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=7, default='#3498db')

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Task(models.Model):
    PRIORITY_CHOICES = [
        ('low',      'Low'),
        ('medium',   'Medium'),
        ('high',     'High'),
        ('critical', 'Critical'),
    ]
    STATUS_CHOICES = [
        ('pending',     'Pending'),
        ('in_progress', 'In Progress'),
        ('completed',   'Completed'),
        ('on_hold',     'On Hold'),
    ]

    title          = models.CharField(max_length=200)
    description    = models.TextField()
    assigned_to    = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks')
    created_by     = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tasks')
    status         = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority       = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    tags           = models.ManyToManyField(Tag, blank=True)
    deadline       = models.DateTimeField(null=True, blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)
    attachment     = models.FileField(upload_to='task_attachments/', null=True, blank=True)
    completion_note = models.TextField(blank=True)

    def __str__(self):
        return self.title

    @property
    def is_overdue(self):
        if self.deadline and self.status != 'completed':
            return timezone.now() > self.deadline
        return False

    class Meta:
        ordering = ['-created_at']


class Comment(models.Model):
    task       = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    author     = models.ForeignKey(User, on_delete=models.CASCADE)
    content    = models.TextField()
    attachment = models.FileField(upload_to='comment_attachments/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Comment by {self.author.username} on {self.task.title}"

    class Meta:
        ordering = ['created_at']


class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('created',         'Task Created'),
        ('assigned',        'Task Assigned'),
        ('status_changed',  'Status Changed'),
        ('priority_changed','Priority Changed'),
        ('commented',       'Comment Added'),
        ('file_uploaded',   'File Uploaded'),
        ('edited',          'Task Edited'),
        ('deleted',         'Task Deleted'),
    ]

    task      = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='audit_logs')
    user      = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action    = models.CharField(max_length=30, choices=ACTION_CHOICES)
    detail    = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action} on {self.task.title} by {self.user}"

    class Meta:
        ordering = ['-timestamp']


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('user',  'User'),
    ]
    user       = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role       = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    department = models.CharField(max_length=100, blank=True)
    phone      = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.user.username} ({self.role})"

    @property
    def is_admin(self):
        return self.role == 'admin'
