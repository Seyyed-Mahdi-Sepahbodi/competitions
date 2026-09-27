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
        try:
            request._form_access_start_time = time.time()

            resolver_match = getattr(request, "resolver_match", None)
            if resolver_match is None:
                try:
                    resolver_match = resolve(request.path_info)
                except Exception:
                    resolver_match = None

            if (
                resolver_match
                and resolver_match.url_name == "form_detail"
                and request.method == "GET"
            ):
                if "form_start_times" not in request.session:
                    request.session["form_start_times"] = {}

                form_pk = resolver_match.kwargs.get("form_pk")
                # if not form_pk and resolver_match.kwargs:
                #     form_pk = next(iter(resolver_match.kwargs.values()))

                if form_pk is not None:
                    form_start_times = request.session.get("form_start_times", {})
                    form_start_times[str(form_pk)] = time.time()
                    request.session["form_start_times"] = form_start_times
                    request.session.modified = True
        except Exception as error:
            logger.error(f"Error in FormAccessMiddleware: {error}")

        return None


    def process_response(self, request, response):
        try:
            start_time = getattr(request, "_form_access_start_time", None)
            duration = (time.time() - start_time) if start_time else 0.0

            slow_threshold = getattr(settings, "FORM_REQUEST_SLOW_THRESHOLD")

            if slow_threshold is not None and duration > slow_threshold:
                logger.warning(
                    f"Slow request detected: {request.path} took {duration:.3f}s (threshold: {slow_threshold}s)"
                )

            resolver_match = getattr(request, "resolver_match", None)
            if resolver_match is None:
                try:
                    resolver_match = resolve(request.path_info)
                except Exception:
                    resolver_match = None

            url_name = resolver_match.url_name if resolver_match else None
            if (
                url_name == "form_submit"
                and request.method == "POST"
                and request.status_code == 302
            ):
                form_pk = None
                if resolver_match:
                    form_pk = resolver_match.kwargs.get("form_pk")
                    if not form_pk and resolver_match.kwargs:
                        form_pk = next(iter(resolver_match.kwargs.values()))

                self._calculate_completion_time(form_pk, request)

            self._log_form_access(request, response, url_name, duration)

        except Exception as error:
            logger.error(f"Error in FormAccessMiddleware: {error}")

    @staticmethod
    def _calculate_completion_time(form_pk, request):
        try:
            if not form_pk:
                resolver_match = getattr(request, "resolver_match", None)
                if resolver_match is None:
                    try:
                        resolver_match = resolve(request.path_info)
                    except Exception:
                        resolver_match = None
                
                if resolver_match:
                    form_pk = resolver_match.kwargs.get("form_pk")
                    if not form_pk and resolver_match.kwargs:
                        form_pk = next(iter(resolver_match.kwargs.values()))

            if not form_pk or not hasattr(request, "session"):
                return
            
            form_start_times = request.session.get("form_start_times", {})
            form_key = str(form_pk)

            if form_key in form_start_times:
                start_time = form_start_times[form_key]
                completion_time = time.time() - start_time

                request.session["form_completion_time"] = completion_time
                
                del form_start_times[form_key]
                request.session["form_start_times"] = form_start_times
                request.session.modified = True

        except Exception as error:
            logger.error(f"Error in FormAccessMiddleware: {error}")

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
