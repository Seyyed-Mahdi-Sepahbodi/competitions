from django.urls import resolve
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

import time
import logging


logger = logging.getLogger(__name__)


class FormAccessMiddleware(MiddlewareMixin):
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)

        logging.basicConfig(
            filename=settings.FORM_ACCESS_LOG_FILE,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def process_request(self, request):
        pass

    def process_response(self, request, response):
        pass

    @staticmethod
    def _calculate_completion_time(form_pk, request):
        pass

    @staticmethod
    def _get_client_ip(request):
        
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def _log_form_access(self, request, response, url_name, duration):
        
        log_data = {
            'url_name': url_name,
            'method': request.method,
            'status_code': response.status_code,
            'duration': f"{duration:.3f}s",
            'ip_address': self._get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown'),
            'user': request.user.username if request.user.is_authenticated else 'Anonymous',
            'path': request.path,
        }
        
        logger.info(f"Form Access: {log_data}")
