# Product Requirements Document (PRD)

**Version 1.0 · Infosys Virtual Internship 7.0 · AI Domain**

## AI-Powered Food Waste Management Platform for Surplus Identification and Redistribution Optimization

- **Project Type:** AI-powered responsive web application
- **Internship:** Infosys Virtual Internship 7.0 — Batch 4
- **Technology:** Django, Django Templates, HTML, CSS, Bootstrap 5, PostgreSQL, Python Machine Learning

---

## 1. Project Overview

The AI-Powered Food Waste Management Platform is a web-based application designed to reduce food waste by monitoring inventory, predicting potential waste, and connecting businesses with NGOs and community kitchens that can redistribute surplus food.

The platform provides separate dashboards for food providers and recipient organizations. It uses historical demand, inventory quantities, expiry dates, and food-related data to identify potential waste and recommend suitable actions.

The website must be responsive and accessible from laptops, tablets, and mobile phones.

## 2. Problem Statement

Restaurants, supermarkets, food retailers, and other food service businesses frequently waste food because of poor inventory management, inaccurate demand forecasting, and insufficient coordination with organizations that need surplus food.

At the same time, NGOs and community kitchens may struggle to identify available food donations and coordinate their collection.

The proposed platform addresses these challenges through centralized inventory tracking, AI-based waste prediction, surplus food listings, and donation coordination.

## 3. Project Objectives

- Track food inventory, quantities, and expiry dates.
- Identify food items that may become waste.
- Forecast demand and provide inventory recommendations.
- Connect businesses with nearby NGOs and community kitchens.
- Simplify surplus food listing, donation requests, and pickup scheduling.
- Measure food recovery and waste reduction.
- Provide a responsive interface for desktop and mobile users.
- Encourage consistent participation through gamification (points, badges, streaks, and leaderboards).

## 4. Target Users

### 4.1 Food Providers
Restaurants, supermarkets, grocery stores, and food service businesses that manage inventory and donate surplus food.

### 4.2 NGOs and Community Kitchens
Organizations that discover available food donations, request food, and coordinate pickups.

### 4.3 Administrators
Authorized administrators who manage users, monitor platform activity, and maintain data quality.

## 5. Functional Requirements

### Module 1: Inventory Management and Expiry Tracking
- Allow authorized businesses to add, view, edit, and remove inventory records.
- Store food name, category, quantity, unit, purchase date, and expiry date.
- Display inventory in a searchable and filterable table.
- Identify food items approaching their expiry dates.
- Provide expiry notifications and warnings.
- Support manual inventory entry and CSV import.
- Design the data model to support future barcode or QR scanning and POS integration.

### Module 2: AI-Based Waste Prediction
- Collect relevant inventory, sales, demand, and waste data.
- Clean and preprocess historical datasets.
- Calculate a preliminary waste-risk score using expiry, stock quantity, and demand information.
- Develop a forecasting model using an appropriate method, such as Prophet or LSTM, when sufficient data is available.
- Display predicted demand and waste-risk levels.
- Provide recommendations for reducing overstock and preventing waste.
- Expose prediction functionality through a Python service or integrated backend module.

> **Important:** Initial predictions may use transparent rule-based logic while historical data is being collected. Machine-learning predictions must be evaluated before being presented as reliable forecasts.

### Module 3: Surplus Food Redistribution
- Allow businesses to list available surplus food.
- Record food category, quantity, expiry or use-by information, pickup location, and availability window.
- Display available donations to eligible recipient organizations.
- Match potential recipients using food type, quantity, location, and availability.
- Allow NGOs to request donations.
- Provide donation status tracking.
- Support pickup scheduling and collection confirmation.

> Food safety and eligibility checks must be applied before a donation is confirmed.

### Module 4: Dashboards and Analytics

**Business dashboard**
- Total inventory items.
- Items nearing expiry.
- High-risk inventory.
- Available surplus food listings.
- Donation history and inventory trends.

**NGO dashboard**
- Available food donations.
- Requested and confirmed donations.
- Scheduled pickups.
- Completed collections.

