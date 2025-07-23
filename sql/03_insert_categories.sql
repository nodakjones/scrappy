-- Complete mailer categories for contractor enrichment system
-- Based on actual CRM data with 30 priority categories

-- Clear existing data
DELETE FROM mailer_categories;

-- Insert all 30 PRIORITY categories (priority = TRUE)
INSERT INTO mailer_categories (category_name, priority, afb_name, category, keywords, typical_services, sort_order) VALUES

-- Priority Categories (30 total)
('Heating and Cooling', TRUE, 'HOME-HVAC', 'Home Improvement', 
 ARRAY['hvac', 'heating', 'cooling', 'air conditioning', 'furnace', 'heat pump', 'duct work'],
 ARRAY['AC repair', 'Furnace installation', 'Duct cleaning', 'Heat pump service', 'HVAC maintenance'],
 1),

('Plumbing', TRUE, 'SERVICE-Plumbing Services', 'Home Improvement', 
 ARRAY['plumber', 'pipes', 'drain', 'water heater', 'leak', 'sewer', 'faucet', 'toilet'],
 ARRAY['Drain cleaning', 'Water heater repair', 'Pipe repair', 'Leak detection', 'Bathroom fixtures'],
 2),

('Sprinklers', TRUE, 'HOME-Sprinkler/Irrigation', 'Home Improvement',
 ARRAY['sprinkler', 'irrigation', 'watering system', 'lawn sprinkler', 'drip irrigation'],
 ARRAY['Sprinkler installation', 'Irrigation repair', 'Watering system design', 'Sprinkler maintenance'],
 3),

('Blinds', TRUE, 'SERVICE-Window Treatments', 'Home Improvement',
 ARRAY['blinds', 'window treatments', 'shades', 'shutters', 'window coverings'],
 ARRAY['Blind installation', 'Custom window treatments', 'Shade repair', 'Shutter installation'],
 4),

('Window/Door', TRUE, 'HOME-Windows', 'Home Improvement',
 ARRAY['windows', 'doors', 'window installation', 'door replacement', 'glass', 'entry doors'],
 ARRAY['Window replacement', 'Door installation', 'Glass repair', 'Entry door replacement'],
 5),

('Awning/Patio/Carport', TRUE, 'HOME-Patio/Deck/Sunroom', 'Home Services',
 ARRAY['awning', 'patio', 'carport', 'outdoor cover', 'shade structure'],
 ARRAY['Awning installation', 'Patio covers', 'Carport construction', 'Outdoor shade structures'],
 6),

('Bathroom/Kitchen Remodel', TRUE, 'HOME-Bathroom', 'Home Services',
 ARRAY['bathroom', 'kitchen', 'remodel', 'renovation', 'makeover', 'upgrade'],
 ARRAY['Bathroom renovation', 'Kitchen remodel', 'Countertop installation', 'Cabinet upgrade'],
 7),

('Storage & Closets', TRUE, 'SERVICE-Closet/Organization', 'Home Services',
 ARRAY['storage', 'closets', 'organization', 'shelving', 'pantry'],
 ARRAY['Closet organization', 'Storage solutions', 'Custom shelving', 'Pantry systems'],
 8),

('Decks & Patios', TRUE, 'HOME-Patio/Deck/Sunroom', 'Home Services',
 ARRAY['deck', 'patio', 'outdoor living', 'deck building', 'patio construction'],
 ARRAY['Deck construction', 'Patio installation', 'Outdoor living spaces', 'Deck repair'],
 9),

('Electrician', TRUE, 'HOME-Electrical/Lighting', 'Home Services',
 ARRAY['electrician', 'electrical', 'wiring', 'panel', 'outlet', 'lighting'],
 ARRAY['Electrical repairs', 'Panel upgrades', 'Outlet installation', 'Lighting installation'],
 10),

('Fence', TRUE, 'HOME-Fencing', 'Home Services',
 ARRAY['fence', 'fencing', 'gate', 'privacy fence', 'chain link', 'wood fence'],
 ARRAY['Fence installation', 'Gate installation', 'Privacy fencing', 'Fence repair'],
 11),

('Fireplace', TRUE, 'SERVICE-Fireplace Services', 'Home Services',
 ARRAY['fireplace', 'chimney', 'hearth', 'gas fireplace', 'wood burning'],
 ARRAY['Fireplace installation', 'Chimney cleaning', 'Gas fireplace repair', 'Hearth construction'],
 12),

