-- Migration: Remove is_home_contractor column and use residential_focus instead
-- This migration removes the is_home_contractor column since we're now using residential_focus consistently

-- Drop indexes that reference is_home_contractor
DROP INDEX IF EXISTS idx_contractors_home_contractor;

-- Drop the is_home_contractor column
ALTER TABLE contractors DROP COLUMN IF EXISTS is_home_contractor;

-- Update any remaining references in JSONB fields
UPDATE contractors 
SET gpt4mini_analysis = gpt4mini_analysis - 'is_home_contractor'
WHERE gpt4mini_analysis ? 'is_home_contractor';

-- Verify the change
SELECT 
    COUNT(*) as total_contractors,
    COUNT(residential_focus) as with_residential_focus,
    COUNT(CASE WHEN residential_focus = true THEN 1 END) as residential_contractors,
    COUNT(CASE WHEN residential_focus = false THEN 1 END) as commercial_contractors
FROM contractors 
WHERE processing_status = 'completed'; 