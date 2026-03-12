import logging

from django.conf import settings
from django.core.exceptions import BadRequest, PermissionDenied, SuspiciousOperation
from django.http import Http404

from apps.core.utils import render_error_page


logger = logging.getLogger(__name__)


class ErrorPageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not getattr(settings, "CUSTOM_ERROR_PAGES", True):
            return self.get_response(request)

        try:
            response = self.get_response(request)
        except Http404:
            return render_error_page(request, 404)
        except PermissionDenied:
            return render_error_page(request, 403)
        except (BadRequest, SuspiciousOperation):
            return render_error_page(request, 400)
        except Exception:
            logger.exception("Unhandled application error.")
            return render_error_page(request, 500)

        if self._should_replace_with_error_page(request, response):
            return render_error_page(request, response.status_code)

        return response

    def _should_replace_with_error_page(self, request, response):
        if getattr(response, "_custom_error_page", False):
            return False

        if getattr(response, "streaming", False):
            return False

        status_code = getattr(response, "status_code", 200)
        if status_code < 400 or status_code >= 600:
            return False

        content_type = response.get("Content-Type", "")
        if "application/json" in content_type:
            return False

        if self._request_prefers_json(request):
            return False

        return True

    @staticmethod
    def _request_prefers_json(request):
        accept = request.headers.get("Accept", "")
        requested_with = request.headers.get("X-Requested-With", "")

        if request.path.startswith("/api/"):
            return True

        if "application/json" in accept and "text/html" not in accept:
            return True

        if requested_with == "XMLHttpRequest" and "text/html" not in accept:
            return True

        return False
