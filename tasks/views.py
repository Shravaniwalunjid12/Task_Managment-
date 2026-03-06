from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Count, Q
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.core.paginator import Paginator
import json, csv

from .models import Task, Comment, AuditLog, Tag, UserProfile
from .forms import TaskForm, CommentForm, UserRegistrationForm, UserProfileForm, TagForm


def get_or_create_profile(user):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


def log_action(task, user, action, detail=''):
    AuditLog.objects.create(task=task, user=user, action=action, detail=detail)


def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')


@login_required
def dashboard(request):
    profile = get_or_create_profile(request.user)
    if profile.is_admin:
        return redirect('admin_dashboard')
    return redirect('user_dashboard')


@login_required
def admin_dashboard(request):
    profile = get_or_create_profile(request.user)
    if not profile.is_admin:
        return redirect('user_dashboard')

    tasks           = Task.objects.all().select_related('assigned_to', 'created_by')
    total           = tasks.count()
    pending         = tasks.filter(status='pending').count()
    in_progress     = tasks.filter(status='in_progress').count()
    completed       = tasks.filter(status='completed').count()
    on_hold         = tasks.filter(status='on_hold').count()
    overdue         = sum(1 for t in tasks if t.is_overdue)
    total_users     = User.objects.count()
    recent_tasks    = tasks.order_by('-created_at')[:6]
    recent_logs     = AuditLog.objects.all().select_related('user', 'task')[:8]
    completion_rate = round((completed / total * 100), 1) if total > 0 else 0

    user_summary = []
    for u in User.objects.all():
        ut = tasks.filter(assigned_to=u)
        if ut.count() > 0:
            user_summary.append({
                'user':      u,
                'total':     ut.count(),
                'completed': ut.filter(status='completed').count(),
                'pending':   ut.filter(status='pending').count(),
            })

    return render(request, 'tasks/admin_dashboard.html', {
        'profile': profile, 'total': total, 'pending': pending,
        'in_progress': in_progress, 'completed': completed,
        'on_hold': on_hold, 'overdue': overdue,
        'total_users': total_users, 'recent_tasks': recent_tasks,
        'recent_logs': recent_logs, 'completion_rate': completion_rate,
        'user_summary': user_summary,
    })


@login_required
def user_dashboard(request):
    profile      = get_or_create_profile(request.user)
    tasks        = Task.objects.filter(assigned_to=request.user).select_related('created_by')
    total        = tasks.count()
    pending      = tasks.filter(status='pending').count()
    in_progress  = tasks.filter(status='in_progress').count()
    completed    = tasks.filter(status='completed').count()
    overdue      = sum(1 for t in tasks if t.is_overdue)
    recent_tasks = tasks.order_by('-created_at')[:6]
    recent_logs  = AuditLog.objects.filter(task__in=tasks).select_related('user', 'task')[:8]
    completion_rate = round((completed / total * 100), 1) if total > 0 else 0
    upcoming = tasks.filter(
        deadline__gte=timezone.now(),
        status__in=['pending', 'in_progress']
    ).order_by('deadline')[:5]

    return render(request, 'tasks/user_dashboard.html', {
        'profile': profile, 'total': total, 'pending': pending,
        'in_progress': in_progress, 'completed': completed,
        'overdue': overdue, 'recent_tasks': recent_tasks,
        'recent_logs': recent_logs, 'completion_rate': completion_rate,
        'upcoming': upcoming,
    })


