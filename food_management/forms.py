from datetime import date, timedelta

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone

from core.models import UserProfile

from .models import DonationRequest, InventoryItem, NGORequirement, SurplusListing


class InventoryForm(forms.ModelForm):
    class Meta:
        model = InventoryItem
        fields = [
            'name',
            'category',
            'quantity',
            'unit',
            'purchase_date',
            'expiry_date',
            'storage_location',
            'risk_level',
            'notes',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'unit': forms.TextInput(attrs={'class': 'form-control'}),
            'purchase_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'storage_location': forms.TextInput(attrs={'class': 'form-control'}),
            'risk_level': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        expiry_date = cleaned_data.get('expiry_date')
        purchase_date = cleaned_data.get('purchase_date')
        quantity = cleaned_data.get('quantity')

        if purchase_date and expiry_date and expiry_date < purchase_date:
            raise forms.ValidationError('Expiry date cannot be before the purchase date.')

        if quantity is not None and quantity <= 0:
            raise forms.ValidationError('Inventory quantity must be greater than zero.')

        if expiry_date:
            today = timezone.localdate()
            if expiry_date <= today + timedelta(days=3):
                cleaned_data['risk_level'] = 'critical'
            elif expiry_date <= today + timedelta(days=7):
                cleaned_data['risk_level'] = 'high'
            elif expiry_date <= today + timedelta(days=30):
                cleaned_data['risk_level'] = 'medium'
            else:
                cleaned_data['risk_level'] = 'low'
        return cleaned_data


class SurplusListingForm(forms.ModelForm):
    class Meta:
        model = SurplusListing
        fields = [
            'food_name',
            'category',
            'quantity',
            'unit',
            'expiry_date',
            'pickup_location',
            'availability_window',
            'status',
            'notes',
        ]
        widgets = {
            'food_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Cooked Biryani, Fresh Apples, Bread Loaves'}),
            'category': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Prepared Food, Produce, Bakery, Dairy'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '0.1', 'step': '0.1'}),
            'unit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'kg, portions, litres'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'pickup_location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Kitchen / Store address'}),
            'availability_window': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Today 2:00 PM - 6:00 PM'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Packaging details, temperature requirements'}),
        }

    def clean_quantity(self):
        qty = self.cleaned_data.get('quantity')
        if qty is not None and qty <= 0:
            raise forms.ValidationError('Surplus quantity must be greater than zero.')
        return qty

    def clean_expiry_date(self):
        expiry = self.cleaned_data.get('expiry_date')
        if expiry and expiry < date.today():
            raise forms.ValidationError('Expiry date cannot be in the past for surplus food listings.')
        return expiry


class NGORequirementForm(forms.ModelForm):
    class Meta:
        model = NGORequirement
        fields = [
            'category',
            'quantity_needed',
            'unit',
            'urgency',
            'location',
            'notes',
        ]
        widgets = {
            'category': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Dairy, Produce, Bakery, Cooked Meals'}),
            'quantity_needed': forms.NumberInput(attrs={'class': 'form-control', 'min': '0.1', 'step': '0.1'}),
            'unit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'kg, portions, boxes'}),
            'urgency': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Delivery neighborhood / area'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Dietary constraints, serving times, refrigeration available'}),
        }

    def clean_quantity_needed(self):
        qty = self.cleaned_data.get('quantity_needed')
        if qty is not None and qty <= 0:
            raise forms.ValidationError('Requested food quantity must be greater than zero.')
        return qty


class DonationRequestForm(forms.ModelForm):
    class Meta:
        model = DonationRequest
        fields = ['listing', 'ngo_name', 'requested_quantity', 'pickup_date', 'pickup_time_slot', 'status', 'notes']
        widgets = {
            'listing': forms.Select(attrs={'class': 'form-select'}),
            'ngo_name': forms.TextInput(attrs={'class': 'form-control'}),
            'requested_quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '0.1', 'step': '0.1'}),
            'pickup_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'pickup_time_slot': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 11:00 AM - 1:00 PM'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        listing = cleaned_data.get('listing')
        requested_quantity = cleaned_data.get('requested_quantity')
        pickup_date = cleaned_data.get('pickup_date')

        if listing:
            if listing.is_expired():
                raise forms.ValidationError('This surplus lot has expired and can no longer be claimed.')
            if listing.status in ['cancelled', 'collected']:
                raise forms.ValidationError(f'This surplus lot is {listing.status} and cannot be claimed.')

        if requested_quantity is not None and requested_quantity <= 0:
            raise forms.ValidationError('Requested quantity must be greater than zero.')

        if listing and requested_quantity is not None:
            remaining = listing.remaining_quantity
            if self.instance and self.instance.pk and self.instance.status in ['approved', 'scheduled', 'collected']:
                remaining += self.instance.requested_quantity
            if requested_quantity > remaining:
                raise forms.ValidationError(
                    f'Requested quantity cannot exceed the available surplus quantity ({remaining} {listing.unit}).'
                )

        if listing and pickup_date:
            if pickup_date > listing.expiry_date:
                raise forms.ValidationError('Pickup date cannot be after the surplus food expiry date.')
            if pickup_date < date.today():
                raise forms.ValidationError('Pickup date cannot be in the past.')

        return cleaned_data


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=UserProfile.ROLE_CHOICES, initial='business')
    organization_name = forms.CharField(max_length=200, required=False)

    class Meta:
        model = get_user_model()
        fields = ['username', 'email', 'password1', 'password2', 'role', 'organization_name']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            UserProfile.objects.update_or_create(
                user=user,
                defaults={
                    'role': self.cleaned_data['role'],
                    'organization_name': self.cleaned_data.get('organization_name', ''),
                },
            )
        return user


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['role', 'organization_name', 'phone_number', 'address']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-select'}),
            'organization_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }


class CSVImportForm(forms.Form):
    csv_file = forms.FileField(label='CSV file', help_text='Expected columns: name, category, quantity, unit, purchase_date, expiry_date, storage_location, notes')
