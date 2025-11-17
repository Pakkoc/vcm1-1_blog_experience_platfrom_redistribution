"""
Views for campaigns app.
"""

import logging
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views import View
from django.views.generic import DetailView, TemplateView, ListView
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

from apps.users.permissions import AdvertiserRequiredMixin
from .models import Campaign
from .selectors.campaign_selector import CampaignSelector
from .selectors.campaign_selectors import CampaignSelector as PublicCampaignSelector
from .services.campaign_creation import CampaignCreationService
from .services.campaign_management import CampaignCloseService
from .services.influencer_selection import InfluencerSelectionService
from .forms import CampaignCreateForm
from .dto import (
    CampaignCreateDTO,
    CampaignCloseDTO,
    InfluencerSelectionDTO
)
from apps.common.exceptions import (
    PermissionDeniedException,
    InvalidStateException,
    ServiceException
)

logger = logging.getLogger(__name__)


class CampaignManagementView(AdvertiserRequiredMixin, ListView):
    """광고주용 체험단 관리 페이지 - Phase 3"""
    template_name = 'campaigns/campaign_management.html'
    context_object_name = 'campaigns'

    def get_queryset(self):
        """현재 광고주의 체험단 목록 조회"""
        return CampaignSelector.get_campaigns_by_advertiser(
            advertiser_id=self.request.user.id
        )


class CampaignCreateView(AdvertiserRequiredMixin, View):
    """신규 체험단 등록 - Phase 3"""

    def post(self, request):
        """POST 요청 처리"""
        form = CampaignCreateForm(request.POST)

        if not form.is_valid():
            # 폼 오류를 메시지로 표시
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
            return redirect('campaigns:manage')

        # DTO 생성
        dto = CampaignCreateDTO(
            name=form.cleaned_data['name'],
            recruitment_start_date=form.cleaned_data['recruitment_start_date'],
            recruitment_end_date=form.cleaned_data['recruitment_end_date'],
            recruitment_count=form.cleaned_data['recruitment_count'],
            benefits=form.cleaned_data['benefits'],
            mission=form.cleaned_data['mission']
        )

        # 서비스 실행
        try:
            service = CampaignCreationService()
            campaign = service.execute(user=request.user, dto=dto)

            messages.success(request, f"'{campaign.name}' 체험단이 성공적으로 등록되었습니다.")
            return redirect('campaigns:manage')

        except Exception as e:
            messages.error(request, f"체험단 등록 중 오류가 발생했습니다: {str(e)}")
            return redirect('campaigns:manage')


class HomeView(TemplateView):
    """
    랜딩 페이지 (홈 페이지)

    - Hero Section: 플랫폼 소개 및 CTA
    - 모집 중인 체험단 목록: 최신순
    - 플랫폼 특징 및 이용 방법 안내
    """
    template_name = 'campaigns/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 모집 중인 체험단 목록
        context['campaigns'] = PublicCampaignSelector.get_recruiting_campaigns()

        return context


class CampaignDetailView(DetailView):
    """
    Campaign detail page view for all users (public).

    Accessible to all users (including anonymous users).
    For influencers, displays application eligibility status.
    """

    model = Campaign
    template_name = 'campaigns/campaign_detail.html'
    context_object_name = 'campaign'

    def get_object(self, queryset=None):
        """Retrieve campaign detail using Selector"""
        from django.http import Http404
        campaign_id = self.kwargs.get('pk')
        try:
            campaign = PublicCampaignSelector.get_campaign_detail(campaign_id)
            logger.info(
                f"Campaign detail viewed: campaign_id={campaign.id}, "
                f"user_id={self.request.user.id if self.request.user.is_authenticated else 'anonymous'}"
            )
            return campaign
        except Campaign.DoesNotExist:
            logger.warning(f"Campaign not found: campaign_id={campaign_id}")
            raise Http404("Campaign not found")

    def get_context_data(self, **kwargs):
        """Add application eligibility context"""
        context = super().get_context_data(**kwargs)
        campaign = self.object

        # Check if user can apply
        can_apply_info = PublicCampaignSelector.check_user_can_apply(
            campaign,
            self.request.user
        )

        context.update({
            'can_apply': can_apply_info['can_apply'],
            'cannot_apply_reason': can_apply_info['reason'],
            'already_applied': can_apply_info['already_applied'],
        })

        return context


