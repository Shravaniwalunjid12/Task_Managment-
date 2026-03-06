#!/usr/bin/env python
"""
Run this ONCE after migrate to create demo users and tasks.
Usage:  python setup_demo.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'task_management.settings')
django.setup()

from django.contrib.auth.models import User
from tasks.models import Task, Tag, UserProfile, AuditLog
from django.utils import timezone
from datetime import timedelta


def run():
    print("Setting up TaskFlow demo data...")

    tags_data = [
        ('Backend',       '#6366f1'),
        ('Frontend',      '#3b82f6'),
        ('Design',        '#ec4899'),
        ('Bug Fix',       '#ef4444'),
        ('Research',      '#10b981'),
        ('Review',        '#f59e0b'),
        ('Documentation', '#8b5cf6'),
    ]
    created_tags = {}
    for name, color in tags_data:
        tag, _ = Tag.objects.get_or_create(name=name, defaults={'color': color})
        created_tags[name] = tag
    print(f"  Created {len(tags_data)} tags")

    if not User.objects.filter(username='admin').exists():
        admin = User.objects.create_superuser('admin', 'admin@taskflow.com', 'admin123')
        admin.first_name = 'Admin'
        admin.last_name  = 'User'
        admin.save()
        p = UserProfile.objects.get_or_create(user=admin)[0]
        p.role = 'admin'; p.department = 'Management'; p.save()
        print("  Created admin  (username: admin / password: admin123)")
    else:
        admin = User.objects.get(username='admin')
        print("  Admin already exists")

    test_users = [
        ('john_doe',  'John', 'Doe',   'john@taskflow.com',  'Engineering'),
        ('jane_smith','Jane', 'Smith', 'jane@taskflow.com',  'Design'),
        ('bob_jones', 'Bob',  'Jones', 'bob@taskflow.com',   'QA'),
        ('testuser',  'Test', 'User',  'test@taskflow.com',  'Development'),
    ]
    users = {}
    for username, fn, ln, email, dept in test_users:
        if not User.objects.filter(username=username).exists():
            u = User.objects.create_user(username, email, 'user123')
            u.first_name = fn; u.last_name = ln; u.save()
            p = UserProfile.objects.get_or_create(user=u)[0]
            p.role = 'user'; p.department = dept; p.save()
        users[username] = User.objects.get(username=username)
    print(f"  Created {len(test_users)} team users (password: user123)")

    now = timezone.now()
    tasks_data = [
        {
            'title': 'Design new dashboard UI mockups',
            'description': 'Create high-fidelity mockups for the admin dashboard with mobile responsive layouts.',
            'assigned_to': users['jane_smith'], 'status': 'in_progress', 'priority': 'high',
            'deadline': now + timedelta(days=5), 'tags': ['Design', 'Frontend'],
        },
        {
            'title': 'Fix login page authentication bug',
            'description': 'Users are occasionally getting logged out unexpectedly. Investigate session handling.',
            'assigned_to': users['john_doe'], 'status': 'in_progress', 'priority': 'critical',
            'deadline': now + timedelta(days=1), 'tags': ['Bug Fix', 'Backend'],
        },
        {
            'title': 'Write API documentation',
            'description': 'Document all REST API endpoints including request/response schemas and examples.',
            'assigned_to': users['testuser'], 'status': 'pending', 'priority': 'medium',
            'deadline': now + timedelta(days=14), 'tags': ['Documentation', 'Backend'],
        },
        {
            'title': 'Implement file upload feature',
            'description': 'Add ability for users to upload files to tasks. Support PDF, DOCX, PNG up to 10MB.',
            'assigned_to': users['john_doe'], 'status': 'completed', 'priority': 'high',
            'deadline': now - timedelta(days=2), 'tags': ['Backend', 'Frontend'],
        },
        {
            'title': 'Database performance optimization',
            'description': 'Profile and optimize slow queries. Add indexes. Target: reduce page load by 40%.',
            'assigned_to': users['bob_jones'], 'status': 'on_hold', 'priority': 'low',
            'deadline': now + timedelta(days=30), 'tags': ['Backend'],
        },
        {
            'title': 'Deploy to production server',
            'description': 'Deploy release v2.1.0 to production. Run migrations and verify deployment.',
            'assigned_to': users['john_doe'], 'status': 'pending', 'priority': 'critical',
            'deadline': now - timedelta(days=1), 'tags': ['Backend'],
        },
    ]

    for t in tasks_data:
        if not Task.objects.filter(title=t['title']).exists():
            task = Task.objects.create(
                title=t['title'], description=t['description'],
                assigned_to=t['assigned_to'], created_by=admin,
                status=t['status'], priority=t['priority'], deadline=t['deadline'],
            )
            for tag_name in t['tags']:
                if tag_name in created_tags:
                    task.tags.add(created_tags[tag_name])
            AuditLog.objects.create(task=task, user=admin, action='created', detail='Task created')
            AuditLog.objects.create(task=task, user=admin, action='assigned', detail=f'Assigned to {task.assigned_to.username}')

    print(f"  Created {len(tasks_data)} sample tasks")
    print()
    print("=" * 45)
    print("  Setup complete!")
    print("=" * 45)
    print()
    print("  URL     :  http://127.0.0.1:8000/")
    print("  Admin   :  admin      / admin123")
    print("  User    :  testuser   / user123")
    print()


if __name__ == '__main__':
    run()
