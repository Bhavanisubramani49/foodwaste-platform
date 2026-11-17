# FoodWasteAI – Database Design & Schema Specification

## 1. Relational Database Overview

FoodWasteAI uses a normalized PostgreSQL relational database (`foodwaste_db`). The schema enforces referential integrity, column constraints, cascading behaviors, and ACID compliance across inventory, surplus allocations, and donation transfers.

```
+----------------------------------------------------------------------------------------------------+
|                                    Entity-Relationship Overview                                    |
+----------------------------------------------------------------------------------------------------+
|                                                                                                    |
|    +-------------------+           1:1           +----------------------+                          |
|    |     auth_user     | ──────────────────────> |   core_userprofile   |                          |
|    +-------------------+                         +----------------------+                          |
|              │                                              │                                      |
|              │ 1:N (business)                               │ 1:N (role='ngo')                     |
|              ▼                                              ▼                                      |
|    +------------------------------+              +------------------------------+                  |
|    | food_management_surpluslisting|              | food_management_ngorequirement|                 |
|    +------------------------------+              +------------------------------+                  |
|              │ 1                                            │                                      |
|              │                                              │                                      |
|              │ 1:N (listing_id)                             │                                      |
|              ▼                                              │                                      |
|    +---------------------------------+                      │                                      |
|    | food_management_donationrequest | <────────────────────┘                                      |
|    +---------------------------------+                                                             |
|                                                                                                    |
|    +------------------------------+                                                                |
|    | food_management_inventoryitem|                                                                |
|    +------------------------------+                                                                |
+----------------------------------------------------------------------------------------------------+
```

---

## 2. Table Specifications

### 2.1 `core_userprofile` (User Extension)
Stores organization profile data, roles, and gamification points.
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | BigAutoField | Primary Key | Auto-incrementing identifier |
| `user_id` | ForeignKey (`auth_user`) | Unique, On Delete CASCADE | Links to Django auth user |
| `role` | VARCHAR(20) | Choices: `business`, `ngo`, `admin` | System authorization role |
| `organization_name`| VARCHAR(200) | Blankable | Legal or trade entity name |
| `phone_number` | VARCHAR(20) | Blankable | Contact phone number |
| `address` | TEXT | Blankable | Physical facility location |
| `points` | INTEGER | Default: 0 | Gamification impact score |
| `level` | INTEGER | Default: 1 | Gamification level ($1 + \lfloor\text{points}/100\rfloor$) |
| `streak_days` | INTEGER | Default: 0 | Consecutive days of rescue activity |
| `badges` | JSONField | Default: `list` | Earned merit achievements |

### 2.2 `food_management_inventoryitem`
Tracks commercial food inventory batches on site.
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | BigAutoField | Primary Key | Auto-incrementing identifier |
| `name` | VARCHAR(150) | NOT NULL | Item name (e.g. Greek Yogurt 500g) |
| `category` | VARCHAR(100) | NOT NULL | Product category |
| `quantity` | DECIMAL(10,2) | Default: 0, Min: 0.01 | On-hand quantity |
| `unit` | VARCHAR(30) | Default: 'kg' | Unit of measurement (kg, litres, etc.) |
| `purchase_date`| DATE | NOT NULL | Acquisition / production date |
| `expiry_date` | DATE | NOT NULL, Indexed | Best-before / expiry date |
| `storage_location`| VARCHAR(200)| Default: 'Main storage' | Storage facility / shelf |
| `risk_level` | VARCHAR(20) | Choices: `low`, `medium`, `high`, `critical` | Dynamic spoilage risk classification |
| `notes` | TEXT | Blankable | Storage directives & packaging |

