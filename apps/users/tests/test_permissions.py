"""
Test cases for permission decorators and mixins following TDD approach.
"""

import pytest
from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.views import View
from apps.users.models import User
from apps.users.permissions import require_role, AdvertiserRequiredMixin, InfluencerRequiredMixin


@pytest.mark.django_db
class TestRequireRoleDecorator:
    """Test cases for require_role decorator"""

    def setup_method(self):
        """Setup test data"""
        self.factory = RequestFactory()
        self.advertiser = User.objects.create_user(
            email='advertiser@test.com',
            password='testpass123',
            name='Advertiser',
            contact='010-1111-1111',
            role='advertiser'
        )
        self.influencer = User.objects.create_user(
            email='influencer@test.com',
            password='testpass123',
            name='Influencer',
            contact='010-2222-2222',
            role='influencer'
        )

    def test_advertiser_can_access_advertiser_only_view(self):
        """Advertiser should access advertiser-only view"""
        @require_role('advertiser')
        def test_view(request):
            return HttpResponse('Success')

        request = self.factory.get('/test/')
        request.user = self.advertiser

        response = test_view(request)
        assert response.status_code == 200

    def test_influencer_cannot_access_advertiser_only_view(self):
        """Influencer should not access advertiser-only view"""
        @require_role('advertiser')
        def test_view(request):
            return HttpResponse('Success')

        request = self.factory.get('/test/')
        request.user = self.influencer

        response = test_view(request)
        assert response.status_code == 403

    def test_anonymous_user_redirected_to_login(self):
        """Anonymous user should be redirected to login page"""
        @require_role('advertiser')
        def test_view(request):
            return HttpResponse('Success')

        request = self.factory.get('/test/')
        request.user = AnonymousUser()

        response = test_view(request)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url


@pytest.mark.django_db
class TestAdvertiserRequiredMixin:
    """Test cases for AdvertiserRequiredMixin"""

    def setup_method(self):
        """Setup test data"""
        self.factory = RequestFactory()
        self.advertiser = User.objects.create_user(
            email='advertiser@test.com',
            password='testpass123',
            name='Advertiser',
            contact='010-1111-1111',
            role='advertiser'
        )
        self.influencer = User.objects.create_user(
            email='influencer@test.com',
            password='testpass123',
            name='Influencer',
            contact='010-2222-2222',
            role='influencer'
        )

    def test_advertiser_passes_test(self):
        """Advertiser should pass test"""
        class TestView(AdvertiserRequiredMixin, View):
            def get(self, request):
                return HttpResponse('Success')

        view = TestView.as_view()
        request = self.factory.get('/test/')
        request.user = self.advertiser

        response = view(request)
        assert response.status_code == 200

    def test_influencer_fails_test(self):
        """Influencer should fail test and get 403"""
        from django.core.exceptions import PermissionDenied

        class TestView(AdvertiserRequiredMixin, View):
            def get(self, request):
                return HttpResponse('Success')

        view = TestView.as_view()
        request = self.factory.get('/test/')
        request.user = self.influencer

        with pytest.raises(PermissionDenied):
            view(request)

    def test_anonymous_user_redirected(self):
        """Anonymous user should be redirected to login"""
        class TestView(AdvertiserRequiredMixin, View):
            def get(self, request):
                return HttpResponse('Success')

        view = TestView.as_view()
        request = self.factory.get('/test/')
        request.user = AnonymousUser()

        response = view(request)
        assert response.status_code == 302


@pytest.mark.django_db
class TestInfluencerRequiredMixin:
    """Test cases for InfluencerRequiredMixin"""

    def setup_method(self):
        """Setup test data"""
        self.factory = RequestFactory()
        self.advertiser = User.objects.create_user(
            email='advertiser@test.com',
            password='testpass123',
            name='Advertiser',
            contact='010-1111-1111',
            role='advertiser'
        )
        self.influencer = User.objects.create_user(
            email='influencer@test.com',
            password='testpass123',
            name='Influencer',
            contact='010-2222-2222',
            role='influencer'
        )

    def test_influencer_passes_test(self):
        """Influencer should pass test"""
        class TestView(InfluencerRequiredMixin, View):
            def get(self, request):
                return HttpResponse('Success')

        view = TestView.as_view()
        request = self.factory.get('/test/')
        request.user = self.influencer

        response = view(request)
        assert response.status_code == 200

    def test_advertiser_fails_test(self):
        """Advertiser should fail test and get 403"""
        from django.core.exceptions import PermissionDenied

        class TestView(InfluencerRequiredMixin, View):
            def get(self, request):
                return HttpResponse('Success')

        view = TestView.as_view()
        request = self.factory.get('/test/')
        request.user = self.advertiser

        with pytest.raises(PermissionDenied):
            view(request)
