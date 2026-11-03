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
        self.assertContains(response, 'AI PREDICTION')
        self.assertContains(response, 'AI Waste Forecast')
        self.assertContains(response, 'Gamification')


from unittest.mock import MagicMock, patch
from .ml_client import MLServiceClient, ml_client
from .services import estimate_waste_risk


class MLClientIntegrationTests(TestCase):
    def test_estimate_waste_risk_service_with_items(self):
        item1 = InventoryItem.objects.create(
            name='Paneer',
            category='dairy',
            quantity=10,
            unit='kg',
            purchase_date=date.today() - timedelta(days=5),
            expiry_date=date.today() + timedelta(days=2),
            risk_level='high',
        )
        res = estimate_waste_risk([item1])
        self.assertIn('avg_risk', res)
        self.assertIn('predicted_waste_kg', res)
        self.assertGreaterEqual(res['predicted_waste_kg'], 0.0)
        self.assertIn('recommended_action', res)

    def test_estimate_waste_risk_service_empty(self):
        res = estimate_waste_risk([])
        self.assertEqual(res['avg_risk'], 0)
        self.assertEqual(res['predicted_waste_kg'], 0.0)

    def test_ml_client_fallback_when_offline(self):
        client = MLServiceClient(base_url='http://127.0.0.1:9999')
        item = InventoryItem(
            name='Yogurt',
            category='dairy',
            quantity=10,
            purchase_date=date.today() - timedelta(days=2),
            expiry_date=date.today() + timedelta(days=2),
            risk_level='high',
        )
        risk = client.calculate_inventory_risk(item)
        self.assertTrue(risk.get('is_fallback'))
        self.assertEqual(risk['item_name'], 'Yogurt')
        self.assertIn('surplus_qty', risk)

    @patch('urllib.request.urlopen')
    def test_ml_client_predict_demand_mocked(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = (
            b'{"category": "dairy", "model_used": "prophet", "unit": "kg", "horizon_days": 3, '
            b'"forecast": [{"date": "2026-10-26", "predicted_demand": 40.0, "lower_bound": 30.0, "upper_bound": 50.0}], '
            b'"total_projected_demand": 40.0}'
        )
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        client = MLServiceClient()
        res = client.predict_demand(category='dairy', horizon_days=3)
        self.assertIsNotNone(res)
        self.assertEqual(res['category'], 'dairy')
        self.assertEqual(len(res['forecast']), 1)
        self.assertEqual(res['total_projected_demand'], 40.0)

    @patch('urllib.request.urlopen')
    def test_ml_client_recommend_reorder_mocked(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = (
            b'{"category": "dairy", "recommended_order_qty": 35.0, "action": "ORDER_RECOMMENDED", '
            b'"urgency": "NORMAL", "unit": "kg", "reasoning": "Restock needed."}'
        )
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        client = MLServiceClient()
        res = client.recommend_reorder(category='dairy', current_stock=15.0)
        self.assertIsNotNone(res)
        self.assertEqual(res['recommended_order_qty'], 35.0)
        self.assertEqual(res['action'], 'ORDER_RECOMMENDED')

    def test_dashboard_renders_reorder_and_forecast_data(self):
        InventoryItem.objects.create(
            name='Milk Carton',
            category='dairy',
            quantity=25,
            unit='litres',
            purchase_date=date.today() - timedelta(days=2),
            expiry_date=date.today() + timedelta(days=2),
            risk_level='high',
        )
        response = self.client.get('/app/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('dominant_category', response.context)
        self.assertIn('predicted_waste_kg', response.context)
        self.assertIn('reorder_recommendation', response.context)
        self.assertIn('forecast_labels_json', response.context)
        self.assertContains(response, 'AI REORDER RECOMMENDATION')
        self.assertContains(response, 'Fallback Heuristics Active')


from .matching import find_matches_for_listing, find_matches_for_ngo, score_match
from .models import NGORequirement
from .services import get_comprehensive_impact_analytics


class Milestone3RedistributionTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.business_user = User.objects.create_user(username='donor_biz', password='pass123')
        UserProfile.objects.create(user=self.business_user, role='business', organization_name='Green Cafe', points=0)

        self.ngo_user = User.objects.create_user(username='relief_ngo', password='pass123')
        UserProfile.objects.create(user=self.ngo_user, role='ngo', organization_name='Hope Kitchen', points=0)

    def test_surplus_listing_remaining_quantity_and_expiration(self):
        listing = SurplusListing.objects.create(
            business=self.business_user,
            food_name='Vegetable Curry',
            category='Cooked Meals',
            quantity=50.0,
            unit='kg',
            expiry_date=date.today() + timedelta(days=2),
            pickup_location='12 Market Street',
        )
        self.assertEqual(float(listing.allocated_quantity), 0.0)
        self.assertEqual(float(listing.remaining_quantity), 50.0)
        self.assertFalse(listing.is_expired())

        # Create approved claim of 20 kg
        DonationRequest.objects.create(
            listing=listing,
            ngo_user=self.ngo_user,
            ngo_name='Hope Kitchen',
            requested_quantity=20.0,
            pickup_date=date.today() + timedelta(days=1),
            status='approved',
        )
        self.assertEqual(float(listing.allocated_quantity), 20.0)
        self.assertEqual(float(listing.remaining_quantity), 30.0)

    def test_matching_engine_high_compatibility(self):
        listing = SurplusListing.objects.create(
            business=self.business_user,
            food_name='Basmati Rice',
            category='Grains',
            quantity=40.0,
            unit='kg',
            expiry_date=date.today() + timedelta(days=2),
            pickup_location='Downtown Chennai',
        )
        req = NGORequirement.objects.create(
            ngo_user=self.ngo_user,
            ngo_name='Hope Kitchen',
            category='Grains',
            quantity_needed=30.0,
            unit='kg',
            urgency='urgent',
            location='Downtown Chennai',
        )

        match_result = score_match(listing, req)
        self.assertGreaterEqual(match_result['score'], 80)
        self.assertEqual(match_result['tier'], 'Excellent Match')
        self.assertTrue(match_result['eligible'])
        self.assertEqual(match_result['category_score'], 40)
        self.assertEqual(match_result['quantity_score'], 30)

    def test_matching_engine_disqualifies_expired_food(self):
        expired_listing = SurplusListing.objects.create(
            business=self.business_user,
            food_name='Past Milk',
            category='Dairy',
            quantity=10.0,
            unit='litres',
            expiry_date=date.today() - timedelta(days=1),
            pickup_location='Warehouse 4',
        )
        req = NGORequirement.objects.create(
            ngo_user=self.ngo_user,
            ngo_name='Hope Kitchen',
            category='Dairy',
            quantity_needed=10.0,
            unit='litres',
        )
        match_result = score_match(expired_listing, req)
        self.assertEqual(match_result['score'], 0)
        self.assertFalse(match_result['eligible'])

    def test_claim_prevents_overclaiming(self):
        listing = SurplusListing.objects.create(
            business=self.business_user,
            food_name='Paneer Butter Masala',
            category='Cooked Meals',
            quantity=15.0,
            unit='kg',
            expiry_date=date.today() + timedelta(days=2),
            pickup_location='Kitchen A',
        )
        # Attempt to claim more than available
        form = DonationRequestForm(data={
            'listing': listing.pk,
            'ngo_name': 'Hope Kitchen',
            'requested_quantity': 25.0,
            'pickup_date': date.today() + timedelta(days=1),
            'status': 'requested',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('cannot exceed the available surplus quantity', str(form.errors))

    def test_claim_creation_generates_pin_and_updates_status(self):
        listing = SurplusListing.objects.create(
            business=self.business_user,
            food_name='Assorted Sandwiches',
            category='Bakery',
            quantity=20.0,
            unit='portions',
            expiry_date=date.today() + timedelta(days=2),
            pickup_location='Cafe Hub',
        )
        self.client.login(username='relief_ngo', password='pass123')
        response = self.client.post('/app/donations/request/', data={
            'listing': listing.pk,
            'ngo_name': 'Hope Kitchen',
            'requested_quantity': 20.0,
            'pickup_date': date.today() + timedelta(days=1),
            'pickup_time_slot': '11:00 AM - 1:00 PM',
            'status': 'requested',
        })
        self.assertRedirects(response, '/app/donations/')
        claim = DonationRequest.objects.get(listing=listing)
        self.assertEqual(claim.requested_quantity, 20.0)
        self.assertTrue(claim.pickup_code.startswith('RC-'))

        listing.refresh_from_db()
        self.assertEqual(listing.status, 'reserved')

    def test_donation_lifecycle_transitions_and_gamification(self):
        listing = SurplusListing.objects.create(
            business=self.business_user,
            food_name='Lentil Stew',
            category='Cooked Meals',
            quantity=30.0,
            unit='kg',
            expiry_date=date.today() + timedelta(days=3),
            pickup_location='Resto Bar',
        )
        donation = DonationRequest.objects.create(
            listing=listing,
            ngo_user=self.ngo_user,
            ngo_name='Hope Kitchen',
            requested_quantity=30.0,
            pickup_date=date.today() + timedelta(days=1),
            status='requested',
        )

        # 1. State machine validation
        self.assertTrue(donation.can_transition_to('approved'))
        self.assertFalse(donation.can_transition_to('collected'))  # Must approve/schedule first

        # 2. Advance to Approved
        self.client.login(username='donor_biz', password='pass123')
        self.client.post(f'/app/donations/{donation.pk}/update/', data={'status': 'approved'})
        donation.refresh_from_db()
        self.assertEqual(donation.status, 'approved')

        # 3. Advance to Scheduled
        self.client.post(f'/app/donations/{donation.pk}/update/', data={'status': 'scheduled'})
        donation.refresh_from_db()
        self.assertEqual(donation.status, 'scheduled')

        # 4. Advance to Collected -> Triggers points & timestamps
        self.client.post(f'/app/donations/{donation.pk}/update/', data={'status': 'collected'})
        donation.refresh_from_db()
        self.assertEqual(donation.status, 'collected')
        self.assertIsNotNone(donation.completed_at)

        listing.refresh_from_db()
        self.assertEqual(listing.status, 'collected')

        # Donor gets 30 points
        self.business_user.profile.refresh_from_db()
        self.assertEqual(self.business_user.profile.points, 30)

        # NGO gets 25 points and Impact Hero badge
        self.ngo_user.profile.refresh_from_db()
        self.assertEqual(self.ngo_user.profile.points, 25)
        self.assertIn('Impact Hero', self.ngo_user.profile.badges)

    def test_ngo_dashboard_view_routing(self):
        self.client.login(username='relief_ngo', password='pass123')
        response = self.client.get('/app/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'NGO Redistribution Command Center')
        self.assertContains(response, 'SMART MATCH ENGINE')

    def test_impact_analytics_calculations(self):
        listing = SurplusListing.objects.create(
            business=self.business_user,
            food_name='Fresh Oranges',
            category='Produce',
            quantity=100.0,
            unit='kg',
            expiry_date=date.today() + timedelta(days=4),
            pickup_location='Cold Storage',
        )
        DonationRequest.objects.create(
            listing=listing,
            ngo_user=self.ngo_user,
            ngo_name='Hope Kitchen',
            requested_quantity=100.0,
            pickup_date=date.today() - timedelta(days=1),
            status='collected',
        )

        analytics = get_comprehensive_impact_analytics()
        self.assertEqual(analytics['total_recovered_kg'], 100.0)
        # 100 kg * 2.22 = 222 meals
        self.assertEqual(analytics['meals_served'], 222)
        # 100 kg * 2.5 = 250 kg CO2e
        self.assertEqual(analytics['co2_prevented_kg'], 250.0)
        self.assertEqual(analytics['diversion_rate'], 100.0)

        # Check impact page renders
        response = self.client.get('/app/impact/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Food Diversion & Environmental Impact')
        self.assertContains(response, '100.0')
        self.assertContains(response, '222')

    def test_download_csv_template_endpoint(self):
        response = self.client.get('/app/inventory/download-template/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment; filename="inventory_import_template.csv"', response['Content-Disposition'])
        content = response.content.decode('utf-8')
        self.assertIn('name,category,quantity,unit,purchase_date,expiry_date,storage_location,notes', content)
        self.assertIn('Greek Yogurt 500g', content)

    def test_admin_user_toggle_status_and_self_guard(self):
        User = get_user_model()
        admin_user = User.objects.create_superuser(username='admin_boss', password='adminpass123')
        UserProfile.objects.create(user=admin_user, role='admin')

        target_user = User.objects.create_user(username='bad_actor', password='pass123')
        UserProfile.objects.create(user=target_user, role='business')
        self.assertTrue(target_user.is_active)

        self.client.login(username='admin_boss', password='adminpass123')

        # 1. Suspend bad actor
        response = self.client.post(f'/app/admin/users/{target_user.pk}/toggle/', follow=True)
        self.assertEqual(response.status_code, 200)
        target_user.refresh_from_db()
        self.assertFalse(target_user.is_active)

        # 2. Re-activate bad actor
        response = self.client.post(f'/app/admin/users/{target_user.pk}/toggle/', follow=True)
        self.assertEqual(response.status_code, 200)
        target_user.refresh_from_db()
        self.assertTrue(target_user.is_active)

        # 3. Prevent admin from suspending self
        response = self.client.post(f'/app/admin/users/{admin_user.pk}/toggle/', follow=True)
        self.assertEqual(response.status_code, 200)
        admin_user.refresh_from_db()
        self.assertTrue(admin_user.is_active)
        self.assertContains(response, 'You cannot suspend your own administrative account')

    def test_claim_rejects_expired_and_cancelled_or_collected_surplus(self):
        expired_listing = SurplusListing.objects.create(
            business=self.business_user,
            food_name='Expired Milk',
            category='Dairy',
            quantity=10.0,
            unit='litres',
            expiry_date=date.today() - timedelta(days=1),
            pickup_location='Cold Room',
        )
        self.client.login(username='relief_ngo', password='pass123')
        res = self.client.post('/app/donations/request/', data={
            'listing': expired_listing.pk,
            'ngo_name': 'Hope Kitchen',
            'requested_quantity': 5.0,
            'pickup_date': date.today() - timedelta(days=1),
            'status': 'requested',
        })
        self.assertContains(res, 'expired and can no longer be claimed')

        cancelled_listing = SurplusListing.objects.create(
            business=self.business_user,
            food_name='Cancelled Apples',
            category='Produce',
            quantity=10.0,
            unit='kg',
            expiry_date=date.today() + timedelta(days=2),
            pickup_location='Warehouse',
            status='cancelled',
        )
        res2 = self.client.post('/app/donations/request/', data={
            'listing': cancelled_listing.pk,
            'ngo_name': 'Hope Kitchen',
            'requested_quantity': 5.0,
            'pickup_date': date.today() + timedelta(days=1),
            'status': 'requested',
        })
        self.assertContains(res2, 'cancelled and cannot be claimed')

    def test_surplus_cancellation_and_collected_lot_guard(self):
        listing = SurplusListing.objects.create(
            business=self.business_user,
            food_name='Pastries',
            category='Bakery',
            quantity=20.0,
            unit='boxes',
            expiry_date=date.today() + timedelta(days=2),
            pickup_location='Bakery',
        )
        donation = DonationRequest.objects.create(
            listing=listing,
            ngo_user=self.ngo_user,
            ngo_name='Hope Kitchen',
            requested_quantity=10.0,
            pickup_date=date.today() + timedelta(days=1),
            status='requested',
        )

        # Unauthorized user cannot cancel
        other_user = get_user_model().objects.create_user(username='other_biz', password='pass123')
        UserProfile.objects.create(user=other_user, role='business')
        self.client.login(username='other_biz', password='pass123')
        res = self.client.post(f'/app/surplus/{listing.pk}/cancel/', follow=True)
        self.assertContains(res, 'Permission denied: You can only cancel your own surplus listings')
        listing.refresh_from_db()
        self.assertEqual(listing.status, 'available')

        # Owner can cancel active listing
        self.client.login(username='donor_biz', password='pass123')
        res = self.client.post(f'/app/surplus/{listing.pk}/cancel/', follow=True)
        self.assertEqual(res.status_code, 200)
        listing.refresh_from_db()
        self.assertEqual(listing.status, 'cancelled')
        donation.refresh_from_db()
        self.assertEqual(donation.status, 'cancelled')
        self.assertIn('Surplus lot cancelled by donor', donation.cancellation_reason)

        # Cannot cancel already collected listing
        collected_listing = SurplusListing.objects.create(
            business=self.business_user,
            food_name='Consumed Soup',
            category='Cooked Meals',
            quantity=10.0,
            unit='kg',
            expiry_date=date.today() + timedelta(days=1),
            pickup_location='Kitchen',
            status='collected',
        )
        res2 = self.client.post(f'/app/surplus/{collected_listing.pk}/cancel/', follow=True)
        self.assertContains(res2, 'Cannot cancel a surplus listing that has already been collected')
        collected_listing.refresh_from_db()
        self.assertEqual(collected_listing.status, 'collected')

    def test_donation_status_update_rbac_and_pin_verification(self):
        listing = SurplusListing.objects.create(
            business=self.business_user,
            food_name='Dal Fry',
            category='Cooked Meals',
            quantity=15.0,
            unit='kg',
            expiry_date=date.today() + timedelta(days=2),
            pickup_location='Food Center',
        )
        donation = DonationRequest.objects.create(
            listing=listing,
            ngo_user=self.ngo_user,
            ngo_name='Hope Kitchen',
            requested_quantity=15.0,
            pickup_date=date.today() + timedelta(days=1),
            status='requested',
        )
        pin = donation.pickup_code

        # 1. Third party user cannot update donation
        unrelated_user = get_user_model().objects.create_user(username='rando_ngo', password='pass123')
        UserProfile.objects.create(user=unrelated_user, role='ngo')
        self.client.login(username='rando_ngo', password='pass123')
        res = self.client.post(f'/app/donations/{donation.pk}/update/', data={'status': 'approved'}, follow=True)
        self.assertContains(res, 'Permission denied: You do not have permission to manage this donation allocation')

        # 2. NGO claimant cannot self-approve
        self.client.login(username='relief_ngo', password='pass123')
        res = self.client.post(f'/app/donations/{donation.pk}/update/', data={'status': 'approved'}, follow=True)
        self.assertContains(res, 'Only the donor business or an administrator can approve donation requests')
        donation.refresh_from_db()
        self.assertEqual(donation.status, 'requested')

        # 3. Donor business approves
        self.client.login(username='donor_biz', password='pass123')
        self.client.post(f'/app/donations/{donation.pk}/update/', data={'status': 'approved'}, follow=True)
        donation.refresh_from_db()
        self.assertEqual(donation.status, 'approved')

        # 4. Schedule pickup
        self.client.login(username='relief_ngo', password='pass123')
        self.client.post(f'/app/donations/{donation.pk}/update/', data={'status': 'scheduled'}, follow=True)
        donation.refresh_from_db()
        self.assertEqual(donation.status, 'scheduled')

        # 5. Invalid PIN rejected upon collection
        self.client.login(username='donor_biz', password='pass123')
        res_fail = self.client.post(f'/app/donations/{donation.pk}/update/', data={'status': 'collected', 'verification_pin': 'RC-9999'}, follow=True)
        self.assertContains(res_fail, 'Verification failed: PIN')
        donation.refresh_from_db()
        self.assertEqual(donation.status, 'scheduled')

        # 6. Valid PIN succeeds
        res_success = self.client.post(f'/app/donations/{donation.pk}/update/', data={'status': 'collected', 'verification_pin': pin}, follow=True)
        self.assertEqual(res_success.status_code, 200)
        donation.refresh_from_db()
        self.assertEqual(donation.status, 'collected')
        self.assertIsNotNone(donation.completed_at)

    def test_ngo_requirement_status_toggle_and_rbac(self):
        req = NGORequirement.objects.create(
            ngo_user=self.ngo_user,
            ngo_name='Hope Kitchen',
            category='Vegetables',
            quantity_needed=50.0,
            unit='kg',
            status='open',
        )

        # Unauthorized user cannot toggle requirement
        other_user = get_user_model().objects.create_user(username='intruder_ngo', password='pass123')
        UserProfile.objects.create(user=other_user, role='ngo')
        self.client.login(username='intruder_ngo', password='pass123')
        res = self.client.post(f'/app/ngo/requirements/{req.pk}/status/', data={'status': 'cancelled'}, follow=True)
        self.assertContains(res, 'Permission denied: You can only update your own food requirements')
        req.refresh_from_db()
        self.assertEqual(req.status, 'open')

        # NGO owner can fulfill or cancel
        self.client.login(username='relief_ngo', password='pass123')
        res2 = self.client.post(f'/app/ngo/requirements/{req.pk}/status/', data={'status': 'fulfilled'}, follow=True)
        self.assertEqual(res2.status_code, 200)
        req.refresh_from_db()
        self.assertEqual(req.status, 'fulfilled')

        # Smart matching rejects fulfilled requirement
        listing = SurplusListing.objects.create(
            business=self.business_user,
            food_name='Fresh Veggies',
            category='Vegetables',
            quantity=50.0,
            unit='kg',
            expiry_date=date.today() + timedelta(days=2),
            pickup_location='Market',
        )
        match = score_match(listing, req)
        self.assertEqual(match['score'], 0)
        self.assertFalse(match['eligible'])
        self.assertIn('already fulfilled', match['reasons'][0])