('Garage Floors', TRUE, 'HOME-Garages', 'Home Services',
 ARRAY['garage floor', 'epoxy', 'garage coating', 'concrete floor', 'floor coating'],
 ARRAY['Epoxy garage floors', 'Garage floor coating', 'Concrete floor finishing', 'Floor resurfacing'],
 13),

('Gutters', TRUE, 'HOME-Gutters', 'Home Improvement',
 ARRAY['gutters', 'downspouts', 'gutter cleaning', 'gutter installation', 'leaf guards'],
 ARRAY['Gutter installation', 'Gutter cleaning', 'Downspout repair', 'Gutter guards'],
 14),

('Handyman', TRUE, 'SERVICE-Handyman', 'Home Services',
 ARRAY['handyman', 'repair', 'maintenance', 'odd jobs', 'fix', 'installation'],
 ARRAY['General repairs', 'Home maintenance', 'Fixture installation', 'Odd jobs'],
 15),

('Junk Removal', TRUE, 'SERVICE-Junk/Hauling', 'Home Services',
 ARRAY['junk removal', 'hauling', 'debris', 'cleanup', 'trash removal'],
 ARRAY['Junk hauling', 'Debris removal', 'Estate cleanout', 'Construction cleanup'],
 16),

('Landscaping', TRUE, 'HOME-Landscaping', 'Home Services',
 ARRAY['landscaping', 'gardening', 'lawn care', 'landscape design', 'yard work'],
 ARRAY['Landscape design', 'Lawn maintenance', 'Garden installation', 'Yard cleanup'],
 17),

('Lighting', TRUE, 'HOME-Electrical/Lighting', 'Home Services',
 ARRAY['lighting', 'light fixtures', 'outdoor lighting', 'landscape lighting', 'led'],
 ARRAY['Light fixture installation', 'Outdoor lighting design', 'LED upgrades', 'Landscape lighting'],
 18),

('Tree Service', TRUE, 'HOME-Trees', 'Home Services',
 ARRAY['tree service', 'tree removal', 'trimming', 'pruning', 'stump grinding'],
 ARRAY['Tree removal', 'Tree trimming', 'Stump grinding', 'Tree pruning'],
 19),

('Window Cleaning', TRUE, 'SERVICE-Other', 'Home Services',
 ARRAY['window cleaning', 'window washing', 'glass cleaning', 'window service'],
 ARRAY['Residential window cleaning', 'Pressure washing windows', 'Glass cleaning service'],
 20),

('Window/Glass Repair', TRUE, 'HOME-Windows', 'Home Services',
 ARRAY['window repair', 'glass repair', 'window replacement', 'broken glass'],
 ARRAY['Window glass replacement', 'Screen repair', 'Window hardware repair', 'Glass restoration'],
 21),

('House Cleaning', TRUE, 'SERVICE-Maid/Cleaning', 'Home Services',
 ARRAY['house cleaning', 'maid service', 'cleaning service', 'residential cleaning'],
 ARRAY['Regular house cleaning', 'Deep cleaning', 'Move-in cleaning', 'Post-construction cleanup'],
 22),

('Garage Doors', TRUE, 'HOME-Garages', 'Home Improvement',
 ARRAY['garage door', 'garage door opener', 'overhead door', 'garage door repair'],
 ARRAY['Garage door installation', 'Opener repair', 'Garage door maintenance', 'Door replacement'],
 23),

('Solar', TRUE, 'HOME-Electrical/Lighting', 'Home Improvement',
 ARRAY['solar', 'solar panels', 'renewable energy', 'solar installation', 'solar power'],
 ARRAY['Solar panel installation', 'Solar system design', 'Solar maintenance', 'Energy storage'],
 24),

('Duct Cleaning', TRUE, 'SERVICE-Air Ducts', 'Home Services',
 ARRAY['duct cleaning', 'air duct', 'hvac cleaning', 'ventilation cleaning'],
 ARRAY['Air duct cleaning', 'HVAC system cleaning', 'Dryer vent cleaning', 'Ventilation maintenance'],
 25),

('Carpet Cleaning', TRUE, 'SERVICE-Carpet/Floor Cleaning', 'Home Services',
 ARRAY['carpet cleaning', 'upholstery cleaning', 'rug cleaning', 'steam cleaning'],
 ARRAY['Professional carpet cleaning', 'Upholstery cleaning', 'Stain removal', 'Steam cleaning'],
 26),

('Closets', TRUE, 'SERVICE-Closet/Organization', 'Home Improvement',
 ARRAY['closets', 'closet systems', 'wardrobe', 'closet design', 'storage systems'],
 ARRAY['Custom closet systems', 'Closet organization', 'Walk-in closets', 'Storage design'],
 27),

