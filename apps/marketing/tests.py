from django.test import TestCase, override_settings
from django.urls import reverse


@override_settings(
    SECURE_SSL_REDIRECT=False,
    ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"],
)
class MarketingPagesTests(TestCase):
    def test_landing_page_uses_marketing_template_content(self):
        response = self.client.get(reverse("landing"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Aplikasi CBT Sekolah")
        self.assertContains(response, "manifest.json")
        self.assertContains(response, 'content="index, follow', html=False)

    def test_secondary_pages_show_coming_soon_state(self):
        for route_name in (
            "marketing_features",
            "marketing_pricing",
            "marketing_faq",
            "marketing_contact",
        ):
            response = self.client.get(reverse(route_name))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "Coming Soon")
            self.assertContains(response, 'content="noindex, nofollow, noarchive, nosnippet"', html=False)
            self.assertEqual(response["X-Robots-Tag"], "noindex, nofollow, noarchive, nosnippet")

    def test_robots_and_sitemap_are_available(self):
        robots_response = self.client.get(reverse("marketing_robots"))
        sitemap_response = self.client.get(reverse("marketing_sitemap"))

        self.assertEqual(robots_response.status_code, 200)
        self.assertContains(robots_response, "Host: cbtpro.web.id")
        self.assertContains(robots_response, "Sitemap: https://cbtpro.web.id/sitemap.xml")
        self.assertContains(robots_response, "Disallow: /admin/")
        self.assertEqual(sitemap_response.status_code, 200)
        self.assertContains(sitemap_response, "<loc>https://cbtpro.web.id/</loc>", html=False)
        self.assertNotContains(sitemap_response, "<loc>https://cbtpro.web.id/features/</loc>", html=False)

    def test_manifest_json_is_available(self):
        response = self.client.get(reverse("marketing_manifest"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/manifest+json")
        self.assertContains(response, '"start_url": "https://cbtpro.web.id/"', html=False)
