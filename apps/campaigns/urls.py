"""
Campaign URL configuration.
"""

from django.urls import path
from . import views

app_name = 'campaigns'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('<int:pk>/', views.CampaignDetailView.as_view(), name='detail'),

    # Phase 3 & 4: Campaign Management
    path('manage/campaigns/', views.CampaignManagementView.as_view(), name='manage'),
    path('manage/campaigns/create/', views.CampaignCreateView.as_view(), name='create'),

    # Advertiser campaign detail management
    path(
        'manage/<int:pk>/',
        views.AdvertiserCampaignDetailView.as_view(),
        name='advertiser_detail'
    ),
    path(
        'manage/<int:pk>/close/',
        views.close_recruitment,
        name='close_recruitment'
    ),
    path(
        'manage/<int:pk>/select/',
        views.select_influencers,
        name='select_influencers'
    ),
]
