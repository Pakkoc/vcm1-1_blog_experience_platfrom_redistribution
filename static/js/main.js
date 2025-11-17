// ===== Toast 알림 시스템 =====
const ToastManager = {
    toast: null,
    toastElement: null,

    init() {
        this.toastElement = document.getElementById('mainToast');
        if (this.toastElement) {
            this.toast = new bootstrap.Toast(this.toastElement, {
                autohide: true,
                delay: 3000
            });
        }
    },

    show(message, type = 'info') {
        if (!this.toast) return;

        const toastBody = this.toastElement.querySelector('.toast-body');
        const toastHeader = this.toastElement.querySelector('.toast-header');

        // 메시지 설정
        toastBody.textContent = message;

        // 타입에 따른 스타일 설정
        toastHeader.className = 'toast-header';
        switch (type) {
            case 'success':
                toastHeader.classList.add('bg-success', 'text-white');
                break;
            case 'error':
                toastHeader.classList.add('bg-danger', 'text-white');
                break;
            case 'warning':
                toastHeader.classList.add('bg-warning');
                break;
            default:
                toastHeader.classList.add('bg-info', 'text-white');
        }

        this.toast.show();
    },

    success(message) {
        this.show(message, 'success');
    },

    error(message) {
        this.show(message, 'error');
    },

    warning(message) {
        this.show(message, 'warning');
    },

    info(message) {
        this.show(message, 'info');
    }
};

// ===== 로딩 오버레이 =====
const LoadingOverlay = {
    overlay: null,

    init() {
        // 로딩 오버레이 생성
        if (!document.getElementById('loadingOverlay')) {
            const overlay = document.createElement('div');
            overlay.id = 'loadingOverlay';
            overlay.className = 'loading-overlay';
            overlay.innerHTML = '<div class="loading-spinner"></div>';
            document.body.appendChild(overlay);
            this.overlay = overlay;
        } else {
            this.overlay = document.getElementById('loadingOverlay');
        }
    },

    show() {
        if (this.overlay) {
            this.overlay.classList.add('show');
        }
    },

    hide() {
        if (this.overlay) {
            this.overlay.classList.remove('show');
        }
    }
};

// ===== 폼 제출 처리 개선 =====
const FormHandler = {
    init() {
        // 모든 폼에 제출 이벤트 리스너 추가 (필요시)
        document.querySelectorAll('form[data-loading="true"]').forEach(form => {
            form.addEventListener('submit', function () {
                LoadingOverlay.show();
            });
        });
    },

    async submitFormAjax(form, onSuccess, onError) {
        const formData = new FormData(form);
        const url = form.action;
        const method = form.method || 'POST';

        LoadingOverlay.show();

        try {
            const response = await fetch(url, {
                method: method,
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                },
            });

            LoadingOverlay.hide();

            if (response.ok) {
                const data = await response.json();
                if (onSuccess) onSuccess(data);
                return data;
            } else {
                const error = await response.json();
                if (onError) onError(error);
                ToastManager.error(error.message || '요청 처리 중 오류가 발생했습니다.');
            }
        } catch (error) {
            LoadingOverlay.hide();
            if (onError) onError(error);
            ToastManager.error('네트워크 오류가 발생했습니다.');
        }
    }
};

// ===== AJAX 유틸리티 함수 =====
async function fetchJSON(url, options = {}) {
    LoadingOverlay.show();

    try {
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
                ...options.headers,
            },
        });

        LoadingOverlay.hide();

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        LoadingOverlay.hide();
        ToastManager.error('요청 처리 중 오류가 발생했습니다.');
        throw error;
    }
}

// ===== CSRF 토큰 가져오기 =====
function getCsrfToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
}

// ===== 스무스 스크롤 =====
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        const href = this.getAttribute('href');
        if (href === '#' || !href) return;

        const target = document.querySelector(href);
        if (target) {
            e.preventDefault();
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// ===== 카드 애니메이션 =====
function animateCards() {
    const cards = document.querySelectorAll('.card');
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
            }
        });
    }, {
        threshold: 0.1
    });

    cards.forEach(card => observer.observe(card));
}

// ===== 초기화 =====
document.addEventListener('DOMContentLoaded', function () {
    ToastManager.init();
    LoadingOverlay.init();
    FormHandler.init();
    animateCards();

    // Django messages를 Toast로 표시
    const djangoMessages = document.querySelectorAll('.alert');
    djangoMessages.forEach(msg => {
        const type = msg.classList.contains('alert-success') ? 'success' :
            msg.classList.contains('alert-danger') ? 'error' :
                msg.classList.contains('alert-warning') ? 'warning' : 'info';

        ToastManager.show(msg.textContent.trim(), type);
    });
});

// ===== 전역으로 노출 =====
window.ToastManager = ToastManager;
window.LoadingOverlay = LoadingOverlay;
window.FormHandler = FormHandler;
window.fetchJSON = fetchJSON;
window.getCsrfToken = getCsrfToken;
