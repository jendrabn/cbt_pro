from django.urls import path

from .views import (
    ContactPageView,
    FaqPageView,
    FeaturesPageView,
    LandingPageView,
    ManifestView,
    PricingPageView,
    RobotsTxtView,
    SitemapXmlView,
)


urlpatterns = [
    path("", LandingPageView.as_view(), name="landing"),
    path("features/", FeaturesPageView.as_view(), name="marketing_features"),
    path("pricing/", PricingPageView.as_view(), name="marketing_pricing"),
    path("faq/", FaqPageView.as_view(), name="marketing_faq"),
    path("contact/", ContactPageView.as_view(), name="marketing_contact"),
    path("sitemap.xml", SitemapXmlView.as_view(), name="marketing_sitemap"),
    path("robots.txt", RobotsTxtView.as_view(), name="marketing_robots"),
    path("manifest.json", ManifestView.as_view(), name="marketing_manifest"),
    path("manifest.webmanifest", ManifestView.as_view(), name="marketing_manifest_webmanifest"),
]
