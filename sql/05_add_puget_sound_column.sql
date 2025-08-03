-- Add puget_sound column to contractors table
-- Migration script for Puget Sound zip code filtering

-- Add the puget_sound column
ALTER TABLE contractors 
ADD COLUMN puget_sound BOOLEAN DEFAULT FALSE;

-- Create an index for efficient filtering
CREATE INDEX idx_contractors_puget_sound ON contractors(puget_sound);

-- Add a comment to document the column
COMMENT ON COLUMN contractors.puget_sound IS 'Boolean flag indicating if contractor is located in Puget Sound region based on zip code'; 