('Concrete', TRUE, 'HOME-Concrete', 'Home Improvement',
 ARRAY['concrete', 'driveway', 'patio', 'sidewalk', 'foundation', 'cement'],
 ARRAY['Concrete driveways', 'Patio construction', 'Sidewalk installation', 'Foundation work'],
 28),

('Foundations', TRUE, 'HOME-Other', 'Home Improvement',
 ARRAY['foundation', 'foundation repair', 'basement', 'crawl space', 'structural'],
 ARRAY['Foundation repair', 'Basement waterproofing', 'Crawl space encapsulation', 'Structural work'],
 29),

('Exterior Cleaning', TRUE, 'SERVICE-Pressure Washing', 'Home Improvement;Home Services',
 ARRAY['pressure washing', 'power washing', 'exterior cleaning', 'house washing'],
 ARRAY['House pressure washing', 'Driveway cleaning', 'Deck cleaning', 'Exterior surface cleaning'],
 30);

-- Insert STANDARD categories (priority = FALSE) - key ones for comprehensive coverage
INSERT INTO mailer_categories (category_name, priority, afb_name, category, keywords, typical_services, sort_order) VALUES

('Flooring', FALSE, 'HOME-Flooring', 'Home Improvement',
 ARRAY['flooring', 'hardwood', 'carpet', 'tile', 'laminate', 'vinyl'],
 ARRAY['Hardwood installation', 'Carpet installation', 'Tile work', 'Floor refinishing'],
 31),

('Roofing', FALSE, 'HOME-Roofing', 'Home Improvement',
 ARRAY['roofing', 'roof repair', 'shingles', 'roof replacement', 'gutters'],
 ARRAY['Roof replacement', 'Roof repair', 'Shingle installation', 'Roof inspection'],
 32),

('Painting', FALSE, 'HOME-Painting', 'Home Services',
 ARRAY['painting', 'interior painting', 'exterior painting', 'painter', 'drywall'],
 ARRAY['Interior painting', 'Exterior painting', 'Drywall repair', 'Color consultation'],
 33),

('Pools and Spas', FALSE, 'HOME-Pool/Spa Builders', 'Home Improvement',
 ARRAY['pool', 'spa', 'hot tub', 'pool maintenance', 'pool repair'],
 ARRAY['Pool installation', 'Spa service', 'Pool maintenance', 'Hot tub repair'],
 34),

('Security Systems', FALSE, 'SERVICE-Security Serv/Equip.', 'Home Improvement',
 ARRAY['security', 'alarm', 'camera', 'monitoring', 'access control'],
 ARRAY['Security system installation', 'Camera systems', 'Alarm monitoring', 'Smart locks'],
 35),

('Insulation', FALSE, 'HOME-Other', 'Home Services',
 ARRAY['insulation', 'attic insulation', 'weatherization', 'energy efficiency'],
 ARRAY['Attic insulation', 'Wall insulation', 'Weatherproofing', 'Energy audits'],
 36),

('Septic Systems', FALSE, 'SERVICE-Other', 'Home Services',
 ARRAY['septic', 'septic tank', 'drain field', 'septic pumping'],
 ARRAY['Septic pumping', 'Septic repair', 'Drain field installation', 'Septic inspection'],
 37),

('Pest Control', FALSE, 'SERVICE-Pest Control', 'Home Services',
 ARRAY['pest control', 'exterminator', 'bug control', 'rodent control'],
 ARRAY['Pest elimination', 'Rodent control', 'Insect treatment', 'Preventive pest control'],
 38),

('Mold Remediation', FALSE, 'SERVICE-Mold Remediation', 'Home Services',
 ARRAY['mold', 'mold removal', 'mold remediation', 'water damage'],
 ARRAY['Mold removal', 'Mold testing', 'Water damage restoration', 'Air quality testing'],
 39),

-- Commercial/Industrial categories (filtered out in residential processing)
('Commercial Construction', FALSE, 'HOME-Construction', 'Commercial',
 ARRAY['commercial construction', 'office building', 'retail construction'],
 ARRAY['Office construction', 'Retail buildouts', 'Commercial renovation'],
 50),

('Industrial Services', FALSE, 'PROFESSIONAL-Other', 'Industrial',
 ARRAY['industrial', 'manufacturing', 'factory maintenance'],
 ARRAY['Industrial maintenance', 'Factory services', 'Equipment installation'],
 51);