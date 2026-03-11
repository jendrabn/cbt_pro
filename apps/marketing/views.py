from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.templatetags.static import static
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import FormView, TemplateView

from apps.accounts.views import get_role_redirect_url
from apps.core.services import get_branding_settings

from .content import (
    FAQ_PREVIEW,
    FEATURE_PAGE_ITEMS,
    HOME_PROOF_POINTS,
    IMPLEMENTATION_STEPS,
    LANDING_FEATURE_CARDS,
    LANDING_STATS,
    PRICING_COMPARISON_ROWS,
    PRICING_FAQ,
    PRICING_PLAN,
)
from .forms import MarketingContactForm


DEFAULT_WHATSAPP_NUMBER = "628xxxxxxxxxx"
DEFAULT_CONTACT_EMAIL = "halo@cbtpro.web.id"
DEFAULT_OPERATING_HOURS = "Senin - Sabtu, 08.00 - 17.00 WIB"
DEFAULT_THEME_COLOR = "#16335B"
PRODUCT_NAME = "CBT Pro"


def _json_ld(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def _marketing_asset_version() -> str:
    css_path = Path(settings.BASE_DIR) / "static" / "css" / "marketing.css"
    try:
        return str(int(css_path.stat().st_mtime))
    except OSError:
        return "1"


def _normalized_whatsapp_number() -> str:
    raw_value = getattr(settings, "WHATSAPP_NUMBER", DEFAULT_WHATSAPP_NUMBER) or DEFAULT_WHATSAPP_NUMBER
    digits = re.sub(r"\D", "", raw_value)
    return digits or DEFAULT_WHATSAPP_NUMBER


def _site_root_url() -> str:
    return getattr(settings, "MARKETING_SITE_URL", "https://cbtpro.web.id").rstrip("/")


def _absolute_public_url(path: str) -> str:
    base_url = f"{_site_root_url()}/"
    return urljoin(base_url, path.lstrip("/"))


def _dashboard_cta(request) -> dict[str, str]:
    dashboard_url = reverse("login")
    dashboard_label = "Login"
    dashboard_icon = "ri-login-box-line"

    if request.user.is_authenticated:
        dashboard_url = get_role_redirect_url(request.user)
        dashboard_label = {
            "admin": "Dashboard Admin",
            "teacher": "Dashboard Guru",
            "student": "Dashboard Siswa",
        }.get(getattr(request.user, "role", ""), "Dashboard")
        dashboard_icon = "ri-dashboard-line"
    elif settings.DEMO_MODE:
        dashboard_label = "Demo"
        dashboard_icon = "ri-play-circle-line"

    return {
        "dashboard_url": dashboard_url,
        "dashboard_label": dashboard_label,
        "dashboard_icon": dashboard_icon,
    }


class MarketingPageMixin:
    template_name = ""
    meta_title = PRODUCT_NAME
    meta_description = ""
    meta_keywords: list[str] = []
    page_name = PRODUCT_NAME
    page_schema_type = "WebPage"
    breadcrumb_label = ""
    body_class = ""
    show_marketing_chrome = True
    is_indexable = True

    def dispatch(self, request, *args, **kwargs):
        self.branding = get_branding_settings()
        if not self.branding.get("landing_page_enabled", True):
            return redirect("login")
        return super().dispatch(request, *args, **kwargs)

    def get_meta_title(self) -> str:
        return self.meta_title

    def get_meta_description(self) -> str:
        return self.meta_description

    def get_meta_keywords(self) -> list[str]:
        return self.meta_keywords

    def get_canonical_url(self) -> str:
        return _absolute_public_url(self.request.path)

    def get_site_root(self) -> str:
        return _site_root_url()

    def get_logo_url(self) -> str:
        logo_url = self.branding.get("institution_logo_url") or static("images/logo-dark.png")
        return _absolute_public_url(logo_url)

    def get_og_image_url(self) -> str:
        return _absolute_public_url(static("images/og-image.png"))

    def get_breadcrumbs(self) -> list[dict[str, str]]:
        if not self.show_marketing_chrome:
            return []
        if not self.breadcrumb_label:
            return []
        return [
            {"label": "Beranda", "url": reverse("landing")},
            {"label": self.breadcrumb_label, "url": self.request.path},
        ]

    def get_page_schema(self) -> dict:
        return {
            "@context": "https://schema.org",
            "@type": self.page_schema_type,
            "name": self.page_name,
            "description": self.get_meta_description(),
            "url": self.get_canonical_url(),
            "inLanguage": "id-ID",
            "keywords": ", ".join(self.get_meta_keywords()),
            "isPartOf": {
                "@type": "WebSite",
                "name": PRODUCT_NAME,
                "url": self.get_site_root(),
            },
        }

    def get_extra_schema(self) -> list[dict]:
        return []

    def get_robots_meta_content(self) -> str:
        if self.is_indexable:
            return "index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1"
        return "noindex, nofollow, noarchive, nosnippet"

    def get_contact_email(self) -> str:
        return str(self.branding.get("institution_email") or "").strip() or DEFAULT_CONTACT_EMAIL

    def get_contact_phone(self) -> str:
        return _normalized_whatsapp_number()

    def get_common_context(self) -> dict[str, object]:
        whatsapp_number = self.get_contact_phone()
        phone_display = f"+{whatsapp_number}" if whatsapp_number.startswith("62") else whatsapp_number
        breadcrumbs = self.get_breadcrumbs()
        extra_schema = list(self.get_extra_schema())

        if breadcrumbs:
            extra_schema.append(
                {
                    "@context": "https://schema.org",
                    "@type": "BreadcrumbList",
                    "itemListElement": [
                        {
                            "@type": "ListItem",
                            "position": index,
                            "name": crumb["label"],
                            "item": _absolute_public_url(crumb["url"]),
                        }
                        for index, crumb in enumerate(breadcrumbs, start=1)
                    ],
                }
            )

        organization_schema = {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": PRODUCT_NAME,
            "url": self.get_site_root(),
            "logo": self.get_logo_url(),
            "email": self.get_contact_email(),
            "telephone": f"+{whatsapp_number}",
            "contactPoint": [
                {
                    "@type": "ContactPoint",
                    "contactType": "sales",
                    "telephone": f"+{whatsapp_number}",
                    "email": self.get_contact_email(),
                    "areaServed": "ID",
                    "availableLanguage": ["id", "en"],
                }
            ],
        }
        website_schema = {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "name": PRODUCT_NAME,
            "url": self.get_site_root(),
            "inLanguage": "id-ID",
        }

        return {
            "product_name": PRODUCT_NAME,
            "current_year": timezone.now().year,
            "marketing_asset_version": _marketing_asset_version(),
            "whatsapp_number": whatsapp_number,
            "whatsapp_display": phone_display,
            "whatsapp_url": f"https://wa.me/{whatsapp_number}",
            "contact_email": self.get_contact_email(),
            "operating_hours": DEFAULT_OPERATING_HOURS,
            "marketing_logo_url": self.branding.get("institution_logo_url") or static("images/logo-dark.png"),
            "theme_color": DEFAULT_THEME_COLOR,
            "canonical_url": self.get_canonical_url(),
            "og_image_url": self.get_og_image_url(),
            "meta_title": self.get_meta_title(),
            "meta_description": self.get_meta_description(),
            "meta_keywords": ", ".join(self.get_meta_keywords()),
            "robots_meta_content": self.get_robots_meta_content(),
            "body_class": self.body_class,
            "show_marketing_chrome": self.show_marketing_chrome,
            "breadcrumbs": breadcrumbs,
            "organization_schema_json": _json_ld(organization_schema),
            "website_schema_json": _json_ld(website_schema),
            "page_schema_json": _json_ld(self.get_page_schema()),
            "extra_schema_json_list": [_json_ld(item) for item in extra_schema],
            **_dashboard_cta(self.request),
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_common_context())
        return context

    def render_to_response(self, context, **response_kwargs):
        response = super().render_to_response(context, **response_kwargs)
        response["X-Robots-Tag"] = self.get_robots_meta_content()
        return response


class LandingPageView(MarketingPageMixin, TemplateView):
    template_name = "marketing/landing.html"
    meta_title = "CBT Pro | Aplikasi CBT Sekolah untuk Ujian Online yang Siap Pakai"
    meta_description = (
        "CBT Pro adalah aplikasi CBT sekolah untuk ujian online, try out, dan asesmen digital "
        "dengan setup cepat, randomisasi soal, monitoring, dan analitik hasil."
    )
    meta_keywords = [
        "aplikasi CBT sekolah",
        "ujian online sekolah",
        "software CBT Indonesia",
        "CBT Pro",
    ]
    page_name = "CBT Pro landing page"
    body_class = "page-landing"

    def get_extra_schema(self) -> list[dict]:
        return [
            {
                "@context": "https://schema.org",
                "@type": "SoftwareApplication",
                "name": PRODUCT_NAME,
                "applicationCategory": "EducationalApplication",
                "operatingSystem": "Web",
                "description": self.get_meta_description(),
                "url": self.get_site_root(),
                "offers": {
                    "@type": "Offer",
                    "price": "499000",
                    "priceCurrency": "IDR",
                    "availability": "https://schema.org/InStock",
                },
            }
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "proof_points": HOME_PROOF_POINTS,
                "landing_feature_cards": LANDING_FEATURE_CARDS,
                "landing_stats": LANDING_STATS,
                "implementation_steps": IMPLEMENTATION_STEPS,
                "faq_preview": FAQ_PREVIEW,
                "pricing_plan": PRICING_PLAN,
            }
        )
        return context