### 2.3 `food_management_surpluslisting`
Commercial surplus inventory made available for immediate rescue.
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | BigAutoField | Primary Key | Auto-incrementing identifier |
| `business_id` | ForeignKey (`auth_user`) | Nullable, On Delete SET_NULL | Donor business entity |
| `food_name` | VARCHAR(150) | NOT NULL | Description of surplus package |
| `category` | VARCHAR(100) | NOT NULL | Category (Produce, Dairy, etc.) |
| `quantity` | DECIMAL(10,2) | Default: 0, Min: 0.01 | Total batch quantity offered |
| `unit` | VARCHAR(30) | Default: 'kg' | Measurement unit |
| `expiry_date` | DATE | NOT NULL, Indexed | Consumption deadline |
| `pickup_location`| VARCHAR(250)| NOT NULL | Address for volunteer pickup |
| `availability_window`| VARCHAR(200)| Default: 'Today' | Time window available for handoff |
| `status` | VARCHAR(20) | Choices: `available`, `reserved`, `collected`, `cancelled` | Lifecycle state |
| `notes` | TEXT | Blankable | Packaging and temperature notes |

### 2.4 `food_management_ngorequirement`
Registered food demand from community kitchens and relief shelters.
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | BigAutoField | Primary Key | Auto-incrementing identifier |
| `ngo_user_id` | ForeignKey (`auth_user`) | Nullable, On Delete CASCADE | Submitting NGO representative |
| `ngo_name` | VARCHAR(200) | NOT NULL | Recipient organization |
| `category` | VARCHAR(100) | NOT NULL | Desired food category |
| `quantity_needed`| DECIMAL(10,2)| NOT NULL, Min: 0.01 | Target quantity required |
| `unit` | VARCHAR(30) | Default: 'kg' | Unit of measure |
| `urgency` | VARCHAR(20) | Choices: `low`, `medium`, `urgent` | Fulfillment priority |
| `location` | VARCHAR(250) | Blankable | Target service neighborhood |
| `status` | VARCHAR(20) | Choices: `open`, `partially_fulfilled`, `fulfilled`, `cancelled` | Fulfillment status |
| `fulfilled_quantity`| DECIMAL(10,2)| Default: 0 | Quantity delivered to date |

### 2.5 `food_management_donationrequest`
Atomic transfer claim, scheduling, and verified collection record.
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | BigAutoField | Primary Key | Auto-incrementing identifier |
| `listing_id` | ForeignKey (`SurplusListing`)| On Delete CASCADE, related: `requests` | Claimed surplus package |
| `ngo_user_id` | ForeignKey (`auth_user`) | Nullable, On Delete SET_NULL | Claimant representative |
| `ngo_name` | VARCHAR(200) | NOT NULL | Claiming organization name |
| `requested_quantity`| DECIMAL(10,2)| NOT NULL, Min: 0.01 | Claimed mass / volume |
| `pickup_date` | DATE | NOT NULL | Scheduled collection date |
| `pickup_time_slot`| VARCHAR(100)| Default: 'Morning (9:00 - 12:00)' | Agreed handoff time window |
| `pickup_code` | VARCHAR(10) | Auto-generated: `RC-XXXX` | 4-digit PIN required upon arrival |
| `status` | VARCHAR(20) | Choices: `requested`, `approved`, `scheduled`, `collected`, `cancelled` | State machine status |
| `cancellation_reason`| TEXT | Blankable | Reason logged if cancelled |
| `completed_at`| DATETIME | Nullable | Confirmed timestamp of collection |

---

## 3. Concurrency Protection & Transaction Integrity

To eliminate race conditions (such as two NGOs attempting to claim the final 10 kg simultaneously), claims are processed inside an atomic transaction with row-level locking:

```python
with transaction.atomic():
    # Row lock on the target listing prevents concurrent updates
    listing = SurplusListing.objects.select_for_update().get(pk=listing_id)
    
    if listing.is_expired():
        raise ValidationError("This lot has expired.")
    if listing.status in ['cancelled', 'collected']:
        raise ValidationError(f"This lot is {listing.status}.")
    if requested_qty > listing.remaining_quantity:
        raise ValidationError(f"Insufficient stock ({listing.remaining_quantity} available).")
        
    donation = form.save(commit=False)
    donation.save()
    
    # If remaining stock depleted, set to reserved
    if listing.remaining_quantity <= 0:
        listing.status = 'reserved'
        listing.save()
```
