from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect

from core.models import UserProfile


def get_or_create_user_profile(user):
    if not user or not getattr(user, 'is_authenticated', False):
        return None
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


def get_user_role(user):
    profile = get_or_create_user_profile(user)
    return profile.role if profile else None


def role_required(*allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')

            user_role = get_user_role(request.user)
            if user_role not in allowed_roles:
                messages.error(request, 'You do not have permission to access this page.')
                return redirect('dashboard')

            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator
