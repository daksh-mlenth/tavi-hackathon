-- Initialize the database with extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create enum types
CREATE TYPE work_order_status AS ENUM (
    'submitted',
    'discovering_vendors',
    'contacting_vendors',
    'evaluating_quotes',
    'awaiting_approval',
    'dispatched',
    'in_progress',
    'completed',
    'cancelled'
);

CREATE TYPE trade_type AS ENUM (
    'plumbing',
    'electrical',
    'hvac',
    'landscaping',
    'roofing',
    'painting',
    'carpentry',
    'cleaning',
    'pest_control',
    'general_maintenance'
);

CREATE TYPE communication_channel AS ENUM (
    'email',
    'sms',
    'phone',
    'system'
);

CREATE TYPE quote_status AS ENUM (
    'pending',
    'received',
    'accepted',
    'rejected',
    'expired'
);

CREATE TYPE work_type AS ENUM (
    'reactive',
    'preventive',
    'other'
);

CREATE TYPE priority AS ENUM (
    'none',
    'low',
    'medium',
    'high'
);

CREATE TYPE category AS ENUM (
    'damage',
    'electrical',
    'inspection',
    'mechanical',
    'preventive',
    'project',
    'refrigeration',
    'safety',
    'standard_operating_procedure'
);

CREATE TYPE recurrence AS ENUM (
    'none',
    'daily',
    'weekly',
    'monthly',
    'quarterly',
    'yearly'
);
