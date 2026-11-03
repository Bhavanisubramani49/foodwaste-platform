from datetime import date
from decimal import Decimal
import random

from django.contrib.auth.models import User
from django.db import models


class InventoryItem(models.Model):
    RISK_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    name = models.CharField(max_length=150)
    category = models.CharField(max_length=100)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unit = models.CharField(max_length=30, default='kg')
    purchase_date = models.DateField()
    expiry_date = models.DateField()
    storage_location = models.CharField(max_length=200, default='Main storage')
    risk_level = models.CharField(max_length=20, choices=RISK_CHOICES, default='low')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.name} ({self.quantity} {self.unit})'

    def days_until_expiry(self):
        return (self.expiry_date - date.today()).days

    def calculate_waste_risk_score(self):
        days_left = self.days_until_expiry()
        score = 10
        if days_left <= 3:
            score += 60
        elif days_left <= 7:
            score += 45
        elif days_left <= 14:
            score += 25
        elif days_left <= 30:
            score += 15

        quantity = float(self.quantity or 0)
        score += min(int(quantity / 10), 25)

        if self.risk_level == 'critical':
            score += 15
        elif self.risk_level == 'high':
            score += 10
        elif self.risk_level == 'medium':
            score += 5

        return min(score, 100)


class SurplusListing(models.Model):
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('reserved', 'Reserved'),
        ('collected', 'Collected'),
        ('cancelled', 'Cancelled'),
    ]

    business = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='surplus_listings',
    )
    food_name = models.CharField(max_length=150)
    category = models.CharField(max_length=100)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unit = models.CharField(max_length=30, default='kg')
    expiry_date = models.DateField()
    pickup_location = models.CharField(max_length=250)
    availability_window = models.CharField(max_length=200, default='Today')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.food_name} ({self.quantity} {self.unit}) - {self.status}'

    @property
    def allocated_quantity(self) -> Decimal:
        from django.db.models import Sum
        total = self.requests.filter(status__in=['requested', 'approved', 'scheduled', 'collected']).aggregate(
            total=Sum('requested_quantity')
        )['total']
        return Decimal(str(total or 0))

    @property
    def remaining_quantity(self) -> Decimal:
        qty = Decimal(str(self.quantity or 0))
        return max(Decimal('0'), qty - self.allocated_quantity)

    def is_expired(self):
        return self.expiry_date < date.today()


class NGORequirement(models.Model):
    URGENCY_CHOICES = [
        ('low', 'Low (Within 7 days)'),
        ('medium', 'Medium (Within 2-3 days)'),
        ('urgent', 'Urgent (Within 24 hours)'),
    ]
    STATUS_CHOICES = [
        ('open', 'Open / Active'),
        ('partially_fulfilled', 'Partially Fulfilled'),
        ('fulfilled', 'Fulfilled'),
        ('cancelled', 'Cancelled'),
    ]

    ngo_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='requirements',
        null=True,
        blank=True,
    )
    ngo_name = models.CharField(max_length=200)
    category = models.CharField(max_length=100)
    quantity_needed = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=30, default='kg')
    urgency = models.CharField(max_length=20, choices=URGENCY_CHOICES, default='medium')
    location = models.CharField(max_length=250, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    fulfilled_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.ngo_name}: {self.quantity_needed} {self.unit} {self.category} ({self.get_urgency_display()})"

    @property
    def unfulfilled_quantity(self) -> Decimal:
        needed = Decimal(str(self.quantity_needed or 0))
        fulfilled = Decimal(str(self.fulfilled_quantity or 0))
        return max(Decimal('0'), needed - fulfilled)


class DonationRequest(models.Model):
    STATUS_CHOICES = [
        ('requested', 'Requested'),
        ('approved', 'Approved'),
        ('scheduled', 'Scheduled'),
        ('collected', 'Collected'),
        ('cancelled', 'Cancelled'),
    ]

    listing = models.ForeignKey(SurplusListing, on_delete=models.CASCADE, related_name='requests')
    ngo_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='donation_requests',
    )
    ngo_name = models.CharField(max_length=200)
    requested_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    pickup_date = models.DateField()
    pickup_time_slot = models.CharField(max_length=100, default='Morning (9:00 - 12:00)', blank=True)
    pickup_code = models.CharField(max_length=10, blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='requested')
    cancellation_reason = models.TextField(blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.ngo_name} - {self.listing.food_name} ({self.status})'

    def save(self, *args, **kwargs):
        if not self.pickup_code:
            self.pickup_code = f"RC-{random.randint(1000, 9999)}"
        super().save(*args, **kwargs)

    def can_transition_to(self, new_status: str) -> bool:
        valid_transitions = {
            'requested': {'approved', 'cancelled'},
            'approved': {'scheduled', 'cancelled'},
            'scheduled': {'collected', 'cancelled'},
            'collected': set(),
            'cancelled': set(),
        }
        return new_status in valid_transitions.get(self.status, set())
