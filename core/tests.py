from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from core.models import UserProfile
from core.forms import UserRegistrationForm, UserLoginForm

User = get_user_model()


class CoreAuthenticationAndProfileTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.business_user = User.objects.create_user(
            username='donor_test',
            email='donor@test.org',
            password='Password123!',
        )
        UserProfile.objects.create(
            user=self.business_user,
            role='business',
            organization_name='Green Bakery',
            phone_number='+91 9876543210',
        )

    def test_home_page_rendering_and_context(self):
        response = self.client.get(reverse('core:home'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('login_form', response.context)
        self.assertIn('register_form', response.context)
        self.assertIn('total_items', response.context)
        self.assertIn('active_surplus', response.context)
        self.assertIn('recovered_kg', response.context)
        self.assertIn('total_ngos', response.context)

    def test_user_profile_string_representation(self):
        profile = self.business_user.profile
        self.assertIn('donor_test', str(profile))
        self.assertIn('Green Bakery', str(profile))
        self.assertIn('Food Provider / Business', str(profile))

    def test_user_registration_form_success(self):
        form_data = {
            'username': 'new_ngo_user',
            'email': 'ngo@charity.org',
            'password': 'StrongPassword123!',
            'confirm_password': 'StrongPassword123!',
            'role': 'ngo',
            'organization_name': 'Shelter Kitchen',
            'phone_number': '+91 9876543211',
        }
        form = UserRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()
        self.assertEqual(user.username, 'new_ngo_user')
        self.assertEqual(user.profile.role, 'ngo')
        self.assertEqual(user.profile.organization_name, 'Shelter Kitchen')

    def test_user_registration_password_mismatch(self):
        form_data = {
            'username': 'mismatch_user',
            'email': 'mismatch@test.org',
            'password': 'Password123!',
            'confirm_password': 'DifferentPassword456!',
            'role': 'business',
            'organization_name': 'Cafe A',
        }
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('confirm_password', form.errors)

    def test_user_registration_duplicate_username(self):
        form_data = {
            'username': 'donor_test',  # Already exists
            'email': 'other@test.org',
            'password': 'Password123!',
            'confirm_password': 'Password123!',
            'role': 'business',
            'organization_name': 'Other Bakery',
        }
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

    def test_user_registration_duplicate_email(self):
        form_data = {
            'username': 'unique_user',
            'email': 'donor@test.org',  # Already exists
            'password': 'Password123!',
            'confirm_password': 'Password123!',
            'role': 'business',
            'organization_name': 'Unique Bakery',
        }
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_login_view_with_username_success(self):
        response = self.client.post(reverse('core:login'), {
            'username': 'donor_test',
            'password': 'Password123!',
        })
        self.assertRedirects(response, '/app/')

    def test_login_view_with_email_success(self):
        response = self.client.post(reverse('core:login'), {
            'username': 'donor@test.org',
            'password': 'Password123!',
        })
        self.assertRedirects(response, '/app/')

    def test_login_view_invalid_credentials(self):
        response = self.client.post(reverse('core:login'), {
            'username': 'donor_test',
            'password': 'WrongPassword!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid username/email or password')

    def test_logout_view(self):
        self.client.login(username='donor_test', password='Password123!')
        response = self.client.get(reverse('core:logout'))
        self.assertRedirects(response, reverse('core:home'))
