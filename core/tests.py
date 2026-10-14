from django.test import TestCase, Client
from django.urls import reverse


class FoodWasteAIFoundationTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_home_page_rendering_and_branding(self):
        """Verify that the home page loads with FoodWasteAI brand and headline."""
        response = self.client.get(reverse('core:home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/home.html')
        self.assertTemplateUsed(response, 'base.html')
        self.assertContains(response, 'FoodWasteAI')
        self.assertContains(response, 'Turn Surplus Food into')
        self.assertContains(response, 'Community Impact')

    def test_business_dashboard_rendering_and_kpis(self):
        """Verify that the Business Dashboard loads with KPI statistics and Chart.js containers."""
        response = self.client.get(reverse('core:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/dashboard.html')
        self.assertTemplateUsed(response, 'base.html')
        self.assertContains(response, 'Business Operations Dashboard')
        self.assertContains(response, 'Inventory Batches')
        self.assertContains(response, 'categoryChart')
        self.assertContains(response, 'expiryTimelineChart')
        self.assertContains(response, 'riskChart')
        self.assertContains(response, 'donationVolumeChart')

    def test_all_navigation_views_return_200(self):
        """Ensure all primary sidebar navigation links resolve with HTTP 200 without broken routes."""
        endpoints = [
            'core:inventory_list',
            'core:expiry_alerts',
            'core:waste_prediction',
            'core:marketplace',
            'core:ngo_requirements',
            'core:donation_requests',
            'core:pickup_schedule',
            'core:impact_analytics',
            'core:leaderboard',
            'core:notifications',
            'core:profile',
        ]
        for ep in endpoints:
            with self.subTest(endpoint=ep):
                res = self.client.get(reverse(ep))
                self.assertEqual(res.status_code, 200)

    def test_health_check_api_endpoint(self):
        """Verify that the DRF health check API responds with valid status JSON and theme info."""
        response = self.client.get(reverse('core:health_check'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get('status'), 'healthy')
        self.assertEqual(data.get('platform'), 'FoodWasteAI')
        self.assertEqual(data.get('theme'), 'Orange + Sky Blue')
        self.assertEqual(data.get('rest_framework'), 'active')
