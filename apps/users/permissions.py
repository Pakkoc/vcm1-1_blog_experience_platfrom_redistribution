"""
Permission decorators and mixins for role-based access control.
"""

from functools import wraps
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.conf import settings


def require_role(role):
    """
    Decorator to require a specific user role.

    Args:
        role: Required role ('advertiser' or 'influencer')

    Returns:
        Decorated function that checks user role
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Check if user is authenticated
            if not request.user.is_authenticated:
                return redirect(f"{settings.LOGIN_URL}?next={request.path}")

            # Check if user has required role
            if request.user.role != role:
                return HttpResponseForbidden('You do not have permission to access this page.')

            return view_func(request, *args, **kwargs)

        return wrapper
    return decorator


class AdvertiserRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    광고주 전용 View를 위한 Mixin

    Usage:
        class MyView(AdvertiserRequiredMixin, View):
            def get(self, request):
                ...
    """

    def test_func(self):
        """Test if user is an advertiser"""
        return (
            self.request.user.is_authenticated and
            self.request.user.role == 'advertiser'
        )

    def handle_no_permission(self):
        """Handle permission denied cases"""
        if not self.request.user.is_authenticated:
            # 비로그인 → 로그인 페이지로 리디렉션
            return super().handle_no_permission()
        else:
            # 로그인은 했지만 광고주가 아님 → 403
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("광고주만 접근할 수 있는 페이지입니다.")


class InfluencerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin to require influencer role for class-based views.

    Usage:
        class MyView(InfluencerRequiredMixin, View):
            def get(self, request):
                ...
    """

    def test_func(self):
        """Test if user is an influencer"""
        return self.request.user.is_authenticated and self.request.user.role == 'influencer'
