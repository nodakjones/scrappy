-- Insert sample mailer categories for home contractors
-- This represents common contractor service categories

INSERT INTO mailer_categories (category_name, priority, afb_name, category, keywords, typical_services, sort_order) VALUES
('Plumbing', TRUE, 'Plumbing Services', 'Home Services', 
 ARRAY['plumber', 'pipes', 'drain', 'water heater', 'leak', 'sewer', 'faucet', 'toilet'],
 ARRAY['Drain cleaning', 'Water heater repair', 'Pipe repair', 'Leak detection', 'Bathroom fixtures'],
 1),

('HVAC', TRUE, 'Heating & Cooling', 'Home Services',
 ARRAY['heating', 'cooling', 'air conditioning', 'furnace', 'hvac', 'heat pump', 'duct'],
 ARRAY['AC repair', 'Furnace installation', 'Duct cleaning', 'Heat pump service'],
 2),

('Electrical', TRUE, 'Electrical Services', 'Home Services',
 ARRAY['electrician', 'wiring', 'electrical', 'panel', 'outlet', 'lighting', 'electrical repair'],
 ARRAY['Electrical repairs', 'Panel upgrades', 'Outlet installation', 'Lighting installation'],
 3),

('Roofing', TRUE, 'Roofing Contractors', 'Home Services',
 ARRAY['roofer', 'roofing', 'shingles', 'roof repair', 'gutters', 'siding'],
 ARRAY['Roof replacement', 'Roof repair', 'Gutter installation', 'Siding repair'],
 4),

('General Contractor', TRUE, 'General Construction', 'Home Services',
 ARRAY['general contractor', 'construction', 'remodeling', 'renovation', 'building'],
 ARRAY['Home remodeling', 'Room additions', 'Kitchen renovation', 'Bathroom remodel'],
 5),

('Handyman', TRUE, 'Handyman Services', 'Home Services',
 ARRAY['handyman', 'repair', 'maintenance', 'odd jobs', 'fix', 'installation'],
 ARRAY['General repairs', 'Home maintenance', 'Fixture installation', 'Odd jobs'],
 6),

('Flooring', TRUE, 'Flooring Installation', 'Home Services',
 ARRAY['flooring', 'hardwood', 'carpet', 'tile', 'laminate', 'vinyl', 'floor installation'],
 ARRAY['Hardwood installation', 'Carpet installation', 'Tile work', 'Floor refinishing'],
 7),

('Painting', TRUE, 'Painting Services', 'Home Services',
 ARRAY['painter', 'painting', 'interior painting', 'exterior painting', 'drywall'],
 ARRAY['Interior painting', 'Exterior painting', 'Drywall repair', 'Wallpaper removal'],
 8),

('Landscaping', TRUE, 'Landscaping Services', 'Home Services',
 ARRAY['landscaping', 'lawn care', 'tree service', 'gardening', 'irrigation', 'landscape design'],
 ARRAY['Lawn maintenance', 'Tree removal', 'Landscape design', 'Irrigation systems'],
 9),

('Windows & Doors', TRUE, 'Window & Door Installation', 'Home Services',
 ARRAY['windows', 'doors', 'window installation', 'door replacement', 'glass'],
 ARRAY['Window replacement', 'Door installation', 'Glass repair', 'Screen repair'],
 10),

('Concrete', FALSE, 'Concrete Services', 'Home Services',
 ARRAY['concrete', 'driveway', 'patio', 'sidewalk', 'foundation', 'cement'],
 ARRAY['Driveway installation', 'Patio construction', 'Concrete repair', 'Foundation work'],
 11),

('Fencing', FALSE, 'Fencing Contractors', 'Home Services',
 ARRAY['fence', 'fencing', 'gate', 'privacy fence', 'chain link'],
 ARRAY['Fence installation', 'Gate repair', 'Privacy fencing', 'Fence repair'],
 12),

('Kitchen & Bath', TRUE, 'Kitchen & Bathroom Remodeling', 'Home Services',
 ARRAY['kitchen', 'bathroom', 'cabinets', 'countertops', 'vanity', 'backsplash'],
 ARRAY['Kitchen remodel', 'Bathroom renovation', 'Cabinet installation', 'Countertop installation'],
 13),

('Insulation', FALSE, 'Insulation Services', 'Home Services',
 ARRAY['insulation', 'attic insulation', 'weatherization', 'energy efficiency'],
 ARRAY['Attic insulation', 'Wall insulation', 'Weatherproofing', 'Energy audits'],
 14),

('Security Systems', FALSE, 'Security Services', 'Home Services',
 ARRAY['security', 'alarm', 'camera', 'monitoring', 'access control'],
 ARRAY['Security system installation', 'Camera systems', 'Alarm monitoring'],
 15),

('Pool & Spa', FALSE, 'Pool Services', 'Home Services',
 ARRAY['pool', 'spa', 'hot tub', 'pool maintenance', 'pool repair'],
 ARRAY['Pool cleaning', 'Pool repair', 'Hot tub service', 'Pool equipment'],
 16),

('Garage Doors', FALSE, 'Garage Door Services', 'Home Services',
 ARRAY['garage door', 'opener', 'garage door repair', 'overhead door'],
 ARRAY['Garage door installation', 'Opener repair', 'Door maintenance'],
 17),

('Septic Systems', FALSE, 'Septic Services', 'Home Services',
 ARRAY['septic', 'septic tank', 'drain field', 'septic pumping'],
 ARRAY['Septic pumping', 'Septic repair', 'Drain field installation'],
 18),

('Solar', FALSE, 'Solar Installation', 'Home Services',
 ARRAY['solar', 'solar panels', 'renewable energy', 'solar installation'],
 ARRAY['Solar panel installation', 'Solar system design', 'Solar maintenance'],
 19),

('Demolition', FALSE, 'Demolition Services', 'Construction',
 ARRAY['demolition', 'removal', 'tear down', 'debris removal'],
 ARRAY['Structure demolition', 'Debris removal', 'Site clearing'],
 20);

-- Insert some commercial/non-home contractor categories for filtering
INSERT INTO mailer_categories (category_name, priority, afb_name, category, keywords, typical_services, sort_order) VALUES
('Commercial Construction', FALSE, 'Commercial Building', 'Commercial',
 ARRAY['commercial construction', 'office building', 'retail', 'warehouse'],
 ARRAY['Office construction', 'Retail buildouts', 'Warehouse construction'],
 50),

('Industrial Services', FALSE, 'Industrial Contractors', 'Industrial',
 ARRAY['industrial', 'manufacturing', 'factory', 'plant maintenance'],
 ARRAY['Industrial maintenance', 'Factory services', 'Plant construction'],
 51),

('Municipal Services', FALSE, 'Government Contractors', 'Municipal',
 ARRAY['municipal', 'government', 'public works', 'city contracts'],
 ARRAY['Public works', 'Municipal construction', 'Government projects'],
 52);