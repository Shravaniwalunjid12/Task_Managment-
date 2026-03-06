from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Task, Comment, UserProfile, Tag


class TaskForm(forms.ModelForm):
    deadline = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        input_formats=['%Y-%m-%dT%H:%M']
    )

    class Meta:
        model  = Task
        fields = ['title', 'description', 'assigned_to', 'status', 'priority', 'tags', 'deadline', 'attachment']
        widgets = {
            'title':       forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Task title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Task description'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'status':      forms.Select(attrs={'class': 'form-select'}),
            'priority':    forms.Select(attrs={'class': 'form-select'}),
            'tags':        forms.CheckboxSelectMultiple(),
            'attachment':  forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assigned_to'].queryset   = User.objects.all()
        self.fields['assigned_to'].empty_label = '-- Select User --'


class CommentForm(forms.ModelForm):
    class Meta:
        model  = Comment
        fields = ['content', 'attachment']
        widgets = {
            'content':    forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Add a comment...'}),
            'attachment': forms.FileInput(attrs={'class': 'form-control'}),
        }


class UserRegistrationForm(UserCreationForm):
    email      = forms.EmailField(required=True,  widget=forms.EmailInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(max_length=100,  widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name  = forms.CharField(max_length=100,  widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model  = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})


class UserProfileForm(forms.ModelForm):
    class Meta:
        model  = UserProfile
        fields = ['role', 'department', 'phone']
        widgets = {
            'role':       forms.Select(attrs={'class': 'form-select'}),
            'department': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Department'}),
            'phone':      forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone number'}),
        }


class TagForm(forms.ModelForm):
    class Meta:
        model  = Tag
        fields = ['name', 'color']
        widgets = {
            'name':  forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tag name'}),
            'color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
        }