class AdvertiserCampaignDetailView(AdvertiserRequiredMixin, View):
    """Advertiser campaign detail page"""

    template_name = 'campaigns/advertiser_campaign_detail.html'

    def get(self, request, pk):
        """
        Render campaign detail page for advertiser.

        Args:
            request: HTTP request
            pk: Campaign ID
        """
        # 1. Fetch campaign (with ownership verification)
        campaign = CampaignSelector.get_campaign_with_proposals_count(
            campaign_id=pk,
            advertiser_id=request.user.id
        )

        if not campaign:
            messages.error(request, "존재하지 않거나 접근할 수 없는 체험단입니다.")
            return redirect('campaigns:advertiser_list')

        # 2. Fetch proposals list
        proposals = CampaignSelector.get_proposals_by_campaign(
            campaign_id=pk
        )

        # 3. Determine action button visibility based on status
        context = {
            'campaign': campaign,
            'proposals': proposals,
            'can_close': campaign.status == 'recruiting',
            'can_select': (
                campaign.status == 'recruitment_ended' and
                campaign.submitted_proposals > 0
            ),
            'is_complete': campaign.status == 'selection_complete',
        }

        return render(request, self.template_name, context)


@login_required
@require_POST
def close_recruitment(request, pk):
    """
    Close campaign recruitment (Ajax request).

    Args:
        request: HTTP POST request
        pk: Campaign ID
    """
    try:
        # 1. Create DTO
        dto = CampaignCloseDTO(campaign_id=pk)

        # 2. Execute service
        service = CampaignCloseService()
        campaign = service.execute(user=request.user, dto=dto)

        # 3. Success response
        messages.success(request, "모집이 종료되었습니다.")
        return redirect('campaigns:advertiser_detail', pk=pk)

    except PermissionDeniedException as e:
        messages.error(request, str(e))
        return redirect('campaigns:advertiser_list')

    except InvalidStateException as e:
        messages.error(request, str(e))
        return redirect('campaigns:advertiser_detail', pk=pk)

    except Exception as e:
        messages.error(request, "일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요.")
        return redirect('campaigns:advertiser_detail', pk=pk)


@login_required
@require_POST
def select_influencers(request, pk):
    """
    Select influencers for campaign (Ajax request).

    Args:
        request: HTTP POST request
        pk: Campaign ID
    """
    try:
        # 1. Parse selected proposal IDs
        selected_ids = request.POST.getlist('selected_proposals[]', [])
        selected_ids = [int(id) for id in selected_ids if id.isdigit()]

        # 2. Create DTO
        dto = InfluencerSelectionDTO(
            campaign_id=pk,
            selected_proposal_ids=selected_ids
        )

        # 3. Execute service
        service = InfluencerSelectionService()
        result = service.execute(user=request.user, dto=dto)

        # 4. Success response
        messages.success(
            request,
            f"체험단 선정이 완료되었습니다. "
            f"선정: {result.selected_count}명, "
            f"반려: {result.rejected_count}명"
        )
        return redirect('campaigns:advertiser_detail', pk=pk)

    except PermissionDeniedException as e:
        messages.error(request, str(e))
        return redirect('campaigns:advertiser_list')

    except InvalidStateException as e:
        messages.error(request, str(e))
        return redirect('campaigns:advertiser_detail', pk=pk)

    except ServiceException as e:
        messages.error(request, str(e))
        return redirect('campaigns:advertiser_detail', pk=pk)

    except ValueError:
        messages.error(request, "잘못된 요청입니다.")
        return redirect('campaigns:advertiser_detail', pk=pk)

    except Exception as e:
        messages.error(request, "일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요.")
        return redirect('campaigns:advertiser_detail', pk=pk)
