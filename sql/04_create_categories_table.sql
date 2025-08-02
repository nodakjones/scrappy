-- Categories table for contractor service categories
-- This table stores the categories imported from data/categories.csv

CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    record_id VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    priority BOOLEAN DEFAULT FALSE,
    afb_name VARCHAR(100),
    category VARCHAR(100),
    modified_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_categories_name ON categories(name);
CREATE INDEX IF NOT EXISTS idx_categories_priority ON categories(priority);
CREATE INDEX IF NOT EXISTS idx_categories_record_id ON categories(record_id);

-- Apply updated_at trigger to categories table
CREATE TRIGGER update_categories_updated_at BEFORE UPDATE ON categories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column(); 