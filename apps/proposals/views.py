"""
Views for proposals app.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views import View
from django.core.exceptions import PermissionDenied

from apps.users.permissions import InfluencerRequiredMixin
from apps.campaigns.models import Campaign
from .selectors.proposal_selector import ProposalSelector
from .models import Proposal
from .forms import ProposalCreateForm
from .dto import ProposalCreateDTO
from .services.proposal_service import ProposalCreationService
from apps.common.exceptions import InvalidStateException, DuplicateActionException


class MyProposalsListView(InfluencerRequiredMixin, ListView):
    """
    Influencer-only view for listing their proposal applications.

    Permissions:
    - Login required
    - Influencer role only

    Features:
    - Automatic sorting by status (submitted -> selected -> rejected)
    - Within same status, sorted by most recent first
    """
    template_name = 'proposals/my_proposals_list.html'
    context_object_name = 'proposals'

    def get_queryset(self):
        """Retrieve proposals using selector pattern"""
        return ProposalSelector.get_influencer_proposals(
            influencer_id=self.request.user.id
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add empty state flag
        context['has_proposals'] = self.get_queryset().exists()

        # Optional: Add status counts for future use
        # context['status_counts'] = ProposalSelector.get_proposal_count_by_status(
        #     influencer_id=self.request.user.id
        # )

        return context


class ProposalCreateView(LoginRequiredMixin, View):
    """View for creating a new proposal"""

    template_name = 'proposals/proposal_create.html'
    login_url = '/accounts/login/'

    def dispatch(self, request, *args, **kwargs):
        """Check if user is an influencer before processing request"""
        if request.user.is_authenticated and request.user.role != 'influencer':
            raise PermissionDenied("체험단에 지원할 권한이 없습니다.")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, pk):
        """Display proposal creation form"""
        # Get campaign
        campaign = get_object_or_404(Campaign, pk=pk)

        # Check if already applied
        already_applied = Proposal.objects.filter(
            campaign_id=pk,
            influencer_id=request.user.id
        ).exists()

        if already_applied:
            messages.warning(request, "이미 지원한 체험단입니다.")
            return redirect('proposals:my_proposals')

        # Check if campaign is accepting applications
        if not campaign.can_apply():
            messages.error(request, "모집이 종료된 체험단입니다.")
            return redirect('campaigns:detail', pk=pk)

        # Create form
        form = ProposalCreateForm()

        context = {
            'campaign': campaign,
            'form': form,
        }
        return render(request, self.template_name, context)

    def post(self, request, pk):
        """Process proposal creation"""
        # Get campaign
        campaign = get_object_or_404(Campaign, pk=pk)

        # Validate form
        form = ProposalCreateForm(request.POST)

        if not form.is_valid():
            context = {
                'campaign': campaign,
                'form': form,
            }
            return render(request, self.template_name, context)

        # Create DTO
        dto = ProposalCreateDTO(
            campaign_id=pk,
            influencer_id=request.user.id,
            cover_letter=form.cleaned_data['cover_letter'],
            desired_visit_date=form.cleaned_data['desired_visit_date'],
        )

        # Execute service
        try:
            service = ProposalCreationService()
            service.execute(dto, user=request.user)

            messages.success(request, "지원이 성공적으로 완료되었습니다.")
            return redirect('proposals:my_proposals')

        except InvalidStateException as e:
            messages.error(request, str(e))
            return redirect('campaigns:detail', pk=pk)

        except DuplicateActionException as e:
            messages.warning(request, str(e))
            return redirect('proposals:my_proposals')