**Impact dashboard**
- Quantity of food redistributed.
- Donation trends over time.
- Estimated food waste avoided, when supported by a documented calculation method.

### Module 5: Authentication and Access Control
- Provide user registration and login.
- Support business, NGO, and administrator roles.
- Restrict pages and actions based on user permissions.
- Protect private user and business data.
- Use Django authentication and permission mechanisms.

### Module 6: Gamification and Engagement
- Award points for meaningful actions, such as keeping inventory updated, resolving high-risk items before expiry, publishing surplus listings, and completing donations.
- NGOs earn points for timely pickups and confirmed collections.
- Provide badges for milestones (for example, First Donation, Zero-Waste Week, 100 kg Recovered).
- Track activity streaks (for example, consecutive days of inventory updates).
- Provide levels based on accumulated points.
- Display leaderboards for businesses and NGOs, with an option to be shown by organization name or anonymously.
- Support time-limited challenges (for example, "Reduce expiring stock by 20% this month").
- Show a progress card on each dashboard with current points, level, streak, and next badge.
- Show gamification progress on the Impact dashboard.

> **Fairness and safety rules:** Points for donations are awarded only after collection is confirmed, not when a listing is published. Points must never reward listing unsafe or expired food, and food safety checks always take priority over engagement features. Point rules and formulas must be documented and configurable by administrators.

## 6. Responsive UI/UX Requirements

The platform must work on desktop, tablet, and mobile screens.

**Desktop**
- Expanded navigation or sidebar.
- Multi-column dashboard cards.
- Charts and detailed inventory tables.
- Easy access to all major modules.

**Tablet**
- Flexible grid layouts.
- Compact navigation.
- Readable tables and charts.

**Mobile**
- Single-column layouts where appropriate.
- Collapsible navigation.
- Touch-friendly buttons and form fields.
- Readable text without horizontal page overflow.
- Inventory tables that adapt to small screens.
- Forms that fit the viewport.
- Accessible alerts and clear status indicators.

> **Implementation:** Use Bootstrap 5 responsive containers, grid classes, breakpoints, and responsive utilities. Test layouts at mobile, tablet, and desktop widths.

## 7. Non-Functional Requirements

**Performance**
- Pages should load efficiently under normal project-demo conditions.
- Database queries should avoid unnecessary repeated work.
- Large datasets should use pagination where appropriate.

**Security**
- Validate user inputs on the server.
- Apply authentication and role-based permissions.
- Protect forms against CSRF attacks.
- Store secrets in environment variables.
- Use secure configuration for production deployment.

**Usability**
- Use consistent navigation, readable typography, and clear feedback.
- Provide validation messages and useful empty states.
- Ensure core workflows are understandable to first-time users.

**Maintainability**
- Use modular Django applications.
- Keep templates, static files, models, forms, and views organized.
- Track code changes using Git and GitHub.

## 8. Proposed Technology Stack

| Layer | Technology |
|---|---|
| Frontend | HTML5, CSS3, JavaScript |
| Responsive UI | Bootstrap 5 |
| Template rendering | Django Templates |
| Backend | Python and Django |
| Database | PostgreSQL |
| Authentication | Django Authentication |
| Data processing | Pandas and NumPy |
| Machine learning | Scikit-learn; Prophet or LSTM where appropriate |
| Version control | Git and GitHub |
| Deployment | A suitable cloud hosting platform |

The first implementation will use Django Templates instead of a separate React frontend. This keeps the architecture simpler for a beginner and supports responsive pages without requiring a separate frontend application.

## 9. Proposed Database Entities

**User**
- User ID, Name, Email
- Password hash managed by Django
- Role
- Organization details

**Food Inventory**
- Inventory ID, Business ID
- Food name, Food category
- Quantity and unit
- Purchase date, Expiry date
- Storage information
- Created and updated timestamps

**Waste Prediction**
- Prediction ID
- Inventory ID or business reference
- Prediction date
- Waste-risk score, Risk category
- Forecasted demand
- Recommendation
- Model version

**Surplus Listing**
- Listing ID, Business ID
- Food details
- Available quantity
- Pickup location
- Availability window
- Listing status

