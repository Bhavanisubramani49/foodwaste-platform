from datetime import date

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

    def __str__(self):
        return f'{self.food_name} - {self.status}'


class DonationRequest(models.Model):
    STATUS_CHOICES = [
        ('requested', 'Requested'),
        ('scheduled', 'Scheduled'),
        ('collected', 'Collected'),
        ('cancelled', 'Cancelled'),
    ]

    listing = models.ForeignKey(SurplusListing, on_delete=models.CASCADE, related_name='requests')
    ngo_name = models.CharField(max_length=200)
    requested_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    pickup_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='requested')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.ngo_name} - {self.listing.food_name}'
