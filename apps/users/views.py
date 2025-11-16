"""
Views for user authentication and registration.
"""

from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth import login, logout, authenticate
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
                return redirect('campaigns:manage')
            else:
                return redirect('campaigns:home')

        except DuplicateActionException as e:
            form.add_error(None, str(e))
            return render(request, self.template_name, {'form': form})
        except Exception as e:
            messages.error(request, '회원가입 처리 중 오류가 발생했습니다.')
            return render(request, self.template_name, {'form': form})


class LoginView(View):
    """
    View for user login.
    """
    template_name = 'users/login.html'

    def get(self, request):
        """Display login form"""
        # Redirect authenticated users to home
        if request.user.is_authenticated:
            return redirect('/')

        return render(request, self.template_name)

    def post(self, request):
        """Process login form submission"""
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        # Validate input
        if not email or not password:
            messages.error(request, '이메일과 비밀번호를 모두 입력해주세요.')
            return render(request, self.template_name)

        # Authenticate user
        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f'{user.name}님, 환영합니다!')

            # Role-based redirection
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            elif user.role == 'advertiser':
                return redirect('campaigns:manage')
            else:
                return redirect('campaigns:home')
        else:
            messages.error(request, '이메일 또는 비밀번호가 올바르지 않습니다.')
            return render(request, self.template_name, {'email': email})


class LogoutView(View):
    """
    View for user logout.
    """
    def post(self, request):
        """Process logout"""
        logout(request)
        messages.success(request, '로그아웃되었습니다.')
        return redirect('campaigns:home')
