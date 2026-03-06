from django.urls import path
from . import views

urlpatterns = [
    path('',                            views.home,             name='home'),
    path('dashboard/',                  views.dashboard,        name='dashboard'),
    path('dashboard/admin/',            views.admin_dashboard,  name='admin_dashboard'),
    path('dashboard/user/',             views.user_dashboard,   name='user_dashboard'),
    path('analytics/',                  views.analytics,        name='analytics'),
    path('tasks/',                      views.task_list,        name='task_list'),
    path('tasks/create/',               views.task_create,      name='task_create'),
    path('tasks/<int:pk>/',             views.task_detail,      name='task_detail'),
    path('tasks/<int:pk>/edit/',        views.task_edit,        name='task_edit'),
    path('tasks/<int:pk>/delete/',      views.task_delete,      name='task_delete'),
    path('tasks/<int:pk>/status/',      views.update_status,    name='update_status'),
    path('users/',                      views.user_list,        name='user_list'),
    path('users/create/',               views.user_create,      name='user_create'),
    path('tags/',                       views.tag_list,         name='tag_list'),
    path('tags/<int:pk>/delete/',       views.tag_delete,       name='tag_delete'),
    path('reports/',                    views.reports,          name='reports'),
    path('profile/',                    views.my_profile,       name='my_profile'),
    path('settings/',                   views.settings_view,    name='settings'),
    path('logout/',                     views.logout_view,      name='logout'),
    path('register/',                   views.register,         name='register'),
]
