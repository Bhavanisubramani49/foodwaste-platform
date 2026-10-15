# AI-Powered Food Waste Management Platform
### For Surplus Identification & Redistribution Optimization
**Infosys Virtual Internship 7.0 — Batch 4 (AI Domain)** · *Milestone 1 Submission*

---

## 📌 Project Overview

The **AI-Powered Food Waste Management Platform** is a full-stack, responsive web application engineered to minimize food waste across commercial food establishments (restaurants, supermarkets, caterers, food retailers) and streamline surplus food redistribution to NGOs and community kitchens.

By unifying real-time inventory tracking, intelligent shelf-life and expiry risk analysis, surplus food listings, and pickup scheduling into a single responsive platform, it creates a sustainable, tech-driven food recovery ecosystem.

---

## 🚀 Key Features (Milestone 1 Deliverables)

### 1. Foundation & Multi-Role Architecture
- **Django Core Architecture:** Structured into modular applications (`core`, `food_management`, `config`).
- **Role-Based Access Control (RBAC):**
  - **Food Provider / Business:** Manage inventory, track expiry dates, monitor waste risk, and publish surplus listings.
  - **NGO / Community Kitchen:** Discover available surplus donations, submit donation requests, and track pickups.
  - **System Administrator:** Oversee system data, user profiles, and manage operations through the Django Admin interface.
- **Custom User Profiles:** Built-in gamification profile tracking (points, levels, streaks, and achievement badges).

### 2. Core Inventory Management
- **Full Inventory Lifecycle:** Complete CRUD operations (Add, View, Edit, Delete) restricted to authenticated business accounts.
- **Detailed Tracking:** Records food name, category, quantity, unit (kg, liters, units, boxes, etc.), purchase date, expiry date, storage location, and operational notes.
- **Automated Waste-Risk Scoring:** Dynamic risk-level evaluation (`low`, `medium`, `high`, `critical`) based on shelf-life remaining, volume, and storage condition.

### 3. Surplus Food Redistribution Workflow
- **Surplus Food Listings:** Providers can convert near-expiry stock into public or NGO-facing surplus food donations with pickup windows and location details.
- **Donation Request System:** NGOs can browse available surplus listings and submit requests with specified pickup dates and requested quantities.
- **Status Pipeline:** Real-time request tracking across `Requested` ➔ `Scheduled` ➔ `Collected` ➔ `Cancelled` stages.

### 4. Database & Cloud Architecture
- **Supabase PostgreSQL Support:** Configured for cloud PostgreSQL hosting on Supabase with SSL support (`psycopg3`), seamless connection pooling, and automated schema migration.
- **Local Fallback:** Automatic zero-config fallback to SQLite for quick offline testing and local development.
- **Security:** Complete separation of secrets using environment variables (`.env`).

### 5. Responsive UI / UX
- **Bootstrap 5 & Custom Modern Design:** Responsive layout optimized for smartphones, tablets, and desktop workstations.
- **Interactive Dashboards:** Visual KPI metrics, quick actions, and data tables.

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Backend Framework** | Django 5.x (Python) |
| **Database** | PostgreSQL (Supabase) / SQLite (Local dev) |
| **Frontend** | HTML5, Vanilla CSS, Bootstrap 5, Bootstrap Icons |
| **Authentication & RBAC** | Django Auth & Custom `UserProfile` with role-based routing |
| **Configuration** | `python-dotenv` for secure environment variable management |
| **Upcoming ML/AI** | Prophet, Scikit-learn, LSTM (Demand forecasting & predictive waste scoring) |

---

## 📁 Repository Structure

```text
infosys-project/
├── config/                     # Core Django project configuration & settings
│   ├── settings.py             # Dual-engine database config (Supabase / SQLite)
│   ├── urls.py                 # Root URL routing
│   └── wsgi.py
├── core/                       # Core authentication & gamification profile app
│   ├── models.py               # UserProfile with RBAC (Business, NGO, Admin)
│   ├── views.py                # Register, login, logout, profile handlers
│   └── urls.py
├── food_management/            # Inventory, surplus & donation workflow app
│   ├── models.py               # InventoryItem, SurplusListing, DonationRequest
│   ├── forms.py                # Inventory, donation & listing forms
│   ├── views.py                # Dashboard, CRUD views, and request handlers
│   └── templates/              # App-specific HTML templates
├── static/                     # Static CSS, JS, and image assets
│   ├── css/theme.css           # Custom styling and design tokens
│   └── js/
├── templates/                  # Base layout & global templates
│   ├── base.html               # Responsive Bootstrap 5 navbar and layout
│   └── core/                   # Authentication & profile templates
├── PRD.md                      # Complete Product Requirements Document
├── requirements.txt            # Python dependencies
├── manage.py                   # Django management script
└── supabase_database_storage.sql # Supabase schema & storage definitions
```

---

## ⚡ Getting Started Locally

### 1. Prerequisites
- Python 3.10+ installed
- Git installed

### 2. Clone the Repository
```bash
git clone https://github.com/Yoge486/food_waste_management.git
cd food_waste_management
```

### 3. Create and Activate Virtual Environment
On Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

On macOS / Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Update `.env` with your Supabase credentials or leave empty to use the local SQLite database:
```ini
SECRET_KEY=your-django-secret-key
DEBUG=True

# Optional Supabase PostgreSQL configuration:
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your_supabase_db_password
DB_HOST=aws-0-region.pooler.supabase.com
DB_PORT=5432
```

### 6. Apply Migrations & Create Superuser
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### 7. Run the Development Server
```bash
python manage.py runserver
```
Visit **http://127.0.0.1:8000/** in your web browser. Access the Django admin at **http://127.0.0.1:8000/admin/**.

---

## 📅 Roadmap & Next Milestones

- [x] **Week 1 (Milestone 1 - Foundation & Core Inventory):**
  - Database schema & Supabase connection
  - Role-based registration, login, and user profiles
  - Inventory tracking with CRUD workflows
  - Responsive Bootstrap 5 UI and base layout
- [ ] **Week 2 (Milestone 1 - Enhancements):**
  - Advanced search, multi-criteria filtering, and pagination
  - Expiry alert notifications and live metric counters
  - Bulk CSV inventory import
  - Final responsive verification & demo preparation
- [ ] **Milestone 2 (AI & Analytics):**
  - Machine learning waste-risk prediction model
  - Demand forecasting with Prophet / Scikit-learn
  - Detailed analytics dashboards and reporting

---

## 📄 License
Developed for educational and demonstration purposes as part of the Infosys Virtual Internship 7.0.