class FeaturesPageView(MarketingPageMixin, TemplateView):
    template_name = "marketing/features.html"
    meta_title = "Fitur CBT Sekolah | 5 Fitur Utama CBT Pro untuk Ujian Digital"
    meta_description = (
        "Pelajari fitur CBT sekolah di CBT Pro: bank soal terstruktur, randomisasi ujian, "
        "monitoring pengawas, analitik hasil, dan workflow multi-role untuk sekolah."
    )
    meta_keywords = [
        "fitur CBT sekolah",
        "fitur ujian online sekolah",
        "fitur aplikasi CBT",
        "software CBT sekolah",
        "CBT Pro",
    ]
    page_name = "Fitur CBT sekolah di CBT Pro"
    breadcrumb_label = "Fitur"
    body_class = "page-features page-minimal"
    show_marketing_chrome = False
    is_indexable = False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["feature_page_items"] = FEATURE_PAGE_ITEMS
        return context


class PricingPageView(MarketingPageMixin, TemplateView):
    template_name = "marketing/pricing.html"
    meta_title = "Harga CBT Sekolah | Paket Lisensi CBT Pro untuk Sekolah"
    meta_description = (
        "Lihat harga CBT sekolah untuk lisensi CBT Pro, detail yang termasuk, tabel perbandingan "
        "dengan SaaS dan bangun dari nol, serta FAQ pembelian."
    )
    meta_keywords = [
        "harga CBT sekolah",
        "biaya aplikasi CBT sekolah",
        "harga software ujian online",
        "lisensi CBT Pro",
        "CBT Pro",
    ]
    page_name = "Harga CBT sekolah dengan CBT Pro"
    breadcrumb_label = "Harga"
    body_class = "page-pricing page-minimal"
    show_marketing_chrome = False
    is_indexable = False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "pricing_plan": PRICING_PLAN,
                "comparison_rows": PRICING_COMPARISON_ROWS,
                "pricing_faq": PRICING_FAQ,
            }
        )
        return context


