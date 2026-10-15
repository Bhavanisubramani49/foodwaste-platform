# Start Guide

This project is a Django-based food waste management app based on the PRD.

## 1. Create and activate the virtual environment

```bash
cd d:\infosys-project
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
pip install django
```

## 2. Run database setup

```bash
python manage.py makemigrations
python manage.py migrate
```

## 3. Start the server

```bash
python manage.py runserver
```

Then open:
- http://127.0.0.1:8000/

## 4. Main features implemented in the starter build

- Dashboard with KPI cards and impact summary
- Inventory entry, search, filtering, edit, and delete actions
- Surplus food listing page with posting workflow
- Donation request workflow with status tracking and updates
- Leaderboard and gamification profile tracking
- Responsive Bootstrap layout
- Django admin integration for data management

## 5. Admin access

```bash
python manage.py createsuperuser
```

Then login at:
- http://127.0.0.1:8000/admin/

## 6. Project structure

- food_waste_manager/ - Django project
- food_management/ - app containing models, views, templates, and forms

## 7. Next steps

- add authentication and user roles
- implement AI-based waste prediction
- build CSV import and analytics
- add gamification and dashboards
