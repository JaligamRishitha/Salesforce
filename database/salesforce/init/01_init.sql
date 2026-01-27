-- Salesforce CRM Database Initialization Script
-- PostgreSQL 16

-- Enable UUID extension for generating UUIDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- CORE CRM TABLES
-- =============================================================================

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    role VARCHAR(20) DEFAULT 'user',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Accounts table (Companies/Organizations)
CREATE TABLE IF NOT EXISTS accounts (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    industry VARCHAR(100),
    website VARCHAR(255),
    phone VARCHAR(50),
    billing_address TEXT,
    shipping_address TEXT,
    description TEXT,
    annual_revenue DECIMAL(15, 2),
    number_of_employees INTEGER,
    owner_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Contacts table
CREATE TABLE IF NOT EXISTS contacts (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    phone VARCHAR(50),
    mobile VARCHAR(50),
    title VARCHAR(100),
    department VARCHAR(100),
    account_id INTEGER REFERENCES accounts(id),
    owner_id INTEGER REFERENCES users(id),
    mailing_address TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Leads table
CREATE TABLE IF NOT EXISTS leads (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100) NOT NULL,
    company VARCHAR(255),
    title VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(50),
    mobile VARCHAR(50),
    website VARCHAR(255),
    lead_source VARCHAR(100),
    status VARCHAR(50) DEFAULT 'New',
    industry VARCHAR(100),
    annual_revenue DECIMAL(15, 2),
    number_of_employees INTEGER,
    rating VARCHAR(20),
    description TEXT,
    address TEXT,
    owner_id INTEGER REFERENCES users(id),
    is_converted BOOLEAN DEFAULT FALSE,
    converted_date TIMESTAMP,
    converted_account_id INTEGER REFERENCES accounts(id),
    converted_contact_id INTEGER REFERENCES contacts(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Opportunities table
CREATE TABLE IF NOT EXISTS opportunities (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    account_id INTEGER REFERENCES accounts(id),
    amount DECIMAL(15, 2),
    close_date DATE,
    stage VARCHAR(50) DEFAULT 'Prospecting',
    probability INTEGER DEFAULT 0,
    type VARCHAR(50),
    lead_source VARCHAR(100),
    next_step VARCHAR(255),
    description TEXT,
    owner_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Cases table (Customer Support)
CREATE TABLE IF NOT EXISTS cases (
    id SERIAL PRIMARY KEY,
    case_number VARCHAR(50) UNIQUE NOT NULL,
    subject VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'New',
    priority VARCHAR(20) DEFAULT 'Medium',
    origin VARCHAR(50),
    type VARCHAR(50),
    reason VARCHAR(100),
    account_id INTEGER REFERENCES accounts(id),
    contact_id INTEGER REFERENCES contacts(id),
    owner_id INTEGER REFERENCES users(id),
    escalated BOOLEAN DEFAULT FALSE,
    escalation_reason TEXT,
    resolution TEXT,
    resolution_date TIMESTAMP,
    sla_violation BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Activities table
CREATE TABLE IF NOT EXISTS activities (
    id SERIAL PRIMARY KEY,
    type VARCHAR(50) NOT NULL,
    subject VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'Open',
    priority VARCHAR(20) DEFAULT 'Normal',
    due_date TIMESTAMP,
    completed_date TIMESTAMP,
    related_to_type VARCHAR(50),
    related_to_id INTEGER,
    owner_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- SERVICE MANAGEMENT TABLES
-- =============================================================================

-- Service Level Agreements
CREATE TABLE IF NOT EXISTS service_level_agreements (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    response_time_hours INTEGER,
    resolution_time_hours INTEGER,
    priority VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Service Accounts (Warranty & Service Contracts)
CREATE TABLE IF NOT EXISTS service_accounts (
    id SERIAL PRIMARY KEY,
    account_id INTEGER REFERENCES accounts(id),
    service_type VARCHAR(100),
    warranty_start_date DATE,
    warranty_end_date DATE,
    service_level VARCHAR(50),
    sla_id INTEGER REFERENCES service_level_agreements(id),
    status VARCHAR(50) DEFAULT 'Active',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Quotations
CREATE TABLE IF NOT EXISTS quotations (
    id SERIAL PRIMARY KEY,
    quote_number VARCHAR(50) UNIQUE NOT NULL,
    opportunity_id INTEGER REFERENCES opportunities(id),
    account_id INTEGER REFERENCES accounts(id),
    contact_id INTEGER REFERENCES contacts(id),
    total_amount DECIMAL(15, 2),
    discount_percent DECIMAL(5, 2),
    tax_amount DECIMAL(15, 2),
    grand_total DECIMAL(15, 2),
    valid_until DATE,
    status VARCHAR(50) DEFAULT 'Draft',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Invoices
CREATE TABLE IF NOT EXISTS invoices (
    id SERIAL PRIMARY KEY,
    invoice_number VARCHAR(50) UNIQUE NOT NULL,
    account_id INTEGER REFERENCES accounts(id),
    contact_id INTEGER REFERENCES contacts(id),
    quote_id INTEGER REFERENCES quotations(id),
    total_amount DECIMAL(15, 2),
    tax_amount DECIMAL(15, 2),
    grand_total DECIMAL(15, 2),
    due_date DATE,
    paid_date DATE,
    status VARCHAR(50) DEFAULT 'Draft',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- PLATFORM EVENTS & AUDIT
-- =============================================================================

-- Audit Log
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(50) NOT NULL,
    object_type VARCHAR(50),
    object_id INTEGER,
    old_values JSONB,
    new_values JSONB,
    ip_address VARCHAR(50),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Platform Events
CREATE TABLE IF NOT EXISTS platform_events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,
    event_source VARCHAR(100),
    payload JSONB,
    correlation_id UUID DEFAULT uuid_generate_v4(),
    status VARCHAR(50) DEFAULT 'Pending',
    processed_at TIMESTAMP,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Recent Records (User access tracking)
CREATE TABLE IF NOT EXISTS recent_records (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    object_type VARCHAR(50) NOT NULL,
    object_id INTEGER NOT NULL,
    object_name VARCHAR(255),
    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- INDEXES
-- =============================================================================

CREATE INDEX idx_accounts_owner ON accounts(owner_id);
CREATE INDEX idx_contacts_account ON contacts(account_id);
CREATE INDEX idx_contacts_owner ON contacts(owner_id);
CREATE INDEX idx_leads_owner ON leads(owner_id);
CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_opportunities_account ON opportunities(account_id);
CREATE INDEX idx_opportunities_stage ON opportunities(stage);
CREATE INDEX idx_cases_account ON cases(account_id);
CREATE INDEX idx_cases_status ON cases(status);
CREATE INDEX idx_cases_owner ON cases(owner_id);
CREATE INDEX idx_activities_owner ON activities(owner_id);
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_object ON audit_logs(object_type, object_id);
CREATE INDEX idx_platform_events_status ON platform_events(status);
CREATE INDEX idx_platform_events_correlation ON platform_events(correlation_id);

-- =============================================================================
-- INITIAL DATA
-- =============================================================================

-- Insert default SLAs
INSERT INTO service_level_agreements (name, description, response_time_hours, resolution_time_hours, priority)
VALUES
    ('Critical SLA', 'For critical priority cases', 1, 4, 'Critical'),
    ('High SLA', 'For high priority cases', 4, 24, 'High'),
    ('Medium SLA', 'For medium priority cases', 8, 48, 'Medium'),
    ('Low SLA', 'For low priority cases', 24, 120, 'Low');

COMMENT ON DATABASE salesforce_crm IS 'Salesforce CRM Clone - Main Application Database';