**Donation Request**
- Request ID
- Surplus listing ID, NGO ID
- Requested quantity
- Pickup schedule
- Request and collection status

**Gamification Profile**
- Profile ID, User or Organization ID
- Total points, Current level
- Current streak, Longest streak

**Points Transaction**
- Transaction ID, Profile ID
- Action type (for example, donation completed, inventory updated)
- Points awarded
- Related object reference (listing or request)
- Timestamp

**Badge and User Badge**
- Badge ID, Name, Description, Criteria
- User Badge: Profile ID, Badge ID, Date earned

**Challenge**
- Challenge ID, Title, Description
- Target metric and target value
- Start date, End date
- Reward points or badge

## 10. Project Development Plan

**Weeks 1–2: Inventory Management and Expiry Tracking**
- Finalize requirements and database design.
- Create the Django project and core applications.
- Implement inventory entry and listing.
- Add expiry alerts.
- Add CSV import support.
- Prepare for future barcode and POS integration.

**Weeks 3–4: AI-Based Waste Prediction**
- Prepare historical inventory and demand data.
- Implement preprocessing and exploratory analysis.
- Create an initial waste-risk scoring system.
- Develop and evaluate forecasting models.
- Integrate prediction results into the backend.

**Weeks 5–6: Redistribution and Analytics**
- Implement surplus food listings.
- Build NGO donation-request workflows.
- Develop recipient matching and pickup scheduling.
- Create business and NGO dashboards.
- Add food recovery analytics.
- Implement gamification: points, badges, streaks, levels, leaderboard, and challenges.
- Prepare the application for cloud deployment.

**Weeks 7–8: Integration, Testing, and Finalization**
- Test end-to-end workflows.
- Validate responsive behavior across browsers and screen sizes.
- Test permissions, input validation, and error handling.
- Evaluate prediction quality.
- Fix defects and improve usability.
- Prepare documentation, presentation slides, and project demonstration.

## 11. Acceptance Criteria

The project will be considered ready for demonstration when:

1. A business user can log in and manage food inventory.
2. Inventory records are saved in PostgreSQL.
3. The system identifies items approaching expiry.
4. The dashboard displays understandable waste-risk information.
5. A business can publish a surplus food listing.
6. An NGO can view and request an available donation.
7. Donation and pickup statuses can be tracked.
8. Dashboard statistics reflect stored application data.
9. Core pages adapt correctly to mobile, tablet, and laptop screens.
10. Authentication, authorization, and form validation work correctly.
11. Core workflows pass functional testing.
12. Users earn points and badges for completed actions, and points appear on their dashboard.
13. The leaderboard and streaks reflect stored application data.
14. Donation points are awarded only after collection is confirmed.
15. The project includes setup instructions, documentation, and a working demonstration.

## 12. Risks and Mitigation

| Risk | Mitigation |
|---|---|
| Insufficient historical data | Begin with transparent rule-based risk scoring and use an appropriate dataset to evaluate machine-learning models. |
| Incorrect predictions | Measure model performance and explain that predictions are estimates rather than guarantees. |
| Food safety concerns | Include expiry and handling checks, and require appropriate confirmation before a donation is completed. |
| Responsive layout issues | Test pages at multiple screen sizes throughout development. |
| Integration delays | Develop and test each module independently before full integration. |
| Data security | Apply Django permissions, validation, CSRF protection, and secure deployment settings. |
| Gamification encourages unsafe or fake activity | Award donation points only after confirmed collection, keep food safety checks mandatory, and let administrators review unusual point activity. |

## 13. Future Enhancements

- Barcode and QR-based inventory entry.
- POS system integration.
- Email or SMS expiry notifications.
- Geolocation-based NGO matching.
- Route optimization for food pickup.
- Advanced demand forecasting.
- Multilingual interface.
- Mobile application integration.

## 14. Expected Outcome

The expected outcome is a functional, responsive web platform that helps businesses monitor food inventory, identify potential waste, redistribute surplus food to suitable organizations, and understand the impact of their recovery activities.

The project combines Django-based web development, PostgreSQL data management, responsive design, and AI-based forecasting to support more efficient food resource utilization.