class FaqPageView(MarketingPageMixin, TemplateView):
    template_name = "marketing/faq.html"
    meta_title = "FAQ CBT Pro | Pertanyaan Umum, Harga, dan Teknis Aplikasi CBT Sekolah"
    meta_description = (
        "Temukan jawaban lengkap tentang CBT Pro, mulai dari penggunaan umum, harga pembelian, "
        "hingga kebutuhan teknis aplikasi CBT sekolah."
    )
    meta_keywords = [
        "faq CBT sekolah",
        "pertanyaan CBT Pro",
        "faq aplikasi ujian online",
        "dukungan CBT sekolah",
    ]
    page_name = "FAQ CBT Pro"
    breadcrumb_label = "FAQ"
    body_class = "page-faq page-minimal"
    show_marketing_chrome = False
    is_indexable = False


class ContactPageView(MarketingPageMixin, FormView):
    template_name = "marketing/contact.html"
    form_class = MarketingContactForm
    meta_title = "Kontak CBT Pro | Konsultasi Aplikasi CBT Sekolah"
    meta_description = (
        "Hubungi CBT Pro untuk konsultasi, demo, dan kebutuhan implementasi aplikasi CBT sekolah. "
        "Tersedia WhatsApp, email, dan form kontak dengan validasi."
    )
    meta_keywords = [
        "kontak CBT sekolah",
        "demo aplikasi CBT",
        "hubungi CBT Pro",
        "konsultasi ujian online sekolah",
    ]
    page_name = "Kontak CBT Pro"
    page_schema_type = "ContactPage"
    breadcrumb_label = "Kontak"
    body_class = "page-contact page-minimal"
    show_marketing_chrome = False
    is_indexable = False

    def get_success_url(self):
        return f"{reverse('marketing_contact')}?submitted=1"

    def get_contact_channels(self) -> list[dict[str, str]]:
        common_context = self.get_common_context()
        return [
            {
                "icon": "ri-whatsapp-line",
                "title": "WhatsApp",
                "description": "Respons tercepat untuk konsultasi lisensi, demo, dan kebutuhan implementasi sekolah.",
                "display_value": common_context["whatsapp_display"],
                "href": common_context["whatsapp_url"],
                "link_label": "Chat WhatsApp",
            },
            {
                "icon": "ri-mail-send-line",
                "title": "Email",
                "description": "Gunakan email untuk proposal, penawaran, atau koordinasi teknis yang lebih rinci.",
                "display_value": self.get_contact_email(),
                "href": f"mailto:{self.get_contact_email()}",
                "link_label": "Kirim email",
            },
            {
                "icon": "ri-time-line",
                "title": "Jam operasional",
                "description": "Tim marketing dan setup tersedia pada jam kerja untuk respons konsultasi dan tindak lanjut.",
                "display_value": DEFAULT_OPERATING_HOURS,
                "href": reverse("marketing_contact"),
                "link_label": "Isi form kontak",
            },
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "contact_channels": self.get_contact_channels(),
                "form_submitted": self.request.GET.get("submitted") == "1",
            }
        )
        return context


