from django.contrib import messages
from django.contrib.auth import logout
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse

from .session_control import validate_student_request_session


class StudentSingleSessionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        result = validate_student_request_session(request)
        if not result.valid:
            user = getattr(request, "user", None)
            if getattr(user, "is_authenticated", False):
                logout(request)

            if self._prefers_json(request):
                return JsonResponse(
                    {
                        "success": False,
                        "message": result.message,
                        "code": result.reason,
                        "redirect_url": reverse("login"),
                    },
                    status=401,
                )

            messages.warning(request, result.message)
            return redirect("login")

        return self.get_response(request)

    def _prefers_json(self, request):
        accept = request.headers.get("Accept", "")
        requested_with = request.headers.get("X-Requested-With", "")
        content_type = request.content_type or ""
        return (
            request.path.startswith("/api/")
            or "application/json" in accept
            or "application/json" in content_type
            or requested_with == "XMLHttpRequest"
        )
