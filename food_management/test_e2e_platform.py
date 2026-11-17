from datetime import date, timedelta
from decimal import Decimal
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase

from core.models import UserProfile
from food_management.forms import (
    DonationRequestForm,
    InventoryForm,
    NGORequirementForm,
    SurplusListingForm,
)
from food_management.matching import find_matches_for_ngo, score_match
from food_management.models import (
    DonationRequest,
    InventoryItem,
    NGORequirement,
    SurplusListing,
)
from food_management.services import get_comprehensive_impact_analytics


User = get_user_model()


class BusinessWorkflowTests(TestCase):
    """
    End-to-End tests for Business user workflows:
    - Login and dashboard
    - Inventory Add, Edit, Delete (CRUD)
    - Expiry alerts view and risk-level filtering
    - CSV bulk import and error validation
    - Waste-risk predictions
    - Demand forecasts and reorder recommendations
    - Surplus food listing creation
    """

    def setUp(self):
        self.business_user = User.objects.create_user(
            username='bistro_owner',
            password='Password123!',
            email='bistro@foodwaste.ai'
        )
        self.profile = UserProfile.objects.create(
            user=self.business_user,
            role='business',
            organization_name='Green Bistro',
            phone_number='+91 98765 43210',
            address='12 Anna Nagar, Chennai',
            points=0,
            level=1
        )
        self.client = Client()

    def test_business_login_and_dashboard(self):
        # 1. Login with valid credentials
        login_success = self.client.login(username='bistro_owner', password='Password123!')
        self.assertTrue(login_success, "Business user should successfully log in.")

        # 2. Access dashboard
        response = self.client.get('/app/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Food Waste Operations Dashboard")
        self.assertContains(response, "AI Waste Forecast")
        self.assertContains(response, "Active Shelf Batches")

    def test_inventory_crud_lifecycle(self):
        self.client.login(username='bistro_owner', password='Password123!')

        # 1. Add Inventory
        create_response = self.client.post('/app/inventory/add/', data={
            'name': 'Fresh Paneer',
            'category': 'Dairy',
            'quantity': '20.0',
            'unit': 'kg',
            'purchase_date': (date.today() - timedelta(days=1)).isoformat(),
            'expiry_date': (date.today() + timedelta(days=3)).isoformat(),
            'storage_location': 'Walk-in Chiller',
            'notes': 'Keep at 4C',
        }, follow=True)
        self.assertEqual(create_response.status_code, 200)
        item = InventoryItem.objects.filter(name='Fresh Paneer').first()
        self.assertIsNotNone(item, "Inventory item should be created.")
        self.assertEqual(item.quantity, Decimal('20.0'))
        self.assertEqual(item.storage_location, 'Walk-in Chiller')

        # 2. Edit Inventory
        edit_response = self.client.post(f'/app/inventory/{item.pk}/edit/', data={
            'name': 'Fresh Paneer Premium',
            'category': 'Dairy',
            'quantity': '18.5',
            'unit': 'kg',
            'purchase_date': (date.today() - timedelta(days=1)).isoformat(),
            'expiry_date': (date.today() + timedelta(days=3)).isoformat(),
            'storage_location': 'Chiller Shelf 2',
            'notes': 'Updated quantity after shift',
        }, follow=True)
        self.assertEqual(edit_response.status_code, 200)
        item.refresh_from_db()
        self.assertEqual(item.name, 'Fresh Paneer Premium')
        self.assertEqual(item.quantity, Decimal('18.5'))
        self.assertEqual(item.storage_location, 'Chiller Shelf 2')

        # 3. Delete Inventory
        del_response = self.client.post(f'/app/inventory/{item.pk}/delete/', follow=True)
        self.assertEqual(del_response.status_code, 200)
        self.assertFalse(InventoryItem.objects.filter(pk=item.pk).exists(), "Item should be deleted.")

    def test_view_expiry_alerts_and_filtering(self):
        self.client.login(username='bistro_owner', password='Password123!')

        # Create 1 critical item and 1 safe item
        critical_item = InventoryItem.objects.create(
            name='Cooked Dal',
            category='Cooked Meals',
            quantity=15.0,
            unit='kg',
            purchase_date=date.today() - timedelta(days=2),
            expiry_date=date.today() + timedelta(days=1),
            risk_level='critical',
        )
        safe_item = InventoryItem.objects.create(
            name='Basmati Rice Bag',
            category='Grains',
            quantity=100.0,
            unit='kg',
            purchase_date=date.today(),
            expiry_date=date.today() + timedelta(days=90),
            risk_level='low',
        )

        # Access dedicated expiry-alerts endpoint
        response = self.client.get('/app/expiry-alerts/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cooked Dal')

        # Filter by risk query parameter
        filter_res = self.client.get('/app/inventory/?risk=critical')
        self.assertEqual(filter_res.status_code, 200)
        self.assertContains(filter_res, 'Cooked Dal')
        self.assertNotContains(filter_res, 'Basmati Rice Bag')

    def test_import_csv_valid_and_invalid(self):
        self.client.login(username='bistro_owner', password='Password123!')

        # 1. Valid CSV Import
        valid_csv = (
            "name,category,quantity,unit,purchase_date,expiry_date,storage_location,notes\n"
            f"Curd 500g,Dairy,30.0,tubs,{date.today().isoformat()},{(date.today() + timedelta(days=4)).isoformat()},Fridge A,Sealed\n"
            f"Wheat Bread,Bakery,15.0,loaves,{date.today().isoformat()},{(date.today() + timedelta(days=2)).isoformat()},Bakery Rack,Fresh\n"
        ).encode('utf-8')

        csv_file = SimpleUploadedFile("inventory.csv", valid_csv, content_type="text/csv")
        res = self.client.post('/app/inventory/import/', {'csv_file': csv_file}, follow=True)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(InventoryItem.objects.filter(name='Curd 500g').exists())
        self.assertTrue(InventoryItem.objects.filter(name='Wheat Bread').exists())

        # 2. Invalid CSV Import (empty / missing header)
        invalid_csv = "random_col1,random_col2\nfoo,bar\n".encode('utf-8')
        bad_file = SimpleUploadedFile("bad.csv", invalid_csv, content_type="text/csv")
        res_bad = self.client.post('/app/inventory/import/', {'csv_file': bad_file}, follow=True)
        self.assertEqual(res_bad.status_code, 200)
        self.assertContains(res_bad, "Imported 0 inventory item")

    def test_waste_risk_predictions_and_demand_forecasts_on_dashboard(self):
        self.client.login(username='bistro_owner', password='Password123!')

        InventoryItem.objects.create(
            name='Milk Cartons',
            category='Dairy',
            quantity=40.0,
            unit='litres',
            purchase_date=date.today() - timedelta(days=3),
            expiry_date=date.today() + timedelta(days=1),
            risk_level='high',
        )

        response = self.client.get('/app/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('predicted_waste_kg', response.context)
        self.assertGreater(response.context['predicted_waste_kg'], 0)
        self.assertIn('dominant_category', response.context)
        self.assertIn('reorder_recommendation', response.context)
        self.assertContains(response, "AI REORDER RECOMMENDATION")
        self.assertContains(response, "AI Waste Forecast")

    def test_create_surplus_food_listing(self):
        self.client.login(username='bistro_owner', password='Password123!')

        res = self.client.post('/app/surplus/add/', data={
            'food_name': 'Vegetable Pulao (Evening Batch)',
            'category': 'Cooked Meals',
            'quantity': '25.0',
            'unit': 'kg',
            'expiry_date': (date.today() + timedelta(days=1)).isoformat(),
            'pickup_location': 'Green Bistro Kitchen Door',
            'availability_window': '6:00 PM - 9:00 PM',
            'status': 'available',
            'notes': 'Freshly prepared, hot food grade containers',
        }, follow=True)
        self.assertEqual(res.status_code, 200)
        listing = SurplusListing.objects.filter(food_name='Vegetable Pulao (Evening Batch)').first()
        self.assertIsNotNone(listing)
        self.assertEqual(listing.business, self.business_user)
        self.assertEqual(listing.remaining_quantity, Decimal('25.0'))
        self.assertEqual(listing.status, 'available')


class NGOWorkflowTests(TestCase):
    """
    End-to-End tests for NGO user workflows:
    - Access NGO dashboard
    - Create NGO food requirements
    - View matching surplus food
    - Submit donation requests
    - Verify pickup PIN
    - Track donation status transitions
    """

    def setUp(self):
        self.business_user = User.objects.create_user(
            username='donor_restaurant',
            password='Password123!',
            email='donor@foodwaste.ai'
        )
        UserProfile.objects.create(
            user=self.business_user,
            role='business',
            organization_name='Royal Kitchen',
            points=0
        )

        self.ngo_user = User.objects.create_user(
            username='shelter_ngo',
            password='Password123!',
            email='ngo@foodwaste.ai'
        )
        self.ngo_profile = UserProfile.objects.create(
            user=self.ngo_user,
            role='ngo',
            organization_name='Seva Shelter Food Bank',
            points=0,
            level=1
        )
        self.client = Client()

    def test_access_ngo_dashboard(self):
        self.client.login(username='shelter_ngo', password='Password123!')

        # Dedicated NGO endpoint
        res = self.client.get('/app/ngo/')
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "NGO Redistribution Command Center")
        self.assertContains(res, "Active Pickups")

        # Root route redirects/renders NGO view for NGO users
        res_root = self.client.get('/app/')
        self.assertEqual(res_root.status_code, 200)
        self.assertContains(res_root, "NGO Redistribution Command Center")

    def test_create_ngo_requirement_and_matching_surplus(self):
        self.client.login(username='shelter_ngo', password='Password123!')

        # 1. Create Requirement
        res = self.client.post('/app/ngo/requirements/add/', data={
            'category': 'Cooked Meals',
            'quantity_needed': '50.0',
            'unit': 'kg',
            'urgency': 'urgent',
            'location': 'Central Chennai',
            'notes': 'Dinner distribution for 150 community members',
        }, follow=True)
        self.assertEqual(res.status_code, 200)
        req = NGORequirement.objects.filter(category='Cooked Meals', ngo_user=self.ngo_user).first()
        self.assertIsNotNone(req)
        self.assertEqual(req.urgency, 'urgent')

        # 2. Create Compatible Surplus Listing
        listing = SurplusListing.objects.create(
            business=self.business_user,
            food_name='Vegetable Biryani',
            category='Cooked Meals',
            quantity=50.0,
            unit='kg',
            expiry_date=date.today() + timedelta(days=1),
            pickup_location='Central Chennai',
            status='available',
        )

        # 3. Check Smart Matching
        matches = find_matches_for_ngo(req, min_score=40)
        self.assertTrue(len(matches) > 0, "Should find compatible surplus match.")
        top_match = matches[0]
        self.assertEqual(top_match['listing'].pk, listing.pk)
        self.assertGreaterEqual(top_match['score'], 80)

        # 4. View requirements list page
        res_list = self.client.get('/app/ngo/requirements/')
        self.assertEqual(res_list.status_code, 200)
        self.assertContains(res_list, 'Vegetable Biryani')

    def test_submit_donation_request_and_pin_generation(self):
        listing = SurplusListing.objects.create(
            business=self.business_user,
            food_name='Sourdough Loaves',
            category='Bakery',
            quantity=30.0,
            unit='loaves',
            expiry_date=date.today() + timedelta(days=2),
            pickup_location='Baker Street',
            status='available',
        )

        self.client.login(username='shelter_ngo', password='Password123!')
        res = self.client.post('/app/donations/request/', data={
            'listing': listing.pk,
            'ngo_name': 'Seva Shelter Food Bank',
            'requested_quantity': '30.0',
            'pickup_date': (date.today() + timedelta(days=1)).isoformat(),
            'pickup_time_slot': '10:00 AM - 12:00 PM',
            'status': 'requested',
            'notes': 'Driver will arrive in van',
        }, follow=True)
        self.assertEqual(res.status_code, 200)

        claim = DonationRequest.objects.filter(listing=listing).first()
        self.assertIsNotNone(claim)
        self.assertEqual(claim.requested_quantity, Decimal('30.0'))
        self.assertTrue(claim.pickup_code.startswith('RC-'), f"Expected PIN starting with RC-, got {claim.pickup_code}")

        # Surplus listing is now reserved since remaining stock is 0
        listing.refresh_from_db()
        self.assertEqual(listing.status, 'reserved')

    def test_verify_pickup_pin_and_track_donation_lifecycle(self):
        listing = SurplusListing.objects.create(
            business=self.business_user,
            food_name='Fresh Apples',
            category='Produce',
            quantity=20.0,
            unit='kg',
            expiry_date=date.today() + timedelta(days=3),
            pickup_location='Orchard Hub',
            status='available',
        )
        donation = DonationRequest.objects.create(
            listing=listing,
            ngo_user=self.ngo_user,
            ngo_name='Seva Shelter Food Bank',
            requested_quantity=20.0,
            pickup_date=date.today() + timedelta(days=1),
            status='requested',
        )
        pin = donation.pickup_code

        # Step 1: Donor approves
        self.client.login(username='donor_restaurant', password='Password123!')
        res_app = self.client.post(f'/app/donations/{donation.pk}/update/', data={'status': 'approved'}, follow=True)
        self.assertEqual(res_app.status_code, 200)
        donation.refresh_from_db()
        self.assertEqual(donation.status, 'approved')

        # Step 2: NGO schedules pickup
        self.client.login(username='shelter_ngo', password='Password123!')
        res_sch = self.client.post(f'/app/donations/{donation.pk}/update/', data={'status': 'scheduled'}, follow=True)
        self.assertEqual(res_sch.status_code, 200)
        donation.refresh_from_db()
        self.assertEqual(donation.status, 'scheduled')

        # Step 3: Collection with Wrong PIN fails
        self.client.login(username='donor_restaurant', password='Password123!')
        res_fail = self.client.post(
            f'/app/donations/{donation.pk}/update/',
            data={'status': 'collected', 'verification_pin': 'RC-0000'},
            follow=True
        )
        self.assertContains(res_fail, "Verification failed: PIN")
        donation.refresh_from_db()
        self.assertEqual(donation.status, 'scheduled')

        # Step 4: Collection with Correct PIN succeeds
        res_ok = self.client.post(
            f'/app/donations/{donation.pk}/update/',
            data={'status': 'collected', 'verification_pin': pin},
            follow=True
        )
        self.assertEqual(res_ok.status_code, 200)
        donation.refresh_from_db()
        self.assertEqual(donation.status, 'collected')
        self.assertIsNotNone(donation.completed_at)

        listing.refresh_from_db()
        self.assertEqual(listing.status, 'collected')


class ImpactAnalyticsWorkflowTests(TestCase):
    """
    End-to-End tests for Impact Analytics dashboard:
    - Calculation of meals, CO2, diversion rate from actual database records
    - Handling of empty-data and zero-value states
    """

    def setUp(self):
        self.client = Client()

    def test_impact_analytics_empty_data_cases(self):
        # Database has zero completed donations
        analytics = get_comprehensive_impact_analytics()
        self.assertEqual(analytics['total_recovered_kg'], 0.0)
        self.assertEqual(analytics['meals_served'], 0)
        self.assertEqual(analytics['co2_prevented_kg'], 0.0)
        self.assertEqual(analytics['diversion_rate'], 0.0)
        self.assertEqual(analytics['completed_collections_count'], 0)

        # Impact page renders safely with zero-value state
        response = self.client.get('/app/impact/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Food Diversion & Environmental Impact")

    def test_impact_analytics_calculated_from_actual_db_records(self):
        user = User.objects.create_user(username='farm_donor', password='Password123!')
        listing = SurplusListing.objects.create(
            business=user,
            food_name='Organic Carrots',
            category='Produce',
            quantity=200.0,
            unit='kg',
            expiry_date=date.today() + timedelta(days=5),
            pickup_location='Farm Shed 3',
        )
        DonationRequest.objects.create(
            listing=listing,
            ngo_name='City Meals Foundation',
            requested_quantity=200.0,
            pickup_date=date.today() - timedelta(days=1),
            status='collected',
        )

        analytics = get_comprehensive_impact_analytics()
        # 200 kg recovered
        self.assertEqual(analytics['total_recovered_kg'], 200.0)
        # 200 * 2.22 = 444 meals
        self.assertEqual(analytics['meals_served'], 444)
        # 200 * 2.5 = 500 kg CO2e
        self.assertEqual(analytics['co2_prevented_kg'], 500.0)
        # 200 / 500 = 0.4 m^3 landfill saved
        self.assertEqual(analytics['landfill_m3_saved'], 0.4)
        # Diversion rate = 100.0%
        self.assertEqual(analytics['diversion_rate'], 100.0)


class SecurityAndValidationWorkflowTests(TestCase):
    """
    End-to-End tests for:
    - Authentication and permissions (role enforcement)
    - Form validation & invalid inputs
    - Missing API responses (FastAPI fallback)
    - Page navigation
    - Responsive layout and error messages
    """

    def setUp(self):
        self.business_user = User.objects.create_user(
            username='secure_biz',
            password='Password123!'
        )
        UserProfile.objects.create(user=self.business_user, role='business')

        self.ngo_user = User.objects.create_user(
            username='secure_ngo',
            password='Password123!'
        )
        UserProfile.objects.create(user=self.ngo_user, role='ngo')

        self.client = Client()

    def test_role_based_permissions(self):
        # 1. Anonymous user blocked from creating inventory
        res = self.client.post('/app/inventory/add/', data={}, follow=True)
        self.assertRedirects(res, '/app/accounts/login/', fetch_redirect_response=False)

        # 2. NGO role blocked from adding business inventory
        self.client.login(username='secure_ngo', password='Password123!')
        res_ngo = self.client.post('/app/inventory/add/', data={}, follow=True)
        self.assertRedirects(res_ngo, '/app/', fetch_redirect_response=False)

        # 3. Business role blocked from creating NGO requirements
        self.client.login(username='secure_biz', password='Password123!')
        res_biz = self.client.post('/app/ngo/requirements/add/', data={}, follow=True)
        self.assertRedirects(res_biz, '/app/', fetch_redirect_response=False)

    def test_form_validation_and_invalid_inputs(self):
        self.client.login(username='secure_biz', password='Password123!')

        # 1. Negative quantity in inventory rejected
        form_inv = InventoryForm(data={
            'name': 'Bad Item',
            'category': 'Dairy',
            'quantity': -5.0,
            'unit': 'kg',
            'purchase_date': date.today(),
            'expiry_date': date.today() + timedelta(days=2),
            'storage_location': 'Rack',
        })
        self.assertFalse(form_inv.is_valid())

        # 2. Past expiry date in surplus listing rejected
        form_surplus = SurplusListingForm(data={
            'food_name': 'Expired Item',
            'category': 'Bakery',
            'quantity': 10.0,
            'unit': 'kg',
            'expiry_date': date.today() - timedelta(days=1),
            'pickup_location': 'Street',
        })
        self.assertFalse(form_surplus.is_valid())
        self.assertIn('Expiry date cannot be in the past', str(form_surplus.errors))

        # 3. Overclaiming surplus quantity rejected
        listing = SurplusListing.objects.create(
            business=self.business_user,
            food_name='Limited Bread',
            category='Bakery',
            quantity=10.0,
            unit='loaves',
            expiry_date=date.today() + timedelta(days=2),
            pickup_location='Bakery',
        )
        form_claim = DonationRequestForm(data={
            'listing': listing.pk,
            'ngo_name': 'Food Bank',
            'requested_quantity': 50.0,
            'pickup_date': date.today() + timedelta(days=1),
            'status': 'requested',
        })
        self.assertFalse(form_claim.is_valid())
        self.assertIn('cannot exceed the available surplus quantity', str(form_claim.errors))

    def test_page_navigation_all_routes_return_200(self):
        self.client.login(username='secure_biz', password='Password123!')
        routes = [
            '/app/',
            '/app/inventory/',
            '/app/expiry-alerts/',
            '/app/surplus/',
            '/app/donations/',
            '/app/ngo/requirements/',
            '/app/impact/',
            '/app/leaderboard/',
            '/app/accounts/profile/',
        ]
        for url in routes:
            with self.subTest(url=url):
                res = self.client.get(url)
                self.assertEqual(res.status_code, 200, f"Route {url} failed with status {res.status_code}")

    def test_responsive_layout_meta_and_flash_messages(self):
        # 1. Verify responsive viewport in base template
        res = self.client.get('/app/')
        self.assertContains(res, '<meta name="viewport" content="width=device-width, initial-scale=1.0">')

        # 2. Verify error messages framework renders cleanly
        self.client.login(username='secure_biz', password='Password123!')
        # Trigger an invalid status transition to test error display
        listing = SurplusListing.objects.create(
            business=self.business_user,
            food_name='Soup',
            category='Cooked Meals',
            quantity=5.0,
            unit='kg',
            expiry_date=date.today() + timedelta(days=1),
            pickup_location='Kitchen',
        )
        donation = DonationRequest.objects.create(
            listing=listing,
            ngo_name='Shelter',
            requested_quantity=5.0,
            pickup_date=date.today() + timedelta(days=1),
            status='requested',
        )
        res_invalid = self.client.post(
            f'/app/donations/{donation.pk}/update/',
            data={'status': 'collected'},  # Cannot jump directly to collected
            follow=True
        )
        self.assertEqual(res_invalid.status_code, 200)
        self.assertContains(res_invalid, "Invalid status transition")