class SitemapXmlView(View):
    def get(self, request, *args, **kwargs):
        now = timezone.now().date().isoformat()
        pages = [
            {
                "location": _absolute_public_url(reverse("landing")),
                "lastmod": now,
                "changefreq": "weekly",
                "priority": "1.0",
            },
        ]
        content = render_to_string("marketing/sitemap.xml", {"pages": pages})
        return HttpResponse(content, content_type="application/xml; charset=utf-8")


class RobotsTxtView(View):
    def get(self, request, *args, **kwargs):
        site_root = _site_root_url()
        content = render_to_string(
            "marketing/robots.txt",
            {
                "host_name": urlparse(site_root).netloc,
                "sitemap_url": _absolute_public_url(reverse("marketing_sitemap")),
                "disallow_paths": [
                    "/admin/",
                    "/login/",
                    "/logout/",
                    "/password-reset/",
                    "/register/",
                    "/profile/",
                    "/change-password/",
                    "/teacher/",
                    "/student/",
                ],
            },
        )
        return HttpResponse(content, content_type="text/plain; charset=utf-8")


class ManifestView(View):
    def get(self, request, *args, **kwargs):
        payload = {
            "name": PRODUCT_NAME,
            "short_name": PRODUCT_NAME,
            "description": "Aplikasi CBT sekolah untuk ujian online, try out, dan asesmen digital.",
            "categories": ["education", "productivity"],
            "lang": "id-ID",
            "dir": "ltr",
            "id": _absolute_public_url(reverse("landing")),
            "start_url": _absolute_public_url(reverse("landing")),
            "scope": _absolute_public_url("/"),
            "display": "standalone",
            "display_override": ["window-controls-overlay", "standalone", "browser"],
            "orientation": "portrait-primary",
            "prefer_related_applications": False,
            "background_color": "#F5EFE3",
            "theme_color": DEFAULT_THEME_COLOR,
            "icons": [
                {
                    "src": _absolute_public_url(static("images/web-app-manifest-192x192.png")),
                    "sizes": "192x192",
                    "type": "image/png",
                    "purpose": "any",
                },
                {
                    "src": _absolute_public_url(static("images/web-app-manifest-512x512.png")),
                    "sizes": "512x512",
                    "type": "image/png",
                    "purpose": "any",
                },
            ],
        }
        return JsonResponse(payload, content_type="application/manifest+json")
