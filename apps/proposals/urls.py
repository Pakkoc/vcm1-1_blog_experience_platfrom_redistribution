"""
URL configuration for proposals app.
"""

from django.urls import path
from .views import MyProposalsListView, ProposalCreateView

app_name = 'proposals'

urlpatterns = [
    path('proposals/', MyProposalsListView.as_view(), name='my_proposals'),
    path('campaigns/<int:pk>/apply/', ProposalCreateView.as_view(), name='apply'),
]
