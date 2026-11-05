-- ==============================================================================
-- CypherLabelGuard v2.0 - Supabase Schema Setup Script
-- Copy all of this code, paste it into Supabase SQL Editor, and click "Run".
-- ==============================================================================

-- 1. UUID Extension enable karein
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. Users Table: Agar pehle se bani hui hai to missing columns add karein, 
-- warna nayi table create karein (Existing data safe rahega)
CREATE TABLE IF NOT EXISTS public.users (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL DEFAULT '!clerk-managed',
    full_name VARCHAR(100) NOT NULL DEFAULT 'King Ghazi',
    role VARCHAR(50) NOT NULL DEFAULT 'User',
    workspace_name VARCHAR(100) NOT NULL DEFAULT 'Ghazi Workspace',
    credits_balance INTEGER DEFAULT 500,
    stripe_customer_id VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Agar table pehle se kisi aur app ki bani hui thi, to CypherLabelGuard ke columns safely add karein:
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='users' AND column_name='id') THEN
        ALTER TABLE public.users ADD COLUMN id VARCHAR(36) DEFAULT uuid_generate_v4()::text;
        UPDATE public.users SET id = uuid_generate_v4()::text WHERE id IS NULL;
        ALTER TABLE public.users ALTER COLUMN id SET NOT NULL;
        ALTER TABLE public.users ADD CONSTRAINT users_id_unique UNIQUE (id);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='hashed_password') THEN
        ALTER TABLE public.users ADD COLUMN hashed_password VARCHAR(255) DEFAULT '!clerk-managed';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='full_name') THEN
        ALTER TABLE public.users ADD COLUMN full_name VARCHAR(100) DEFAULT 'King Ghazi';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='role') THEN
        ALTER TABLE public.users ADD COLUMN role VARCHAR(50) DEFAULT 'User';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='workspace_name') THEN
        ALTER TABLE public.users ADD COLUMN workspace_name VARCHAR(100) DEFAULT 'Ghazi Workspace';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='credits_balance') THEN
        ALTER TABLE public.users ADD COLUMN credits_balance INTEGER DEFAULT 500;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='stripe_customer_id') THEN
        ALTER TABLE public.users ADD COLUMN stripe_customer_id VARCHAR(100);
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_users_email ON public.users(email);

-- 3. Payment Methods Table
CREATE TABLE IF NOT EXISTS public.payment_methods (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    user_id VARCHAR(36) NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    stripe_payment_method_id VARCHAR(100),
    card_brand VARCHAR(50) NOT NULL DEFAULT 'visa',
    last4 VARCHAR(4) NOT NULL,
    exp_month INTEGER NOT NULL,
    exp_year INTEGER NOT NULL,
    cardholder_name VARCHAR(100) NOT NULL DEFAULT 'King Ghazi',
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_payment_methods_user_id ON public.payment_methods(user_id);

-- 4. Subscriptions Table
CREATE TABLE IF NOT EXISTS public.subscriptions (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    user_id VARCHAR(36) NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    plan_name VARCHAR(50) NOT NULL DEFAULT 'Core',
    monthly_price DOUBLE PRECISION NOT NULL DEFAULT 129.00,
    status VARCHAR(50) NOT NULL DEFAULT 'Active',
    stripe_subscription_id VARCHAR(100),
    current_period_start TIMESTAMPTZ DEFAULT NOW(),
    current_period_end TIMESTAMPTZ DEFAULT NOW(),
    cancel_at_period_end BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON public.subscriptions(user_id);

-- 5. Transactions / Invoices Table
CREATE TABLE IF NOT EXISTS public.transactions (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    user_id VARCHAR(36) NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    invoice_number VARCHAR(50) UNIQUE NOT NULL,
    description VARCHAR(255) NOT NULL,
    amount DOUBLE PRECISION NOT NULL,
    currency VARCHAR(10) DEFAULT 'USD',
    status VARCHAR(50) DEFAULT 'Paid',
    stripe_charge_id VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON public.transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_transactions_invoice ON public.transactions(invoice_number);

-- 6. Folder Records Table
CREATE TABLE IF NOT EXISTS public.folder_records (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    name VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_folder_records_name ON public.folder_records(name);

-- 7. Job Records Table
CREATE TABLE IF NOT EXISTS public.job_records (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    user_id VARCHAR(36) NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    job_number VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    modality VARCHAR(50) NOT NULL DEFAULT 'Text',
    status VARCHAR(50) NOT NULL DEFAULT 'Completed',
    progress INTEGER DEFAULT 100,
    labels_count INTEGER DEFAULT 1,
    cost VARCHAR(20) DEFAULT '$0.01',
    consensus_label VARCHAR(100) DEFAULT 'CONFIRMED',
    affirmative_votes INTEGER DEFAULT 32,
    trace_id VARCHAR(100),
    lineage_hash VARCHAR(64),
    image_url TEXT,
    criteria_json TEXT,
    annotations_json TEXT,
    folder_name VARCHAR(100) DEFAULT 'General Workspace',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_job_records_user_id ON public.job_records(user_id);
CREATE INDEX IF NOT EXISTS idx_job_records_job_number ON public.job_records(job_number);

-- 8. Audit Log Entries Table
CREATE TABLE IF NOT EXISTS public.audit_log_entries (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    user_id VARCHAR(36) NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    action VARCHAR(150) NOT NULL,
    details TEXT,
    ip_address VARCHAR(50) DEFAULT '127.0.0.1',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON public.audit_log_entries(user_id);

-- 9. Default Workspace Folder insert karein
INSERT INTO public.folder_records (name)
VALUES ('General Workspace')
ON CONFLICT (name) DO NOTHING;

-- ==============================================================================
-- SUCCESS: Schema ready! All tables and indexes are configured.
-- ==============================================================================
