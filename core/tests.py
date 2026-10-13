from django.test import TestCase, Client
from django.urls import reverse


class CoreFoundationTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_home_page_status_and_template(self):
        """Verify that the home page loads successfully with the correct template."""
        response = self.client.get(reverse('core:home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/home.html')
        self.assertTemplateUsed(response, 'base.html')
        self.assertContains(response, 'AI-Powered Food Waste Management Platform')

    def test_health_check_api_endpoint(self):
        """Verify that the DRF health check API responds with valid status JSON."""
        response = self.client.get(reverse('core:health_check'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get('status'), 'healthy')
        self.assertEqual(data.get('rest_framework'), 'active')