@login_required
def analytics(request):
    profile = get_or_create_profile(request.user)
    if not profile.is_admin:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    tasks = Task.objects.all()

    user_stats = []
    for u in User.objects.all():
        ut = tasks.filter(assigned_to=u)
        user_stats.append({
            'name':        u.get_full_name() or u.username,
            'total':       ut.count(),
            'completed':   ut.filter(status='completed').count(),
            'pending':     ut.filter(status='pending').count(),
            'in_progress': ut.filter(status='in_progress').count(),
        })

    status_data = {
        'pending':     tasks.filter(status='pending').count(),
        'in_progress': tasks.filter(status='in_progress').count(),
        'completed':   tasks.filter(status='completed').count(),
        'on_hold':     tasks.filter(status='on_hold').count(),
    }
    priority_data = {
        'low':      tasks.filter(priority='low').count(),
        'medium':   tasks.filter(priority='medium').count(),
        'high':     tasks.filter(priority='high').count(),
        'critical': tasks.filter(priority='critical').count(),
    }

    from django.db.models.functions import TruncMonth
    monthly = (
        tasks.filter(status='completed')
        .annotate(month=TruncMonth('updated_at'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )

    total = tasks.count()
    return render(request, 'tasks/analytics.html', {
        'profile':       profile,
        'user_stats':    json.dumps(user_stats),
        'status_data':   json.dumps(status_data),
        'priority_data': json.dumps(priority_data),
        'monthly':       json.dumps([{'month': m['month'].strftime('%b %Y'), 'count': m['count']} for m in monthly]),
        'total_tasks':   total,
        'overdue_count': sum(1 for t in tasks if t.is_overdue),
        'completion_rate': round(tasks.filter(status='completed').count() / total * 100, 1) if total else 0,
    })


@login_required
def task_list(request):
    profile = get_or_create_profile(request.user)

    if profile.is_admin:
        tasks = Task.objects.all().select_related('assigned_to', 'created_by').prefetch_related('tags')
    else:
        tasks = Task.objects.filter(assigned_to=request.user).select_related('created_by').prefetch_related('tags')

    status   = request.GET.get('status', '')
    priority = request.GET.get('priority', '')
    tag      = request.GET.get('tag', '')
    search   = request.GET.get('search', '')

    if status:   tasks = tasks.filter(status=status)
    if priority: tasks = tasks.filter(priority=priority)
    if tag:      tasks = tasks.filter(tags__name=tag)
    if search:   tasks = tasks.filter(Q(title__icontains=search) | Q(description__icontains=search))

    paginator  = Paginator(tasks, 10)
    tasks_page = paginator.get_page(request.GET.get('page'))

    return render(request, 'tasks/task_list.html', {
        'profile': profile, 'tasks': tasks_page,
        'all_tags': Tag.objects.all(),
        'current_status': status, 'current_priority': priority,
        'current_tag': tag, 'current_search': search,
    })


@login_required
def task_detail(request, pk):
    task    = get_object_or_404(Task, pk=pk)
    profile = get_or_create_profile(request.user)

    if not profile.is_admin and task.assigned_to != request.user:
        messages.error(request, "You don't have permission to view this task.")
        return redirect('task_list')

    if request.method == 'POST':
        form = CommentForm(request.POST, request.FILES)
        if form.is_valid():
            comment        = form.save(commit=False)
            comment.task   = task
            comment.author = request.user
            comment.save()
            log_action(task, request.user, 'commented', 'Added a comment')
            messages.success(request, 'Comment added.')
            return redirect('task_detail', pk=pk)
    else:
        form = CommentForm()

    return render(request, 'tasks/task_detail.html', {
        'profile': profile, 'task': task,
        'comments': task.comments.all().select_related('author'),
        'audit_logs': task.audit_logs.all().select_related('user'),
        'form': form,
    })


@login_required
def task_create(request):
    profile = get_or_create_profile(request.user)
    if not profile.is_admin:
        messages.error(request, 'Only admins can create tasks.')
        return redirect('task_list')

    if request.method == 'POST':
        form = TaskForm(request.POST, request.FILES)
        if form.is_valid():
            task            = form.save(commit=False)
            task.created_by = request.user
            task.save()
            form.save_m2m()
            log_action(task, request.user, 'created', f'Task created')
            if task.assigned_to:
                log_action(task, request.user, 'assigned', f'Assigned to {task.assigned_to.username}')
            messages.success(request, f'Task "{task.title}" created.')
            return redirect('task_list')
    else:
        form = TaskForm()

    return render(request, 'tasks/task_form.html', {'form': form, 'profile': profile})


@login_required
def task_edit(request, pk):
    task    = get_object_or_404(Task, pk=pk)
    profile = get_or_create_profile(request.user)
    if not profile.is_admin:
        messages.error(request, 'Only admins can edit tasks.')
        return redirect('task_list')

    old_status   = task.status
    old_priority = task.priority

    if request.method == 'POST':
        form = TaskForm(request.POST, request.FILES, instance=task)
        if form.is_valid():
            task = form.save()
            log_action(task, request.user, 'edited', 'Task updated')
            if task.status   != old_status:   log_action(task, request.user, 'status_changed',   f'{old_status} to {task.status}')
            if task.priority != old_priority: log_action(task, request.user, 'priority_changed', f'{old_priority} to {task.priority}')
            messages.success(request, 'Task updated.')
            return redirect('task_detail', pk=task.pk)
    else:
        form = TaskForm(instance=task)

    return render(request, 'tasks/task_form.html', {'form': form, 'profile': profile, 'task': task})


@login_required
def task_delete(request, pk):
    task    = get_object_or_404(Task, pk=pk)
    profile = get_or_create_profile(request.user)
    if not profile.is_admin:
        messages.error(request, 'Only admins can delete tasks.')
        return redirect('task_list')

    if request.method == 'POST':
        title = task.title
        task.delete()
        messages.success(request, f'Task "{title}" deleted.')
        return redirect('task_list')

    return render(request, 'tasks/task_confirm_delete.html', {'task': task, 'profile': profile})


@login_required
def update_status(request, pk):
    task    = get_object_or_404(Task, pk=pk)
    profile = get_or_create_profile(request.user)
    if not profile.is_admin and task.assigned_to != request.user:
        return JsonResponse({'error': 'Permission denied'}, status=403)

    if request.method == 'POST':
        data       = json.loads(request.body)
        old_status = task.status
        new_status = data.get('status')
        if new_status in dict(Task.STATUS_CHOICES):
            task.status = new_status
            if new_status == 'completed':
                task.completion_note = data.get('note', '')
            task.save()
            log_action(task, request.user, 'status_changed', f'{old_status} to {new_status}')
            return JsonResponse({'success': True})

    return JsonResponse({'error': 'Invalid'}, status=400)


@login_required
def user_list(request):
    profile = get_or_create_profile(request.user)
    if not profile.is_admin:
        return redirect('dashboard')

    user_data = []
    for u in User.objects.all():
        p  = get_or_create_profile(u)
        ut = u.assigned_tasks.all()
        user_data.append({
            'user': u, 'profile': p,
            'total':     ut.count(),
            'completed': ut.filter(status='completed').count(),
            'pending':   ut.filter(status='pending').count(),
        })

    return render(request, 'tasks/user_list.html', {'profile': profile, 'user_data': user_data})


@login_required
def user_create(request):
    profile = get_or_create_profile(request.user)
    if not profile.is_admin:
        return redirect('dashboard')

    if request.method == 'POST':
        form         = UserRegistrationForm(request.POST)
        profile_form = UserProfileForm(request.POST)
        if form.is_valid() and profile_form.is_valid():
            user     = form.save()
            up       = profile_form.save(commit=False)
            up.user  = user
            up.save()
            messages.success(request, f'User "{user.username}" created.')
            return redirect('user_list')
    else:
        form         = UserRegistrationForm()
        profile_form = UserProfileForm()

    return render(request, 'tasks/user_form.html', {
        'form': form, 'profile_form': profile_form, 'profile': profile
    })


@login_required
def reports(request):
    profile = get_or_create_profile(request.user)
    if not profile.is_admin:
        return redirect('dashboard')

    tasks = Task.objects.all().select_related('assigned_to', 'created_by').prefetch_related('tags')

    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="tasks_report.csv"'
        writer = csv.writer(response)
        writer.writerow(['ID', 'Title', 'Assigned To', 'Status', 'Priority', 'Deadline', 'Created At', 'Tags'])
        for t in tasks:
            writer.writerow([
                t.id, t.title,
                t.assigned_to.username if t.assigned_to else 'Unassigned',
                t.get_status_display(), t.get_priority_display(),
                t.deadline.strftime('%Y-%m-%d %H:%M') if t.deadline else '',
                t.created_at.strftime('%Y-%m-%d %H:%M'),
                ', '.join(tag.name for tag in t.tags.all())
            ])
        return response

    return render(request, 'tasks/reports.html', {
        'profile':     profile,
        'tasks':       tasks,
        'total':       tasks.count(),
        'completed':   tasks.filter(status='completed').count(),
        'pending':     tasks.filter(status='pending').count(),
        'in_progress': tasks.filter(status='in_progress').count(),
        'overdue':     sum(1 for t in tasks if t.is_overdue),
    })


@login_required
def tag_list(request):
    profile = get_or_create_profile(request.user)
    if not profile.is_admin:
        return redirect('dashboard')

    if request.method == 'POST':
        form = TagForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tag created.')
            return redirect('tag_list')
    else:
        form = TagForm()

    return render(request, 'tasks/tag_list.html', {
        'profile': profile,
        'tags': Tag.objects.annotate(task_count=Count('task')),
        'form': form,
    })


@login_required
def tag_delete(request, pk):
    profile = get_or_create_profile(request.user)
    if not profile.is_admin:
        return redirect('dashboard')
    get_object_or_404(Tag, pk=pk).delete()
    messages.success(request, 'Tag deleted.')
    return redirect('tag_list')


@login_required
def my_profile(request):
    profile = get_or_create_profile(request.user)
    tasks   = Task.objects.filter(assigned_to=request.user)
    return render(request, 'tasks/profile.html', {
        'profile':     profile,
        'tasks':       tasks,
        'completed':   tasks.filter(status='completed').count(),
        'pending':     tasks.filter(status='pending').count(),
        'in_progress': tasks.filter(status='in_progress').count(),
    })


@login_required
def settings_view(request):
    profile = get_or_create_profile(request.user)
    user    = request.user

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_profile':
            user.first_name    = request.POST.get('first_name', '').strip()
            user.last_name     = request.POST.get('last_name', '').strip()
            user.email         = request.POST.get('email', '').strip()
            user.save()
            profile.department = request.POST.get('department', '').strip()
            profile.phone      = request.POST.get('phone', '').strip()
            profile.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('settings')

        elif action == 'change_password':
            from django.contrib.auth import update_session_auth_hash
            old  = request.POST.get('old_password', '')
            new1 = request.POST.get('new_password1', '')
            new2 = request.POST.get('new_password2', '')
            if not user.check_password(old):
                messages.error(request, 'Current password is incorrect.')
            elif new1 != new2:
                messages.error(request, 'New passwords do not match.')
            elif len(new1) < 6:
                messages.error(request, 'Password must be at least 6 characters.')
            else:
                user.set_password(new1)
                user.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Password changed successfully.')
            return redirect('settings')

    task_stats = {
        'total':       Task.objects.filter(assigned_to=user).count(),
        'completed':   Task.objects.filter(assigned_to=user, status='completed').count(),
        'pending':     Task.objects.filter(assigned_to=user, status='pending').count(),
        'in_progress': Task.objects.filter(assigned_to=user, status='in_progress').count(),
    }

    return render(request, 'tasks/settings.html', {
        'profile':         profile,
        'task_stats':      task_stats,
        'all_users_count': User.objects.count() if profile.is_admin else None,
        'all_tasks_count': Task.objects.count() if profile.is_admin else None,
    })


# ─── LOGOUT — fixes HTTP 405 error ───────────────────────────────────────────
def logout_view(request):
    if request.method == 'POST':
        from django.contrib.auth import logout
        logout(request)
        return redirect('login')
    return redirect('dashboard')


# ─── REGISTER ─────────────────────────────────────────────────────────────────
def register(request):
    from django.contrib.auth import login as auth_login
    if request.user.is_authenticated:
        return redirect('dashboard')
    error_list = []
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user            = form.save(commit=False)
            user.first_name = request.POST.get('first_name', '').strip()
            user.last_name  = request.POST.get('last_name', '').strip()
            user.email      = request.POST.get('email', '').strip()
            user.save()
            role       = request.POST.get('role', 'user')
            department = request.POST.get('department', '').strip()
            phone      = request.POST.get('phone', '').strip()
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.role       = role
            profile.department = department
            profile.phone      = phone
            profile.save()
            if role == 'admin':
                user.is_staff = True
                user.save()
            auth_login(request, user)
            messages.success(request, f'Welcome {user.first_name or user.username}!')
            return redirect('dashboard')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    label = form.fields[field].label if field in form.fields else field
                    error_list.append(f"{label}: {error}")
    else:
        form = UserRegistrationForm()
    preselect_role = request.GET.get('role', 'user')
    return render(request, 'tasks/register.html', {
        'form': form, 'error_list': error_list, 'preselect_role': preselect_role,
    })
