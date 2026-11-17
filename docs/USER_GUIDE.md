# FoodWasteAI – User Guide & Operational Manual

## 1. Introduction

Welcome to **FoodWasteAI**! This guide provides operational instructions tailored to each user role:
- **Commercial Food Businesses:** Restaurants, catering companies, bakeries, grocery stores.
- **Relief Organizations & NGOs:** Community kitchens, food banks, shelters, volunteer aid networks.
- **Platform Administrators:** Compliance auditors, system operators.

---

## 2. Business User Manual

### 2.1 Logging In & Dashboard Overview
1. Navigate to `/app/accounts/login/` and log in with your business credentials.
2. The **Operations Dashboard** (`/app/`) provides:
   - **Hero Metric Cards:** Food saved (kg), meals served, $\text{CO}_2$ avoided, and urgent batches.
   - **AI Waste Prediction:** Projected spoilage volume for the upcoming week based on decay models.
   - **Forecast vs Actual Redirection Chart:** Visualizing 7-day predicted demand with confidence corridors.
   - **AI Reorder Recommendation:** Automated recommendation on when and how much replenishment stock to purchase based on vendor lead times.

### 2.2 Managing Inventory Batches
1. **Add Fresh Batch:** Click `+ Log Batch` or go to `/app/inventory/add/`. Fill in product name, category, quantity, unit, purchase date, expiry date, and storage location.
2. **Review & Filter Inventory:** Go to `/app/inventory/`. You can filter items by search text or expiry risk level (`Critical < 24h`, `High < 7d`, `Medium < 14d`, `Low/Safe`).
3. **Bulk CSV Import:**
   - Download the template by clicking `Import CSV` $\to$ `Download Sample CSV`.
   - Upload your formatted `.csv` file. The platform imports batches and validates dates and positive quantities automatically.
4. **Edit / Delete Batches:** In the inventory table, click `Edit` to adjust stock counts or `Delete` to remove depleted records.

### 2.3 Posting Surplus Food to Marketplace
1. When excess stock is identified, click `+ Post Surplus Lot` on the dashboard or go to `/app/surplus/add/`.
2. Specify the food description, available quantity, pickup address, and availability window (e.g. `Today 6:00 PM - 9:00 PM`).
3. Click **Submit**. Your lot is immediately published to verified relief kitchens within a 5 km radius with an active 45-minute countdown clock.
4. **Cancelling a Lot:** If plans change before collection, business owners can click `Cancel Lot` on the marketplace page.

### 2.4 Verifying Pickup & Handing Off Food
1. Go to **Rescue Pipeline** (`/app/donations/`).
2. When the NGO driver arrives, ask for their **Pickup Verification PIN** (e.g. `RC-8429`).
3. Select status **Collected**, enter the driver's PIN in the input field, and click **Update**.
4. The system validates the code, marks the donation completed, and credits gamification points and streak badges to your profile.

---

## 3. NGO User Manual

### 3.1 NGO Command Center
1. Log in with your verified NGO credentials.
2. The platform automatically directs you to the **NGO Redistribution Command Center** (`/app/ngo/`):
   - **Active Dispatches:** Active claims in `Requested`, `Approved`, or `Scheduled` state with your unique Pickup PINs.
   - **Food Rescued & Meals Served:** Total volume delivered to your community kitchens.
   - **Smart Match Feed:** Top surplus allocations matching your food needs with compatibility scores ($80\%+$ Excellent Match).

### 3.2 Registering Community Food Requirements
1. Click `+ Post Food Requirement` or go to `/app/ngo/requirements/add/`.
2. Enter the food category needed (e.g. `Cooked Meals`, `Dairy`, `Bakery`), required quantity, urgency tier (`Urgent < 24h`, `Medium 2-3d`, `Low 7d`), and delivery area.
3. Click **Submit**. The matching engine immediately begins scoring active and incoming surplus listings against your need.
4. Once fulfilled, you can mark the requirement `Fulfilled` or `Cancel` it from `/app/ngo/requirements/`.

### 3.3 Claiming Surplus Lots
1. In the **Smart Match Feed** or **Surplus Marketplace** (`/app/surplus/`), click **Claim Lot**.
2. Select your pickup date and preferred time window.
3. Click **Confirm Allocation**.
4. Your unique **Pickup Verification PIN** (e.g. `RC-7294`) will be generated. Have your dispatch driver present this PIN upon arrival at the donor's kitchen.

---

## 4. Environmental Impact Analytics Dashboard

Accessible at `/app/impact/` to all platform participants:
- **Total Kilograms Diverted:** Verified cumulative weight of edible food rescued from landfills.
- **Nutritious Meals Provided:** Calculated at $2.22 \text{ meals/kg}$ diverted (USDA standard).
- **Greenhouse Gas Emissions Avoided:** Calculated at $2.5 \text{ kg } \text{CO}_2\text{e/kg}$ organic waste diverted.
- **Landfill Volume Saved:** Compaction density of $500 \text{ kg/m}^3$.
- **Economic Value Rescued:** Average commercial wholesale replacement value at ₹120 per kg.
- **Category & Partner Breakdown:** Charting the highest-volume diverted categories and participating kitchens.

---

## 5. Platform Administrator Manual

Accessible at `/app/admin-panel/` to users with `admin` role:
- **Tenant Management:** View all registered restaurant and NGO profiles.
- **Account Actions:** Suspend or reactivate user accounts involved in policy violations or malpractice.
- **Self-Suspension Guard:** Administrators cannot accidentally suspend or delete their own administrative accounts.
- **Audit Logging:** Review recent platform claims and compliance events across all tenants.
