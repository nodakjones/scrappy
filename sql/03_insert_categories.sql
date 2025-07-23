-- Complete mailer categories for contractor enrichment system
-- Based on actual CRM data with complete taxonomy (62 total categories)

-- Clear existing data
DELETE FROM mailer_categories;

-- Insert ALL 30 PRIORITY categories (priority = TRUE)
INSERT INTO mailer_categories (category_name, priority, afb_name, category, keywords, typical_services, sort_order) VALUES

-- Priority Categories (30 total - high-value residential services)
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

-- Insert ALL 32 STANDARD categories (priority = FALSE) - complete taxonomy coverage
INSERT INTO mailer_categories (category_name, priority, afb_name, category, keywords, typical_services, sort_order) VALUES

-- Home Improvement & Services (not priority but important for complete taxonomy)
('BBQ Cleaning', FALSE, 'SERVICE-Other', 'Home Services',
 ARRAY['bbq cleaning', 'grill cleaning', 'barbecue', 'outdoor kitchen'],
 ARRAY['BBQ deep cleaning', 'Grill maintenance', 'Outdoor kitchen cleaning'],
 31),

('Window Film', FALSE, 'SERVICE-Other', 'Home Improvement',
 ARRAY['window film', 'window tinting', 'privacy film', 'security film'],
 ARRAY['Window tinting', 'Privacy film installation', 'Security window film'],
 32),

('Flooring', FALSE, 'HOME-Flooring', 'Home Improvement',
 ARRAY['flooring', 'hardwood', 'carpet', 'tile', 'laminate', 'vinyl'],
 ARRAY['Hardwood installation', 'Carpet installation', 'Tile work', 'Floor refinishing'],
 33),

('Media Systems', FALSE, 'RETAIL-Other', 'Home Services',
 ARRAY['media systems', 'home theater', 'audio visual', 'entertainment'],
 ARRAY['Home theater installation', 'Audio system setup', 'TV mounting'],
 34),

('Pools and Spas', FALSE, 'HOME-Pool/Spa Builders', 'Home Improvement',
 ARRAY['pool', 'spa', 'hot tub', 'pool maintenance', 'pool repair'],
 ARRAY['Pool installation', 'Spa service', 'Pool maintenance', 'Hot tub repair'],
 35),

('Roofing', FALSE, 'HOME-Roofing', 'Home Improvement',
 ARRAY['roofing', 'roof repair', 'shingles', 'roof replacement'],
 ARRAY['Roof replacement', 'Roof repair', 'Shingle installation', 'Roof inspection'],
 36),

('Exterior Solutions', FALSE, 'HOME-Other', 'Home Improvement',
 ARRAY['exterior', 'siding', 'exterior renovation', 'home exterior'],
 ARRAY['Siding installation', 'Exterior renovation', 'Home weatherization'],
 37),

('Security Screens & Doors', FALSE, 'SERVICE-Security Serv/Equip.', 'Home Improvement',
 ARRAY['security screens', 'security doors', 'screen doors', 'door security'],
 ARRAY['Security screen installation', 'Security door installation'],
 38),

('Security Systems', FALSE, 'SERVICE-Security Serv/Equip.', 'Home Improvement',
 ARRAY['security systems', 'alarm', 'camera', 'monitoring', 'access control'],
 ARRAY['Security system installation', 'Camera systems', 'Alarm monitoring', 'Smart locks'],
 39),

('Sheds and Storage', FALSE, 'HOME-Other', 'Home Improvement',
 ARRAY['sheds', 'storage buildings', 'outdoor storage', 'storage solutions'],
 ARRAY['Shed installation', 'Storage building construction', 'Outdoor storage solutions'],
 40),

('Shelving', FALSE, 'SERVICE-Closet/Organization', 'Home Improvement',
 ARRAY['shelving', 'custom shelves', 'wall shelves', 'storage shelves'],
 ARRAY['Custom shelving installation', 'Wall-mounted shelves', 'Storage solutions'],
 41),

('Siding', FALSE, 'HOME-Other', 'Home Improvement',
 ARRAY['siding', 'vinyl siding', 'exterior siding', 'house siding'],
 ARRAY['Siding installation', 'Siding repair', 'Vinyl siding replacement'],
 42),

('Skylights', FALSE, 'HOME-Windows', 'Home Improvement',
 ARRAY['skylights', 'roof windows', 'natural light', 'solar tubes'],
 ARRAY['Skylight installation', 'Roof window installation', 'Solar tube installation'],
 43),

('Water Systems', FALSE, 'HOME-Landscaping', 'Home Improvement',
 ARRAY['water systems', 'water filtration', 'well systems', 'water treatment'],
 ARRAY['Water filtration systems', 'Well installation', 'Water treatment solutions'],
 44),

('Attic & Crawl Space', FALSE, 'HOME-Other', 'Home Services',
 ARRAY['attic', 'crawl space', 'attic insulation', 'crawl space encapsulation'],
 ARRAY['Attic insulation', 'Crawl space cleaning', 'Attic ventilation'],
 45),

('Cabinet Refinishing', FALSE, 'HOME-Kitchen', 'Home Services',
 ARRAY['cabinet refinishing', 'cabinet painting', 'kitchen cabinets', 'cabinet restoration'],
 ARRAY['Cabinet refinishing', 'Cabinet painting', 'Kitchen cabinet restoration'],
 46),

