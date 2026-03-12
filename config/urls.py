"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

import re

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.views import serve as staticfiles_serve
from django.urls import include, path, re_path

urlpatterns = [
    path("", include("apps.accounts.urls")),
    path("", include("apps.marketing.urls")),
    path("", include("apps.core.urls")),
    path("", include("apps.analytics.urls")),
    path("", include("apps.dashboard.urls")),
    path("", include("apps.questions.urls")),
    path("", include("apps.exams.urls")),
    path("", include("apps.users.urls")),
    path("", include("apps.subjects.urls")),
    path("", include("apps.monitoring.urls")),
    path("", include("apps.results.urls")),
    path("", include("apps.attempts.urls")),
    path("", include("apps.notifications.urls")),
    path("admin/", admin.site.urls),
]

handler403 = "apps.core.views.permission_denied_view"
handler400 = "apps.core.views.bad_request_view"
handler404 = "apps.core.views.not_found_view"
handler500 = "apps.core.views.server_error_view"

if settings.DEBUG or getattr(settings, "SERVE_STATIC_WITH_DJANGO", False):
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += [
        re_path(
            rf"^{re.escape(settings.STATIC_URL.lstrip('/'))}(?P<path>.*)$",
            staticfiles_serve,
            {"insecure": True},
        )
    ]
