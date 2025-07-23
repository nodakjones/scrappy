-- COMPLETE mailer categories for contractor enrichment system
-- Based on actual CRM data with complete taxonomy (194 total categories)
-- 30 Priority + 164 Standard = 194 Total Categories

-- Clear existing data
DELETE FROM mailer_categories;

-- Insert ALL 30 PRIORITY categories (priority = TRUE)
INSERT INTO mailer_categories (category_name, priority, afb_name, category, keywords, typical_services, sort_order) VALUES

-- Priority Categories (30 total - high-value residential services)
('Heating and Cooling', TRUE, 'HOME-HVAC', 'Home Improvement', 
 ARRAY['hvac', 'heating', 'cooling', 'air conditioning', 'furnace', 'heat pump', 'ductwork'],
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

-- Insert ALL 164 STANDARD categories (priority = FALSE) - complete taxonomy coverage
INSERT INTO mailer_categories (category_name, priority, afb_name, category, keywords, typical_services, sort_order) VALUES

-- Home Improvement & Services Categories (164 total)
('ADU Contractor', FALSE, 'HOME-Construction', 'Home Improvement',
 ARRAY['adu', 'accessory dwelling unit', 'granny flat', 'backyard cottage'],
 ARRAY['ADU construction', 'Accessory dwelling units', 'Backyard cottages'],
 31),

('Academy', FALSE, '', 'Personal & Professional Services',
 ARRAY['academy', 'school', 'training', 'education'],
 ARRAY['Educational services', 'Training programs', 'Skill development'],
 32),

('Accounting Services', FALSE, '', 'Personal & Professional Services',
 ARRAY['accounting', 'bookkeeping', 'tax preparation', 'financial records'],
 ARRAY['Tax preparation', 'Bookkeeping services', 'Financial accounting'],
 33),

('Adult Home', FALSE, 'PROFESSIONAL-Other', 'Personal & Professional Services;Home Services',
 ARRAY['adult home', 'assisted living', 'senior care', 'elder care'],
 ARRAY['Assisted living services', 'Senior care', 'Elder support'],
 34),

('Animals', FALSE, 'RETAIL-Pet Care/Supplies', 'Personal & Professional Services',
 ARRAY['animals', 'pets', 'veterinary', 'pet care'],
 ARRAY['Pet care services', 'Veterinary care', 'Animal services'],
 35),

('Appliance Repair', FALSE, 'SERVICE-Appliance Repair', 'Home Services',
 ARRAY['appliance repair', 'refrigerator repair', 'washer repair', 'dryer repair'],
 ARRAY['Refrigerator repair', 'Washer/dryer repair', 'Appliance maintenance'],
 36),

('Appliances', FALSE, 'RETAIL-Other', 'Home Improvement',
 ARRAY['appliances', 'refrigerator', 'washer', 'dryer', 'dishwasher'],
 ARRAY['Appliance sales', 'Kitchen appliances', 'Laundry appliances'],
 37),

('Art', FALSE, 'RETAIL-Art/Rugs', 'Retail',
 ARRAY['art', 'artwork', 'paintings', 'sculptures', 'gallery'],
 ARRAY['Art sales', 'Custom artwork', 'Art galleries'],
 38),

('Asphalt', FALSE, 'HOME-Concrete', 'Home Improvement',
 ARRAY['asphalt', 'driveway paving', 'asphalt repair', 'paving'],
 ARRAY['Asphalt paving', 'Driveway installation', 'Asphalt repair'],
 39),

('Attic & Crawl Space', FALSE, 'HOME-Other', 'Home Services',
 ARRAY['attic', 'crawl space', 'attic insulation', 'crawl space encapsulation'],
 ARRAY['Attic insulation', 'Crawl space cleaning', 'Attic ventilation'],
 40),

('Attorney', FALSE, '', 'Personal & Professional Services',
 ARRAY['attorney', 'lawyer', 'legal services', 'law firm'],
 ARRAY['Legal representation', 'Legal consultation', 'Legal services'],
 41),

('Auto Glass/Repair', FALSE, 'PROFESSIONAL-Other', 'Personal & Professional Services',
 ARRAY['auto glass', 'windshield repair', 'car glass', 'automotive glass'],
 ARRAY['Windshield replacement', 'Auto glass repair', 'Car window repair'],
 42),

('Auto Wrap', FALSE, 'PROFESSIONAL-Other', 'Personal & Professional Services',
 ARRAY['auto wrap', 'vehicle wrap', 'car wrap', 'vinyl wrap'],
 ARRAY['Vehicle wrapping', 'Car graphics', 'Commercial vehicle wraps'],
 43),

('Automobile Dealerships', FALSE, 'RETAIL-Automotive', 'Personal & Professional Services',
 ARRAY['car dealership', 'auto sales', 'vehicle sales', 'car dealer'],
 ARRAY['New car sales', 'Used car sales', 'Auto financing'],
 44),

('Automobile Service', FALSE, 'PROFESSIONAL-Other', 'Personal & Professional Services',
 ARRAY['auto service', 'car repair', 'automotive service', 'auto maintenance'],
 ARRAY['Car repair', 'Auto maintenance', 'Vehicle service'],
 45),

('BBQ Cleaning', FALSE, 'SERVICE-Other', 'Home Services',
 ARRAY['bbq cleaning', 'grill cleaning', 'barbecue', 'outdoor kitchen'],
 ARRAY['BBQ deep cleaning', 'Grill maintenance', 'Outdoor kitchen cleaning'],
 46),

('Bakery', FALSE, '', 'Experiences',
 ARRAY['bakery', 'bread', 'pastries', 'cakes', 'baking'],
 ARRAY['Fresh bread', 'Custom cakes', 'Pastries and desserts'],
 47),

('Banking', FALSE, 'PROFESSIONAL-Financial', 'Personal & Professional Services',
 ARRAY['banking', 'bank', 'financial services', 'loans'],
 ARRAY['Banking services', 'Personal loans', 'Financial planning'],
 48),

('Boat Sales', FALSE, 'RETAIL-Boats', 'Retail',
 ARRAY['boat sales', 'marine', 'watercraft', 'yacht'],
 ARRAY['Boat sales', 'Marine equipment', 'Watercraft services'],
 49),

('Boat Share', FALSE, 'RETAIL-Boats', 'Experiences',
 ARRAY['boat share', 'boat rental', 'boat club', 'marine rental'],
 ARRAY['Boat sharing services', 'Boat rentals', 'Marine club'],
 50),

('Cabinet Refinishing', FALSE, 'HOME-Kitchen', 'Home Services',
 ARRAY['cabinet refinishing', 'cabinet painting', 'kitchen cabinets', 'cabinet restoration'],
 ARRAY['Cabinet refinishing', 'Cabinet painting', 'Kitchen cabinet restoration'],
 51),

('Cabinets', FALSE, 'HOME-Kitchen', 'Home Improvement',
 ARRAY['cabinets', 'kitchen cabinets', 'custom cabinets', 'cabinet installation'],
 ARRAY['Custom cabinet installation', 'Kitchen cabinets', 'Cabinet design'],
 52),

('Car Wash & Detailing', FALSE, 'RETAIL-Automotive', 'Personal & Professional Services',
 ARRAY['car wash', 'auto detailing', 'vehicle cleaning', 'car detailing'],
 ARRAY['Car washing', 'Auto detailing', 'Vehicle cleaning services'],
 53),

('Chimneys', FALSE, 'SERVICE-Fireplace Services', 'Home Services',
 ARRAY['chimney', 'chimney cleaning', 'chimney repair', 'chimney maintenance'],
 ARRAY['Chimney cleaning', 'Chimney repair', 'Chimney inspection'],
 54),

('Chiropractors', FALSE, 'HEALTH-Medical Services', 'Personal & Professional Services',
 ARRAY['chiropractor', 'chiropractic', 'spine care', 'back pain'],
 ARRAY['Chiropractic care', 'Spine treatment', 'Pain management'],
 55),

('Church', FALSE, 'NONPROFIT-Church', 'Personal & Professional Services',
 ARRAY['church', 'religious', 'worship', 'congregation'],
 ARRAY['Religious services', 'Worship services', 'Community faith'],
 56),

('Clothing', FALSE, 'RETAIL-Clothing/Shoes', 'Retail',
 ARRAY['clothing', 'apparel', 'fashion', 'clothes'],
 ARRAY['Clothing retail', 'Fashion apparel', 'Clothing accessories'],
 57),

('Construction Services', FALSE, '', 'Home Improvement',
 ARRAY['construction', 'building', 'contractor', 'general contractor'],
 ARRAY['General construction', 'Building services', 'Construction projects'],
 58),

('Consulting', FALSE, 'PROFESSIONAL-Other', 'Personal & Professional Services',
 ARRAY['consulting', 'consultant', 'business consulting', 'advisory'],
 ARRAY['Business consulting', 'Strategic planning', 'Professional advice'],
 59),

('Cool Sculpting', FALSE, 'HEALTH-Medical Services', 'Personal & Professional Services',
 ARRAY['cool sculpting', 'body contouring', 'fat reduction', 'cosmetic'],
 ARRAY['Body contouring', 'Fat reduction treatments', 'Cosmetic procedures'],
 60),

('Cooperative', FALSE, '', 'Personal & Professional Services',
 ARRAY['cooperative', 'co-op', 'community organization', 'collective'],
 ARRAY['Cooperative services', 'Community programs', 'Collective services'],
 61),

('Counseling Services', FALSE, 'PROFESSIONAL-Counseling', 'Personal & Professional Services',
 ARRAY['counseling', 'therapy', 'mental health', 'counselor'],
 ARRAY['Mental health counseling', 'Therapy services', 'Behavioral health'],
 62),

('Countertops', FALSE, 'HOME-Kitchen', 'Home Services',
 ARRAY['countertops', 'granite', 'quartz', 'kitchen counters', 'bathroom counters'],
 ARRAY['Countertop installation', 'Granite countertops', 'Quartz countertops'],
 63),

('Cruises', FALSE, 'TRAVEL-Cruises', 'Experiences',
 ARRAY['cruises', 'cruise ship', 'ocean travel', 'vacation cruise'],
 ARRAY['Cruise bookings', 'Ocean vacations', 'Cruise packages'],
 64),

('Custom Window Treatments', FALSE, 'SERVICE-Window Treatments', 'Home Improvement',
 ARRAY['custom window treatments', 'window coverings', 'drapery', 'custom blinds'],
 ARRAY['Custom drapery', 'Window covering design', 'Specialty window treatments'],
 65),

('Dentist', FALSE, 'HEALTH-Dental', 'Personal & Professional Services',
 ARRAY['dentist', 'dental', 'teeth', 'oral health'],
 ARRAY['Dental care', 'Teeth cleaning', 'Oral health services'],
 66),

('Dentists & Cosmetic Surgery', FALSE, 'HEALTH-Medical Services', 'Personal & Professional Services',
 ARRAY['cosmetic dentistry', 'dental surgery', 'oral surgery', 'dental implants'],
 ARRAY['Cosmetic dental procedures', 'Dental implants', 'Oral surgery'],
 67),

('Dining', FALSE, 'DINING-Other', 'Experiences',
 ARRAY['dining', 'restaurant', 'food service', 'cuisine'],
 ARRAY['Restaurant dining', 'Food services', 'Culinary experiences'],
 68),

('Doors', FALSE, 'HOME-Doors', 'Home Improvement',
 ARRAY['doors', 'entry doors', 'interior doors', 'door installation'],
 ARRAY['Door installation', 'Entry door replacement', 'Interior doors'],
 69),

('Dry Wall', FALSE, 'SERVICE-Handyman', 'Home Services',
 ARRAY['drywall', 'sheetrock', 'wall repair', 'drywall installation'],
 ARRAY['Drywall installation', 'Wall repair', 'Drywall finishing'],
 70),

('Dry Wall Repair', FALSE, 'SERVICE-Handyman', 'Home Services',
 ARRAY['drywall repair', 'wall patching', 'hole repair', 'wall damage'],
 ARRAY['Wall patching', 'Drywall hole repair', 'Wall damage restoration'],
 71),

('ECommerce', FALSE, 'RETAIL-Other', 'Retail',
 ARRAY['ecommerce', 'online retail', 'internet sales', 'web store'],
 ARRAY['Online retail', 'E-commerce services', 'Internet sales'],
 72),

('Education', FALSE, 'EDUCATION-Tutoring', 'Personal & Professional Services',
 ARRAY['education', 'tutoring', 'learning', 'academic'],
 ARRAY['Educational services', 'Tutoring programs', 'Academic support'],
 73),

('Employment Opportunity', FALSE, 'PROFESSIONAL-Other', 'Personal & Professional Services',
 ARRAY['employment', 'job opportunities', 'hiring', 'recruitment'],
 ARRAY['Job placement', 'Employment services', 'Career opportunities'],
 74),

('Entertainment', FALSE, 'ENTERTAIN-Other', 'Experiences',
 ARRAY['entertainment', 'events', 'shows', 'performances'],
 ARRAY['Entertainment services', 'Event entertainment', 'Performance services'],
 75),

('Event Planning / Catering', FALSE, 'DINING-Other', 'Personal & Professional Services',
 ARRAY['event planning', 'catering', 'party planning', 'wedding planning'],
 ARRAY['Event coordination', 'Catering services', 'Party planning'],
 76),

('Events', FALSE, 'ENTERTAIN-Other', 'Experiences',
 ARRAY['events', 'special events', 'celebrations', 'gatherings'],
 ARRAY['Event services', 'Special occasions', 'Celebration planning'],
 77),

('Exterior Solutions', FALSE, 'HOME-Other', 'Home Improvement',
 ARRAY['exterior', 'siding', 'exterior renovation', 'home exterior'],
 ARRAY['Siding installation', 'Exterior renovation', 'Home weatherization'],
 78),

('Financial Planning', FALSE, 'PROFESSIONAL-Financial', 'Personal & Professional Services',
 ARRAY['financial planning', 'investment', 'retirement planning', 'wealth management'],
 ARRAY['Investment planning', 'Retirement services', 'Wealth management'],
 79),

('Fitness', FALSE, 'HEALTH-Gym/Fitness', 'Personal & Professional Services',
 ARRAY['fitness', 'gym', 'personal training', 'exercise'],
 ARRAY['Fitness training', 'Gym services', 'Personal training'],
 80),

('Flooring', FALSE, 'HOME-Flooring', 'Home Improvement',
 ARRAY['flooring', 'hardwood', 'carpet', 'tile', 'laminate', 'vinyl'],
 ARRAY['Hardwood installation', 'Carpet installation', 'Tile work', 'Floor refinishing'],
 81),

('Fundraising, Events or Services', FALSE, 'NONPROFIT-Charity', 'Experiences',
 ARRAY['fundraising', 'charity events', 'nonprofit', 'donations'],
 ARRAY['Fundraising events', 'Charity services', 'Nonprofit support'],
 82),

('Funeral Home', FALSE, 'PROFESSIONAL-Other', 'Personal & Professional Services',
 ARRAY['funeral home', 'funeral services', 'memorial', 'burial'],
 ARRAY['Funeral services', 'Memorial services', 'Burial arrangements'],
 83),

('Furniture', FALSE, 'RETAIL-Furniture/Décor', 'Retail',
 ARRAY['furniture', 'home furnishings', 'interior furniture', 'home decor'],
 ARRAY['Furniture sales', 'Home furnishings', 'Interior design furniture'],
 84),

('Gates', FALSE, 'HOME-Other', 'Home Improvement',
 ARRAY['gates', 'driveway gates', 'security gates', 'automatic gates'],
 ARRAY['Gate installation', 'Automatic gates', 'Security gate systems'],
 85),

('Generators', FALSE, 'HOME-Electrical/Lighting', 'Home Improvement',
 ARRAY['generators', 'backup power', 'standby generator', 'emergency power'],
 ARRAY['Generator installation', 'Backup power systems', 'Emergency generators'],
 86),

('Golf', FALSE, 'RECREATION-Golf', 'Experiences',
 ARRAY['golf', 'golf course', 'golf lessons', 'golf equipment'],
 ARRAY['Golf courses', 'Golf instruction', 'Golf equipment'],
 87),

('Greenhouse', FALSE, 'HOME-Patio/Deck/Sunroom', 'Home Improvement',
 ARRAY['greenhouse', 'garden house', 'plant house', 'growing structure'],
 ARRAY['Greenhouse construction', 'Garden structures', 'Plant growing facilities'],
 88),

('Grout cleaning', FALSE, 'SERVICE-Carpet/Floor Cleaning', 'Home Improvement',
 ARRAY['grout cleaning', 'tile cleaning', 'grout restoration'],
 ARRAY['Grout cleaning', 'Tile restoration', 'Grout sealing'],
 89),

('Gutter Cleaning', FALSE, 'HOME-Gutters', 'Home Services',
 ARRAY['gutter cleaning', 'gutter maintenance', 'downspout cleaning'],
 ARRAY['Professional gutter cleaning', 'Downspout cleaning', 'Gutter maintenance'],
 90),

('Gutter Guards', FALSE, 'HOME-Gutters', 'Home Improvement',
 ARRAY['gutter guards', 'leaf guards', 'gutter protection', 'gutter screens'],
 ARRAY['Gutter guard installation', 'Leaf protection systems', 'Gutter screens'],
 91),

('Hair Salon / Spa', FALSE, 'BEAUTY-Salons', 'Personal & Professional Services',
 ARRAY['hair salon', 'beauty salon', 'spa', 'hair care'],
 ARRAY['Hair styling', 'Beauty treatments', 'Spa services'],
 92),

('Hardscaping', FALSE, 'HOME-Landscaping', 'Home Improvement',
 ARRAY['hardscaping', 'retaining walls', 'stone work', 'landscape construction'],
 ARRAY['Retaining walls', 'Stone patios', 'Landscape construction'],
 93),

('Health', FALSE, 'HEALTH-Other', 'Personal & Professional Services',
 ARRAY['health', 'healthcare', 'medical', 'wellness'],
 ARRAY['Health services', 'Wellness programs', 'Healthcare support'],
 94),

('Healthcare Services', FALSE, 'HEALTH-Medical Services', 'Personal & Professional Services',
 ARRAY['healthcare', 'medical services', 'health care', 'medical'],
 ARRAY['Medical care', 'Healthcare services', 'Health treatments'],
 95),

('Home Automation', FALSE, '', 'Home Improvement',
 ARRAY['home automation', 'smart home', 'home technology', 'automated systems'],
 ARRAY['Smart home installation', 'Home automation systems', 'Intelligent home technology'],
 96),

('Home Builder', FALSE, 'HOME-Construction', 'Home Improvement',
 ARRAY['home builder', 'custom homes', 'new construction', 'residential construction'],
 ARRAY['Custom home construction', 'New home building', 'Residential construction'],
 97),

('Home Decor', FALSE, 'PROFESSIONAL-Interior Design', 'Home Improvement',
 ARRAY['home decor', 'interior decorating', 'home styling', 'decoration'],
 ARRAY['Interior decorating', 'Home styling services', 'Decorative accessories'],
 98),

('Home Equipment/furnishings', FALSE, 'RETAIL-Furniture/Décor', 'Retail',
 ARRAY['home equipment', 'home furnishings', 'household items', 'home goods'],
 ARRAY['Home furnishing sales', 'Household equipment', 'Home accessories'],
 99),

('Home Improvement', FALSE, 'HOME-Other', 'Home Improvement',
 ARRAY['home improvement', 'home renovation', 'remodeling'],
 ARRAY['General home improvement', 'Home renovation', 'Property upgrades'],
 100),

('Home Inspection', FALSE, 'PROFESSIONAL-Other', 'Home Services',
 ARRAY['home inspection', 'property inspection', 'house inspection', 'inspection services'],
 ARRAY['Property inspections', 'Home buyer inspections', 'Real estate inspections'],
 101),

('Home Items', FALSE, 'RETAIL-Other', 'Retail',
 ARRAY['home items', 'household goods', 'home accessories', 'home products'],
 ARRAY['Home goods retail', 'Household accessories', 'Home product sales'],
 102),

('Home Services', FALSE, 'HOME-Other', 'Home Improvement',
 ARRAY['home services', 'residential services', 'home maintenance', 'house services'],
 ARRAY['Residential services', 'Home maintenance', 'Property services'],
 103),

('Hotels & Resorts', FALSE, 'TRAVEL-Resorts', 'Experiences',
 ARRAY['hotels', 'resorts', 'accommodation', 'lodging'],
 ARRAY['Hotel accommodations', 'Resort stays', 'Lodging services'],
 104),

('Hottub', FALSE, 'HOME-Pool/Spa Builders', 'Home Improvement',
 ARRAY['hot tub', 'spa', 'jacuzzi', 'therapeutic spa'],
 ARRAY['Hot tub installation', 'Spa services', 'Therapeutic spa systems'],
 105),

('IT & Networks', FALSE, '', 'Personal & Professional Services',
 ARRAY['information technology', 'computer networks', 'it support', 'tech services'],
 ARRAY['IT support', 'Network services', 'Computer technical services'],
 106),

('Insurance Providers', FALSE, 'PROFESSIONAL-Insurance', 'Personal & Professional Services',
 ARRAY['insurance', 'insurance agency', 'coverage', 'insurance services'],
 ARRAY['Insurance coverage', 'Policy services', 'Insurance consultation'],
 107),

('Interior Design', FALSE, 'PROFESSIONAL-Interior Design', 'Personal & Professional Services',
 ARRAY['interior design', 'interior decorator', 'home design', 'space planning'],
 ARRAY['Interior design services', 'Space planning', 'Home decoration'],
 108),

('Jewelers', FALSE, 'RETAIL-Jewelry & Watches', 'Retail',
 ARRAY['jewelry', 'jeweler', 'watches', 'precious metals'],
 ARRAY['Jewelry sales', 'Watch repair', 'Custom jewelry'],
 109),

('Kitchen Remodel', FALSE, 'HOME-Kitchen', 'Home Improvement',
 ARRAY['kitchen remodel', 'kitchen renovation', 'kitchen design'],
 ARRAY['Kitchen renovation', 'Kitchen design', 'Cabinet installation'],
 110),

('LEAD Card', FALSE, 'LABEL-Lead', 'Personal & Professional Services',
 ARRAY['lead card', 'lead generation', 'marketing leads', 'business leads'],
 ARRAY['Lead generation services', 'Marketing leads', 'Business development'],
 111),

('Label', FALSE, '', 'Personal & Professional Services',
 ARRAY['labeling', 'labels', 'identification', 'marking'],
 ARRAY['Labeling services', 'Custom labels', 'Identification systems'],
 112),

('Laser Hair Removal', FALSE, 'HEALTH-Spa Services', 'Personal & Professional Services',
 ARRAY['laser hair removal', 'hair removal', 'cosmetic treatment', 'laser treatment'],
 ARRAY['Laser hair removal treatments', 'Cosmetic laser services', 'Hair removal procedures'],
 113),

('Lasik Surgery', FALSE, 'HEALTH-Vision Care/Lasik', 'Personal & Professional Services',
 ARRAY['lasik', 'eye surgery', 'vision correction', 'laser eye surgery'],
 ARRAY['Lasik eye surgery', 'Vision correction', 'Laser eye treatments'],
 114),

('Legal', FALSE, 'PROFESSIONAL-Legal', 'Personal & Professional Services',
 ARRAY['legal services', 'law', 'attorney', 'legal advice'],
 ARRAY['Legal representation', 'Legal consultation', 'Law services'],
 115),

('Life Coaching', FALSE, 'PROFESSIONAL-Counseling', 'Personal & Professional Services',
 ARRAY['life coaching', 'personal coaching', 'life coach', 'personal development'],
 ARRAY['Life coaching services', 'Personal development', 'Goal achievement coaching'],
 116),

('Life Coachingq', FALSE, 'PROFESSIONAL-Counseling', 'Personal & Professional Services',
 ARRAY['life coaching', 'personal coaching', 'life coach', 'personal development'],
 ARRAY['Life coaching services', 'Personal development', 'Goal achievement coaching'],
 117),

('Marketing', FALSE, 'PROFESSIONAL-Other', 'Personal & Professional Services',
 ARRAY['marketing', 'advertising', 'digital marketing', 'promotion'],
 ARRAY['Marketing services', 'Advertising campaigns', 'Digital marketing'],
 118),

('Masonry', FALSE, 'SERVICE-Other', 'Home Improvement',
 ARRAY['masonry', 'stonework', 'brickwork', 'stone installation'],
 ARRAY['Stone installation', 'Brick work', 'Masonry construction'],
 119),

('Massage', FALSE, 'HEALTH-Massage', 'Personal & Professional Services',
 ARRAY['massage', 'massage therapy', 'therapeutic massage', 'wellness'],
 ARRAY['Massage therapy', 'Therapeutic massage', 'Wellness treatments'],
 120),

('Mattress', FALSE, 'RETAIL-Other', 'Retail',
 ARRAY['mattress', 'bedding', 'sleep products', 'bedroom furniture'],
 ARRAY['Mattress sales', 'Bedding products', 'Sleep solutions'],
 121),

('Med Spa', FALSE, 'HEALTH-Spa Services', 'Personal & Professional Services',
 ARRAY['medical spa', 'med spa', 'cosmetic treatments', 'aesthetic services'],
 ARRAY['Medical spa treatments', 'Cosmetic procedures', 'Aesthetic services'],
 122),

('Media Systems', FALSE, 'RETAIL-Other', 'Home Services',
 ARRAY['media systems', 'home theater', 'audio visual', 'entertainment systems'],
 ARRAY['Home theater installation', 'Audio system setup', 'TV mounting'],
 123),

('Medical Supply', FALSE, 'RETAIL-Other', 'Retail',
 ARRAY['medical supplies', 'healthcare products', 'medical equipment', 'health supplies'],
 ARRAY['Medical supply sales', 'Healthcare products', 'Medical equipment'],
 124),

('Mold Remediation', FALSE, 'SERVICE-Mold Remediation', 'Home Services',
 ARRAY['mold remediation', 'mold removal', 'mold cleanup', 'water damage'],
 ARRAY['Mold removal', 'Mold testing', 'Water damage restoration', 'Air quality testing'],
 125),

('Mortgage / Loans', FALSE, 'PROFESSIONAL-Mortgage', 'Personal & Professional Services',
 ARRAY['mortgage', 'home loans', 'lending', 'financing'],
 ARRAY['Mortgage services', 'Home loan financing', 'Lending services'],
 126),

('Moving', FALSE, 'PROFESSIONAL-Moving', 'Personal & Professional Services',
 ARRAY['moving', 'relocation', 'moving services', 'movers'],
 ARRAY['Moving services', 'Residential relocation', 'Commercial moving'],
 127),

('Music', FALSE, 'RETAIL-Instruments', 'Retail',
 ARRAY['music', 'musical instruments', 'music lessons', 'music store'],
 ARRAY['Musical instrument sales', 'Music lessons', 'Music equipment'],
 128),

('Non Profit / Fundraiser', FALSE, 'NONPROFIT-Charity', 'Personal & Professional Services;Experiences',
 ARRAY['nonprofit', 'charity', 'fundraising', 'charitable organization'],
 ARRAY['Nonprofit services', 'Charitable programs', 'Fundraising events'],
 129),

('Notary', FALSE, '', 'Personal & Professional Services',
 ARRAY['notary', 'notary public', 'document notarization', 'legal documents'],
 ARRAY['Notary services', 'Document notarization', 'Legal document services'],
 130),

('Nursery', FALSE, '', 'Experiences',
 ARRAY['nursery', 'plant nursery', 'garden center', 'plants'],
 ARRAY['Plant nursery', 'Garden supplies', 'Landscaping plants'],
 131),

('Outdoor', FALSE, 'RECREATION-Other', 'Retail',
 ARRAY['outdoor', 'outdoor equipment', 'camping', 'recreation'],
 ARRAY['Outdoor equipment', 'Camping supplies', 'Recreation gear'],
 132),

('Outdoor Lighting', FALSE, 'HOME-Electrical/Lighting', 'Home Improvement',
 ARRAY['outdoor lighting', 'landscape lighting', 'exterior lighting', 'garden lights'],
 ARRAY['Landscape lighting', 'Outdoor light installation', 'Garden lighting'],
 133),

('Outdoor Living', FALSE, 'HOME-Patio/Deck/Sunroom', 'Home Improvement',
 ARRAY['outdoor living', 'patio furniture', 'outdoor spaces', 'backyard living'],
 ARRAY['Outdoor living spaces', 'Patio design', 'Backyard entertainment'],
 134),

('Painting', FALSE, 'HOME-Painting', 'Home Services',
 ARRAY['painting', 'interior painting', 'exterior painting', 'house painting'],
 ARRAY['Interior painting', 'Exterior painting', 'Drywall repair', 'Color consultation'],
 135),

('Pavers', FALSE, 'HOME-Landscaping', 'Home Improvement',
 ARRAY['pavers', 'paving stones', 'brick pavers', 'patio pavers'],
 ARRAY['Paver installation', 'Patio pavers', 'Driveway pavers'],
 136),

('Pergolas', FALSE, 'HOME-Patio/Deck/Sunroom', 'Home Improvement',
 ARRAY['pergolas', 'outdoor structures', 'patio covers', 'garden structures'],
 ARRAY['Pergola construction', 'Outdoor shade structures', 'Garden pergolas'],
 137),

('Pest Control', FALSE, 'SERVICE-Pest Control', 'Home Services',
 ARRAY['pest control', 'exterminator', 'bug control', 'rodent control'],
 ARRAY['Pest elimination', 'Rodent control', 'Insect treatment', 'Preventive pest control'],
 138),

('Pets', FALSE, 'RETAIL-Pet Care/Supplies', 'Home Services',
 ARRAY['pets', 'pet care', 'pet supplies', 'animal care'],
 ARRAY['Pet care services', 'Pet supplies', 'Animal grooming'],
 139),

('Photo Archiving', FALSE, 'PROFESSIONAL-Other', 'Personal & Professional Services',
 ARRAY['photo archiving', 'photo organization', 'digital photos', 'photo storage'],
 ARRAY['Photo organization services', 'Digital photo archiving', 'Photo preservation'],
 140),

('Photographers', FALSE, 'PROFESSIONAL-Photography', 'Personal & Professional Services',
 ARRAY['photography', 'photographer', 'wedding photography', 'portrait photography'],
 ARRAY['Wedding photography', 'Portrait photography', 'Event photography'],
 141),

('Piano', FALSE, 'RETAIL-Instruments', 'Retail',
 ARRAY['piano', 'piano lessons', 'piano tuning', 'keyboard'],
 ARRAY['Piano sales', 'Piano lessons', 'Piano tuning services'],
 142),

('Play Equipment', FALSE, 'RETAIL-Sports Equipment/Gear', 'Home Improvement',
 ARRAY['playground equipment', 'play sets', 'swing sets', 'outdoor play'],
 ARRAY['Playground installation', 'Swing set assembly', 'Outdoor play equipment'],
 143),

('Plumbing Fixtures', FALSE, 'RETAIL-Other', 'Home Improvement',
 ARRAY['plumbing fixtures', 'faucets', 'toilets', 'bathroom fixtures'],
 ARRAY['Plumbing fixture sales', 'Bathroom fixtures', 'Kitchen plumbing'],
 144),

('Pools and Spas', FALSE, 'HOME-Pool/Spa Builders', 'Home Improvement',
 ARRAY['pool', 'spa', 'swimming pool', 'pool maintenance', 'pool repair'],
 ARRAY['Pool installation', 'Spa service', 'Pool maintenance', 'Hot tub repair'],
 145),

('Portable Buildings', FALSE, 'HOME-Other', 'Retail',
 ARRAY['portable buildings', 'storage sheds', 'prefab buildings', 'modular structures'],
 ARRAY['Portable building sales', 'Storage shed installation', 'Modular buildings'],
 146),

('Pressure Washing', FALSE, 'SERVICE-Pressure Washing', 'Home Services',
 ARRAY['pressure washing', 'power washing', 'house washing', 'driveway cleaning'],
 ARRAY['House pressure washing', 'Driveway cleaning', 'Deck cleaning'],
 147),

('Printing services', FALSE, '', 'Personal & Professional Services',
 ARRAY['printing', 'print shop', 'commercial printing', 'copy services'],
 ARRAY['Commercial printing', 'Copy services', 'Print production'],
 148),

('Professional Services', FALSE, 'PROFESSIONAL-Other', 'Personal & Professional Services',
 ARRAY['professional services', 'business services', 'consulting', 'expertise'],
 ARRAY['Professional consulting', 'Business services', 'Expert services'],
 149),

('Property Management', FALSE, 'PROFESSIONAL-Other', 'Personal & Professional Services',
 ARRAY['property management', 'real estate management', 'rental management', 'property services'],
 ARRAY['Property management services', 'Rental property management', 'Real estate services'],
 150),

('RV Sales', FALSE, 'RETAIL-Other', 'Retail',
 ARRAY['rv sales', 'recreational vehicles', 'motorhomes', 'travel trailers'],
 ARRAY['RV sales', 'Recreational vehicle services', 'RV rentals'],
 151),

('Radiant Floor Heating', FALSE, 'SERVICE-Plumbing Services', 'Home Improvement',
 ARRAY['radiant floor heating', 'underfloor heating', 'heated floors', 'floor warming'],
 ARRAY['Radiant heating installation', 'Underfloor heating systems', 'Heated floor installation'],
 152),

('Railings', FALSE, 'HOME-Fencing', 'Home Improvement',
 ARRAY['railings', 'handrails', 'deck railings', 'stair railings'],
 ARRAY['Deck railings', 'Stair railings', 'Custom railing installation'],
 153),

('Real Estate', FALSE, 'PROFESSIONAL-Real Estate', 'Personal & Professional Services',
 ARRAY['real estate', 'realtor', 'property sales', 'home sales'],
 ARRAY['Real estate sales', 'Property listings', 'Home buying services'],
 154),

('Recreation', FALSE, 'RECREATION-Other', 'Retail',
 ARRAY['recreation', 'recreational activities', 'leisure', 'entertainment'],
 ARRAY['Recreational services', 'Leisure activities', 'Entertainment options'],
 155),

('Remodel', FALSE, 'HOME-Construction', 'Home Improvement',
 ARRAY['remodel', 'renovation', 'home remodeling', 'reconstruction'],
 ARRAY['Home remodeling', 'Renovation services', 'Property reconstruction'],
 156),

('Restaurant', FALSE, 'DINING-Other', 'Experiences',
 ARRAY['restaurant', 'dining', 'food service', 'cuisine'],
 ARRAY['Restaurant dining', 'Food service', 'Culinary experiences'],
 157),

('Restoration Cleaning', FALSE, 'SERVICE-Maid/Cleaning', 'Home Services',
 ARRAY['restoration cleaning', 'damage restoration', 'cleanup', 'disaster cleanup'],
 ARRAY['Water damage cleanup', 'Fire damage restoration', 'Emergency cleanup'],
 158),

('Retail', FALSE, 'RETAIL-Other', 'Retail',
 ARRAY['retail', 'retail store', 'merchandise', 'shopping'],
 ARRAY['Retail sales', 'Merchandise', 'Shopping services'],
 159),

('Retirement Living', FALSE, 'PROFESSIONAL-Other', 'Personal & Professional Services',
 ARRAY['retirement living', 'senior living', 'retirement community', 'assisted living'],
 ARRAY['Retirement community services', 'Senior living options', 'Assisted living facilities'],
 160),

('Retrofit', FALSE, 'SERVICE-Other', 'Home Improvement',
 ARRAY['retrofit', 'home retrofitting', 'energy retrofit', 'building improvement'],
 ARRAY['Home retrofitting', 'Energy efficiency upgrades', 'Building improvements'],
 161),

('Roof Cleaning & Repair', FALSE, 'HOME-Roofing', 'Home Services',
 ARRAY['roof cleaning', 'roof repair', 'moss removal', 'roof maintenance'],
 ARRAY['Roof cleaning', 'Moss removal', 'Minor roof repairs'],
 162),

('Roof Restoration', FALSE, 'HOME-Roofing', 'Home Improvement',
 ARRAY['roof restoration', 'roof renewal', 'roof coating', 'roof refurbishment'],
 ARRAY['Roof restoration services', 'Roof coating application', 'Roof refurbishment'],
 163),

('Roofing', FALSE, 'HOME-Roofing', 'Home Improvement',
 ARRAY['roofing', 'roof repair', 'shingles', 'roof replacement'],
 ARRAY['Roof replacement', 'Roof repair', 'Shingle installation', 'Roof inspection'],
 164),

('Rug Cleaning', FALSE, 'SERVICE-Carpet/Floor Cleaning', 'Home Services',
 ARRAY['rug cleaning', 'area rug cleaning', 'oriental rug cleaning'],
 ARRAY['Area rug cleaning', 'Oriental rug cleaning', 'Rug restoration'],
 165),

('Rugs', FALSE, 'SERVICE-Carpet/Floor Cleaning', 'Retail',
 ARRAY['rugs', 'area rugs', 'carpet', 'floor coverings'],
 ARRAY['Rug sales', 'Area rug installation', 'Floor covering sales'],
 166),

('Safes', FALSE, 'SERVICE-Security Serv/Equip.', 'Home Services',
 ARRAY['safes', 'security safes', 'home safes', 'fireproof safes'],
 ARRAY['Safe installation', 'Security safe sales', 'Safe opening services'],
 167),

('Security Screens & Doors', FALSE, 'SERVICE-Security Serv/Equip.', 'Home Improvement',
 ARRAY['security screens', 'security doors', 'screen doors', 'door security'],
 ARRAY['Security screen installation', 'Security door installation'],
 168),

('Security Systems', FALSE, 'SERVICE-Security Serv/Equip.', 'Home Improvement',
 ARRAY['security systems', 'alarm', 'camera', 'monitoring', 'access control'],
 ARRAY['Security system installation', 'Camera systems', 'Alarm monitoring', 'Smart locks'],
 169),

('Senior Care', FALSE, 'PROFESSIONAL-Other', 'Personal & Professional Services',
 ARRAY['senior care', 'elderly care', 'aging services', 'senior support'],
 ARRAY['Senior care services', 'Elderly support', 'Aging in place services'],
 170),

('Septic', FALSE, 'SERVICE-Other', 'Home Services',
 ARRAY['septic', 'septic tank', 'drain field', 'septic pumping'],
 ARRAY['Septic pumping', 'Septic repair', 'Drain field installation', 'Septic inspection'],
 171),

('Sewer', FALSE, '', 'Home Improvement',
 ARRAY['sewer', 'sewer line', 'sewer repair', 'drain cleaning'],
 ARRAY['Sewer line repair', 'Drain cleaning', 'Sewer maintenance'],
 172),

('Sheds and Storage', FALSE, 'HOME-Other', 'Home Improvement',
 ARRAY['sheds', 'storage buildings', 'outdoor storage', 'storage solutions'],
 ARRAY['Shed installation', 'Storage building construction', 'Outdoor storage solutions'],
 173),

('Shelving', FALSE, 'SERVICE-Closet/Organization', 'Home Improvement',
 ARRAY['shelving', 'custom shelves', 'wall shelves', 'storage shelves'],
 ARRAY['Custom shelving installation', 'Wall-mounted shelves', 'Storage solutions'],
 174),

('Siding', FALSE, 'HOME-Other', 'Home Improvement',
 ARRAY['siding', 'vinyl siding', 'exterior siding', 'house siding'],
 ARRAY['Siding installation', 'Siding repair', 'Vinyl siding replacement'],
 175),

('Skin', FALSE, 'HEALTH-Spa Services', 'Personal & Professional Services',
 ARRAY['skin care', 'dermatology', 'facial treatments', 'skin health'],
 ARRAY['Skin care treatments', 'Facial services', 'Dermatological care'],
 176),

('Skylights', FALSE, 'HOME-Windows', 'Home Improvement',
 ARRAY['skylights', 'roof windows', 'natural light', 'solar tubes'],
 ARRAY['Skylight installation', 'Roof window installation', 'Solar tube installation'],
 177),

('Sleep', FALSE, 'PROFESSIONAL-Other', 'Personal & Professional Services',
 ARRAY['sleep services', 'sleep study', 'sleep disorders', 'sleep medicine'],
 ARRAY['Sleep disorder treatment', 'Sleep studies', 'Sleep medicine'],
 178),

('Sliding Shelves', FALSE, 'SERVICE-Closet/Organization', 'Home Improvement',
 ARRAY['sliding shelves', 'pull-out shelves', 'cabinet organizers', 'pantry shelves'],
 ARRAY['Pull-out shelf installation', 'Cabinet organization', 'Pantry organizers'],
 179),

('Sporting Goods', FALSE, 'RETAIL-Sports Equipment/Gear', 'Retail',
 ARRAY['sporting goods', 'sports equipment', 'athletic gear', 'fitness equipment'],
 ARRAY['Sports equipment sales', 'Athletic gear', 'Fitness equipment'],
 180),

('Staging', FALSE, 'PROFESSIONAL-Real Estate', 'Personal & Professional Services;Home Services',
 ARRAY['home staging', 'property staging', 'real estate staging', 'staging services'],
 ARRAY['Home staging services', 'Property presentation', 'Real estate staging'],
 181),

('Store', FALSE, 'RETAIL-Other', 'Retail',
 ARRAY['store', 'retail store', 'shop', 'retail business'],
 ARRAY['Retail store operations', 'Shopping services', 'Retail business'],
 182),

('Synthetic Turf', FALSE, 'HOME-Landscaping', 'Home Improvement',
 ARRAY['synthetic turf', 'artificial grass', 'fake grass', 'artificial lawn'],
 ARRAY['Synthetic turf installation', 'Artificial grass installation', 'Fake lawn installation'],
 183),

('Tile', FALSE, 'HOME-Flooring', 'Home Improvement',
 ARRAY['tile', 'ceramic tile', 'porcelain tile', 'tile installation'],
 ARRAY['Tile installation', 'Ceramic tile work', 'Bathroom tile'],
 184),

('Tires', FALSE, 'RETAIL-Automotive', 'Retail',
 ARRAY['tires', 'tire sales', 'tire service', 'automotive tires'],
 ARRAY['Tire sales', 'Tire installation', 'Tire service'],
 185),

('Trade Show', FALSE, 'ENTERTAIN-Other', 'Experiences',
 ARRAY['trade show', 'exhibition', 'business expo', 'industry event'],
 ARRAY['Trade show services', 'Exhibition planning', 'Business expo'],
 186),

('Travel Agent', FALSE, 'TRAVEL-Agency Services', 'Experiences',
 ARRAY['travel agent', 'travel planning', 'vacation planning', 'trip booking'],
 ARRAY['Travel planning services', 'Vacation booking', 'Trip coordination'],
 187),

('Upholstery', FALSE, 'RETAIL-Furniture/Décor', 'Home Improvement',
 ARRAY['upholstery', 'furniture repair', 'reupholstery', 'furniture restoration'],
 ARRAY['Furniture reupholstery', 'Upholstery repair', 'Furniture restoration'],
 188),

('Vacation Property Rental', FALSE, 'TRAVEL-Resorts', 'Experiences',
 ARRAY['vacation rental', 'property rental', 'holiday rental', 'short-term rental'],
 ARRAY['Vacation property rentals', 'Holiday home rentals', 'Short-term accommodations'],
 189),

('Water Feature', FALSE, 'HOME-Landscaping', 'Home Improvement',
 ARRAY['water feature', 'fountain', 'pond', 'water garden'],
 ARRAY['Water feature installation', 'Fountain construction', 'Pond installation'],
 190),

('Water Systems', FALSE, 'HOME-Landscaping', 'Home Improvement',
 ARRAY['water systems', 'water filtration', 'well systems', 'water treatment'],
 ARRAY['Water filtration systems', 'Well installation', 'Water treatment solutions'],
 191),

('Window Film', FALSE, 'SERVICE-Other', 'Home Improvement',
 ARRAY['window film', 'window tinting', 'privacy film', 'security film'],
 ARRAY['Window tinting', 'Privacy film installation', 'Security window film'],
 192),

('Wood Floor', FALSE, 'HOME-Flooring', 'Home Improvement',
 ARRAY['wood floor', 'hardwood flooring', 'wood flooring', 'floor refinishing'],
 ARRAY['Hardwood floor installation', 'Wood floor refinishing', 'Floor restoration'],
 193),

('Yard Maintenance', FALSE, 'HOME-Landscaping', 'Home Services',
 ARRAY['yard maintenance', 'lawn maintenance', 'yard care', 'landscape maintenance'],
 ARRAY['Lawn care', 'Yard cleanup', 'Landscape maintenance'],
 194);