('Countertops', FALSE, 'HOME-Kitchen', 'Home Services',
 ARRAY['countertops', 'granite', 'quartz', 'kitchen counters', 'bathroom counters'],
 ARRAY['Countertop installation', 'Granite countertops', 'Quartz countertops'],
 47),

('Gutter Cleaning', FALSE, 'HOME-Gutters', 'Home Services',
 ARRAY['gutter cleaning', 'gutter maintenance', 'downspout cleaning'],
 ARRAY['Professional gutter cleaning', 'Downspout cleaning', 'Gutter maintenance'],
 48),

('Rug Cleaning', FALSE, 'SERVICE-Carpet/Floor Cleaning', 'Home Services',
 ARRAY['rug cleaning', 'area rug cleaning', 'oriental rug cleaning'],
 ARRAY['Area rug cleaning', 'Oriental rug cleaning', 'Rug restoration'],
 49),

('Painting', FALSE, 'HOME-Painting', 'Home Services',
 ARRAY['painting', 'interior painting', 'exterior painting', 'house painting'],
 ARRAY['Interior painting', 'Exterior painting', 'Drywall repair', 'Color consultation'],
 50),

('Pest Control', FALSE, 'SERVICE-Pest Control', 'Home Services',
 ARRAY['pest control', 'exterminator', 'bug control', 'rodent control'],
 ARRAY['Pest elimination', 'Rodent control', 'Insect treatment', 'Preventive pest control'],
 51),

('Pressure Washing', FALSE, 'SERVICE-Pressure Washing', 'Home Services',
 ARRAY['pressure washing', 'power washing', 'house washing', 'driveway cleaning'],
 ARRAY['House pressure washing', 'Driveway cleaning', 'Deck cleaning'],
 52),

('Roof Cleaning & Repair', FALSE, 'HOME-Roofing', 'Home Services',
 ARRAY['roof cleaning', 'roof repair', 'moss removal', 'roof maintenance'],
 ARRAY['Roof cleaning', 'Moss removal', 'Minor roof repairs'],
 53),

('Hardscaping', FALSE, 'HOME-Landscaping', 'Home Improvement',
 ARRAY['hardscaping', 'retaining walls', 'stone work', 'landscape construction'],
 ARRAY['Retaining walls', 'Stone patios', 'Landscape construction'],
 54),

('Railings', FALSE, 'HOME-Fencing', 'Home Improvement',
 ARRAY['railings', 'handrails', 'deck railings', 'stair railings'],
 ARRAY['Deck railings', 'Stair railings', 'Custom railing installation'],
 55),

('Grout Cleaning', FALSE, 'SERVICE-Carpet/Floor Cleaning', 'Home Improvement',
 ARRAY['grout cleaning', 'tile cleaning', 'grout restoration'],
 ARRAY['Grout cleaning', 'Tile restoration', 'Grout sealing'],
 56),

('Septic', FALSE, 'SERVICE-Other', 'Home Services',
 ARRAY['septic', 'septic tank', 'drain field', 'septic pumping'],
 ARRAY['Septic pumping', 'Septic repair', 'Drain field installation', 'Septic inspection'],
 57),

('ADU Contractor', FALSE, 'HOME-Construction', 'Home Improvement',
 ARRAY['adu', 'accessory dwelling unit', 'granny flat', 'backyard cottage'],
 ARRAY['ADU construction', 'Accessory dwelling units', 'Backyard cottages'],
 58),

('Tile', FALSE, 'HOME-Flooring', 'Home Improvement',
 ARRAY['tile', 'ceramic tile', 'porcelain tile', 'tile installation'],
 ARRAY['Tile installation', 'Ceramic tile work', 'Bathroom tile'],
 59),

('Kitchen Remodel', FALSE, 'HOME-Kitchen', 'Home Improvement',
 ARRAY['kitchen remodel', 'kitchen renovation', 'kitchen design'],
 ARRAY['Kitchen renovation', 'Kitchen design', 'Cabinet installation'],
 60),

('Home Improvement', FALSE, 'HOME-Other', 'Home Improvement',
 ARRAY['home improvement', 'home renovation', 'remodeling'],
 ARRAY['General home improvement', 'Home renovation', 'Property upgrades'],
 61),

('Restoration Cleaning', FALSE, 'SERVICE-Maid/Cleaning', 'Home Services',
 ARRAY['restoration cleaning', 'damage restoration', 'cleanup'],
 ARRAY['Water damage cleanup', 'Fire damage restoration', 'Emergency cleanup'],
 62);

-- Insert Commercial/Industrial categories for complete taxonomy (will be filtered in processing)
INSERT INTO mailer_categories (category_name, priority, afb_name, category, keywords, typical_services, sort_order) VALUES

('Auto Glass/Repair', FALSE, 'PROFESSIONAL-Other', 'Personal & Professional Services',
 ARRAY['auto glass', 'windshield repair', 'car glass', 'automotive glass'],
 ARRAY['Windshield replacement', 'Auto glass repair', 'Car window repair'],
 100),

('Commercial Construction', FALSE, 'HOME-Construction', 'Commercial',
 ARRAY['commercial construction', 'office building', 'retail construction'],
 ARRAY['Office construction', 'Retail buildouts', 'Commercial renovation'],
 101),

('Industrial Services', FALSE, 'PROFESSIONAL-Other', 'Industrial',
 ARRAY['industrial', 'manufacturing', 'factory maintenance'],
 ARRAY['Industrial maintenance', 'Factory services', 'Equipment installation'],
 102);