from pathlib import Path

from django.conf import settings
from django.http import HttpResponse
from django.template.loader import select_template


ERROR_TITLES = {
    400: "Permintaan Tidak Valid",
    403: "Akses Ditolak",
    404: "Halaman Tidak Ditemukan",
    500: "Terjadi Gangguan Server",
}

ERROR_FALLBACKS = {
    4: ("errors/4xx.html", "Permintaan Tidak Dapat Diproses"),
    5: ("errors/5xx.html", "Terjadi Gangguan pada Server"),
}


def _asset_version():
    css_path = Path(settings.BASE_DIR) / "static" / "css" / "custom.css"
    try:
        return str(int(css_path.stat().st_mtime))
    except OSError:
        return "1"


def render_error_page(request, status_code):
    fallback_template, fallback_title = ERROR_FALLBACKS.get(
        status_code // 100,
        ("errors/5xx.html", "Terjadi Kesalahan"),
    )
    template = select_template([f"errors/{status_code}.html", fallback_template])
    response = HttpResponse(
        template.render(
            {
                "status_code": status_code,
                "error_title": ERROR_TITLES.get(status_code, fallback_title),
                "asset_version": _asset_version(),
            }
        ),
        status=status_code,
    )
    response._custom_error_page = True
    return response
