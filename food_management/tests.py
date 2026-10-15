from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase

from core.models import UserProfile

from .forms import DonationRequestForm, InventoryForm
from .models import DonationRequest, InventoryItem, SurplusListing


class InventoryValidationTests(TestCase):
    def test_admin_dashboard_requires_admin_role(self):
        user = get_user_model().objects.create_user(username='normal', password='strongpass123')
        UserProfile.objects.create(user=user, role='business')
        self.client.login(username='normal', password='strongpass123')

        response = self.client.get('/app/admin-panel/', follow=True)

        self.assertRedirects(response, '/app/', fetch_redirect_response=False)

    def test_inventory_form_sets_risk_level_for_near_expiry(self):
        form = InventoryForm(
            data={
                'name': 'Milk',
                'category': 'Dairy',
                'quantity': 15,
                'unit': 'litres',
                'purchase_date': date.today() - timedelta(days=2),
                'expiry_date': date.today() + timedelta(days=2),
                'storage_location': 'Fridge',
                'risk_level': 'low',
                'notes': 'Fresh delivery',
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['risk_level'], 'critical')

    def test_donation_request_rejects_quantity_above_surplus(self):
        listing = SurplusListing.objects.create(
            food_name='Bread',
            category='Bakery',
            quantity=5,
            unit='loaves',
            expiry_date=date.today() + timedelta(days=4),
            pickup_location='Warehouse',
        )
        form = DonationRequestForm(
            data={
                'listing': listing.pk,
                'ngo_name': 'Green Food Bank',
                'requested_quantity': 10,
                'pickup_date': date.today() + timedelta(days=1),
                'status': 'requested',
                'notes': 'Urgent',
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn('Requested quantity cannot exceed', str(form.errors))

    def test_dashboard_loads_with_summary_cards(self):
        InventoryItem.objects.create(
            name='Tomatoes',
            category='Produce',
            quantity=20,
            unit='kg',
            purchase_date=date.today() - timedelta(days=10),
            expiry_date=date.today() + timedelta(days=5),
        )
        response = self.client.get('/app/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'AI waste prediction')
        self.assertContains(response, 'Gamification')
