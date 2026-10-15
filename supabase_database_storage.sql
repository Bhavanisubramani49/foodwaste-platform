-- ==============================================================================
-- AI-Powered Food Waste Management & Surplus Redistribution Platform
-- Supabase PostgreSQL Database & Storage Setup Script
-- Compatible with Supabase SQL Editor and PostgreSQL 15+
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. EXTENSIONS
-- ------------------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ------------------------------------------------------------------------------
-- 2. APPLICATION TABLES (DDL)
-- ------------------------------------------------------------------------------

-- Table: Inventory Items (Module 1: Inventory & Expiry Tracking)
CREATE TABLE IF NOT EXISTS public.food_management_inventoryitem (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    category VARCHAR(100) NOT NULL,
    quantity NUMERIC(10, 2) NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    unit VARCHAR(30) NOT NULL DEFAULT 'kg',
    purchase_date DATE NOT NULL,
    expiry_date DATE NOT NULL,
    storage_location VARCHAR(200) NOT NULL DEFAULT 'Main storage',
    risk_level VARCHAR(20) NOT NULL DEFAULT 'low' CHECK (risk_level IN ('low', 'medium', 'high', 'critical')),
    notes TEXT DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for fast inventory search and expiry filtering
CREATE INDEX IF NOT EXISTS idx_inventory_expiry_date ON public.food_management_inventoryitem (expiry_date);
CREATE INDEX IF NOT EXISTS idx_inventory_risk_level ON public.food_management_inventoryitem (risk_level);
CREATE INDEX IF NOT EXISTS idx_inventory_category ON public.food_management_inventoryitem (category);


-- Table: Surplus Listings (Module 3: Surplus Food Redistribution)
CREATE TABLE IF NOT EXISTS public.food_management_surpluslisting (
    id BIGSERIAL PRIMARY KEY,
    food_name VARCHAR(150) NOT NULL,
    category VARCHAR(100) NOT NULL,
    quantity NUMERIC(10, 2) NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    unit VARCHAR(30) NOT NULL DEFAULT 'kg',
    expiry_date DATE NOT NULL,
    pickup_location VARCHAR(250) NOT NULL,
    availability_window VARCHAR(200) NOT NULL DEFAULT 'Today',
    status VARCHAR(20) NOT NULL DEFAULT 'available' CHECK (status IN ('available', 'reserved', 'collected', 'cancelled')),
    notes TEXT DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for surplus listings
CREATE INDEX IF NOT EXISTS idx_surplus_status ON public.food_management_surpluslisting (status);
CREATE INDEX IF NOT EXISTS idx_surplus_expiry ON public.food_management_surpluslisting (expiry_date);


-- Table: Donation Requests (Module 3: NGO Redistribution Workflow)
CREATE TABLE IF NOT EXISTS public.food_management_donationrequest (
    id BIGSERIAL PRIMARY KEY,
    listing_id BIGINT NOT NULL REFERENCES public.food_management_surpluslisting(id) ON DELETE CASCADE,
    ngo_name VARCHAR(200) NOT NULL,
    requested_quantity NUMERIC(10, 2) NOT NULL CHECK (requested_quantity > 0),
    pickup_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'requested' CHECK (status IN ('requested', 'scheduled', 'collected', 'cancelled')),
    notes TEXT DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for foreign key and status
CREATE INDEX IF NOT EXISTS idx_donation_listing_id ON public.food_management_donationrequest (listing_id);
CREATE INDEX IF NOT EXISTS idx_donation_status ON public.food_management_donationrequest (status);


-- Table: User Profile (Module 5: Role-based Authentication)
CREATE TABLE IF NOT EXISTS public.core_userprofile (
    id BIGSERIAL PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    role VARCHAR(20) NOT NULL DEFAULT 'business' CHECK (role IN ('business', 'ngo', 'admin')),
    organization_name VARCHAR(200) DEFAULT '',
    phone_number VARCHAR(30) DEFAULT '',
    address TEXT DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_userprofile_role ON public.core_userprofile (role);


-- ------------------------------------------------------------------------------
-- 3. SUPABASE STORAGE BUCKET CONFIGURATION
-- ------------------------------------------------------------------------------

-- Create public storage bucket for food item photos and inventory CSVs
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'food-storage',
    'food-storage',
    true,
    5242880, -- 5MB limit
    ARRAY['image/jpeg', 'image/png', 'image/webp', 'text/csv']
)
ON CONFLICT (id) DO UPDATE SET
    public = EXCLUDED.public,
    file_size_limit = EXCLUDED.file_size_limit,
    allowed_mime_types = EXCLUDED.allowed_mime_types;

-- RLS: Allow public read access to uploaded images in food-storage
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'objects' AND policyname = 'Public Access for food-storage'
    ) THEN
        CREATE POLICY "Public Access for food-storage"
        ON storage.objects FOR SELECT
        USING (bucket_id = 'food-storage');
    END IF;
END $$;

-- RLS: Allow authenticated / service users to upload files
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'objects' AND policyname = 'Allow Upload to food-storage'
    ) THEN
        CREATE POLICY "Allow Upload to food-storage"
        ON storage.objects FOR INSERT
        WITH CHECK (bucket_id = 'food-storage');
    END IF;
END $$;


-- ------------------------------------------------------------------------------
-- 4. ANALYTICAL STORAGE & MONITORING QUERIES
-- ------------------------------------------------------------------------------

-- Query 1: Inventory Storage Overview by Location and Risk Level
-- Use this query to see total stock stored in each storage area
SELECT 
    storage_location,
    COUNT(*) AS total_items,
    SUM(quantity) AS total_quantity,
    COUNT(CASE WHEN risk_level IN ('high', 'critical') THEN 1 END) AS high_risk_items,
    COUNT(CASE WHEN expiry_date <= CURRENT_DATE + INTERVAL '7 days' THEN 1 END) AS expiring_soon_items
FROM public.food_management_inventoryitem
GROUP BY storage_location
ORDER BY high_risk_items DESC;

-- Query 2: Active Surplus Redistribution Opportunities
-- Use this query to see all available surplus food ready for NGO claims
SELECT 
    s.id AS surplus_id,
    s.food_name,
    s.category,
    s.quantity,
    s.unit,
    s.expiry_date,
    s.pickup_location,
    s.availability_window,
    COALESCE(COUNT(d.id), 0) AS request_count
FROM public.food_management_surpluslisting s
LEFT JOIN public.food_management_donationrequest d ON s.id = d.listing_id
WHERE s.status = 'available'
GROUP BY s.id
ORDER BY s.expiry_date ASC;

-- Query 3: Food Waste Prevention & Environmental Impact
-- Calculates total food recovered and avoidance metrics
SELECT 
    COUNT(DISTINCT d.id) AS total_completed_donations,
    COALESCE(SUM(d.requested_quantity), 0) AS total_kg_food_recovered,
    ROUND(COALESCE(SUM(d.requested_quantity), 0) * 2.5, 2) AS estimated_co2_kg_avoided,
    ROUND(COALESCE(SUM(d.requested_quantity), 0) * 2.2, 0) AS estimated_meals_provided
FROM public.food_management_donationrequest d
WHERE d.status = 'collected';


-- ------------------------------------------------------------------------------
-- 5. SEED DATA (OPTIONAL - FOR QUICK TESTING)
-- ------------------------------------------------------------------------------
INSERT INTO public.food_management_inventoryitem 
    (name, category, quantity, unit, purchase_date, expiry_date, storage_location, risk_level, notes)
VALUES
    ('Organic Apples', 'Produce', 50.00, 'kg', CURRENT_DATE - INTERVAL '3 days', CURRENT_DATE + INTERVAL '4 days', 'Cold Room A', 'high', 'Batch #A-102'),
    ('Whole Grain Bread', 'Bakery', 25.00, 'units', CURRENT_DATE - INTERVAL '1 day', CURRENT_DATE + INTERVAL '2 days', 'Bakery Shelf 3', 'critical', 'Nearing shelf life'),
    ('Fresh Dairy Milk 1L', 'Dairy', 40.00, 'liters', CURRENT_DATE - INTERVAL '2 days', CURRENT_DATE + INTERVAL '5 days', 'Dairy Chiller', 'medium', 'Supplier batch #89'),
    ('Basmati Rice 5kg', 'Grains', 100.00, 'kg', CURRENT_DATE - INTERVAL '10 days', CURRENT_DATE + INTERVAL '180 days', 'Dry Pantry 1', 'low', 'Stable stock')
ON CONFLICT DO NOTHING;

INSERT INTO public.food_management_surpluslisting
    (food_name, category, quantity, unit, expiry_date, pickup_location, availability_window, status, notes)
VALUES
    ('Bakery Croissants & Baguettes', 'Bakery', 15.00, 'kg', CURRENT_DATE + INTERVAL '1 day', 'Metro Supermarket, Gate 2', 'Today 5:00 PM - 8:00 PM', 'available', 'Baked fresh this morning'),
    ('Assorted Farm Vegetables', 'Produce', 30.00, 'kg', CURRENT_DATE + INTERVAL '2 days', 'Green Grocers, 5th Ave', 'Tomorrow morning', 'available', 'Cosmetically imperfect but fresh')
ON CONFLICT DO NOTHING;
