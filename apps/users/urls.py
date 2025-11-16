"""
URL configuration for users app.
"""

from django.urls import path
from .views import SignupView

app_name = 'users'

urlpatterns = [
    path('signup/', SignupView.as_view(), name='signup'),
]
