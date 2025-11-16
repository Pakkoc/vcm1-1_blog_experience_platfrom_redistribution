"""
Views for user authentication and registration.
"""

from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth import login
from django.contrib import messages

from apps.common.exceptions import DuplicateActionException
from .forms import SignupForm
from .dto import SignupDTO
from .services.signup_service import SignupService


class SignupView(View):
    """
    View for user signup.

    Handles both GET (display form) and POST (process form) requests.
    """
    template_name = 'users/signup.html'

    def get(self, request):
        """Display signup form"""
        # Redirect authenticated users to home
        if request.user.is_authenticated:
            return redirect('/')

        form = SignupForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        """Process signup form submission"""
        form = SignupForm(request.POST)

        if not form.is_valid():
            return render(request, self.template_name, {'form': form})

        # Create DTO from cleaned data
        cleaned_data = form.cleaned_data
        dto = SignupDTO(
            email=cleaned_data['email'],
            password=cleaned_data['password'],
            name=cleaned_data['name'],
            contact=cleaned_data['contact'],
            role=cleaned_data['role'],
            company_name=cleaned_data.get('company_name'),
            business_registration_number=cleaned_data.get('business_registration_number'),
            birth_date=cleaned_data.get('birth_date'),
            sns_link=cleaned_data.get('sns_link')
        )

        # Execute signup service
        try:
            service = SignupService()
            user = service.execute(dto)

            # Auto login
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')

            messages.success(request, '회원가입이 완료되었습니다.')

            # Role-based redirection
            if user.role == 'advertiser':
                # TODO: Create campaign management page later
                return redirect('/')  # Home for now
            else:
                return redirect('/')  # Home page

        except DuplicateActionException as e:
            form.add_error(None, str(e))
            return render(request, self.template_name, {'form': form})
        except Exception as e:
            messages.error(request, '회원가입 처리 중 오류가 발생했습니다.')
            return render(request, self.template_name, {'form': form})
