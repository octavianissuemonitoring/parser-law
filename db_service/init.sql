-- Initialize database schema
-- Acest script rulează automat la crearea containerului PostgreSQL

-- Create schema for legislatie
CREATE SCHEMA IF NOT EXISTS legislatie;

-- Set search path
SET search_path TO legislatie, public;

-- Grant permissions
GRANT ALL PRIVILEGES ON SCHEMA legislatie TO legislatie_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA legislatie TO legislatie_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA legislatie TO legislatie_user;

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";      -- For UUID generation
CREATE EXTENSION IF NOT EXISTS "pg_trgm";        -- For fuzzy text search
CREATE EXTENSION IF NOT EXISTS "unaccent";       -- For accent-insensitive search

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION legislatie.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE '✅ Schema legislatie initialized successfully';
END $$;
