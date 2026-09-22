// ─────────────────────────────────────────────────────────────────────────────
// World Countries → Cities mapping (comprehensive)
// ─────────────────────────────────────────────────────────────────────────────
export const GEO: Record<string, string[]> = {
  // ── North America ──────────────────────────────────────────────────────────
  "United States": [
    "New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia",
    "San Antonio", "San Diego", "Dallas", "San Jose", "Austin", "Jacksonville",
    "Fort Worth", "Columbus", "Charlotte", "Indianapolis", "San Francisco",
    "Seattle", "Denver", "Nashville", "Oklahoma City", "El Paso", "Boston",
    "Portland", "Las Vegas", "Memphis", "Louisville", "Baltimore", "Milwaukee",
    "Albuquerque", "Tucson", "Fresno", "Sacramento", "Mesa", "Kansas City",
    "Atlanta", "Omaha", "Colorado Springs", "Raleigh", "Miami", "Minneapolis",
    "Tampa", "New Orleans", "Cleveland", "Bakersfield", "Honolulu", "Detroit",
    "Arlington", "Anaheim", "Aurora", "St. Louis", "Pittsburgh",
  ],
  "Canada": [
    "Toronto", "Montreal", "Vancouver", "Calgary", "Edmonton", "Ottawa",
    "Winnipeg", "Quebec City", "Hamilton", "Kitchener", "London", "Victoria",
    "Halifax", "Oshawa", "Windsor", "Saskatoon", "Regina", "St. Catharines",
    "Kelowna", "Abbotsford", "Barrie", "Sudbury", "Kingston",
  ],
  "Mexico": [
    "Mexico City", "Guadalajara", "Monterrey", "Puebla", "Tijuana", "León",
    "Juárez", "Zapopan", "Mérida", "San Luis Potosí", "Querétaro", "Aguascalientes",
    "Hermosillo", "Mexicali", "Acapulco", "Cancún", "Culiacán", "Veracruz",
  ],

  // ── Central America & Caribbean ────────────────────────────────────────────
  "Guatemala": ["Guatemala City", "Mixco", "Villa Nueva", "Quetzaltenango"],
  "Costa Rica": ["San José", "Alajuela", "Desamparados", "Cartago"],
  "Panama": ["Panama City", "San Miguelito", "Colón"],
  "Cuba": ["Havana", "Santiago de Cuba", "Camagüey"],
  "Dominican Republic": ["Santo Domingo", "Santiago", "La Romana", "San Pedro"],
  "Puerto Rico": ["San Juan", "Bayamón", "Carolina", "Ponce"],
  "Jamaica": ["Kingston", "Montego Bay", "Portmore"],

  // ── South America ──────────────────────────────────────────────────────────
  "Brazil": [
    "São Paulo", "Rio de Janeiro", "Brasília", "Salvador", "Fortaleza",
    "Belo Horizonte", "Manaus", "Curitiba", "Recife", "Porto Alegre",
    "Belém", "Goiânia", "Guarulhos", "Campinas", "São Luís",
  ],
  "Argentina": [
    "Buenos Aires", "Córdoba", "Rosario", "Mendoza", "La Plata",
    "San Miguel de Tucumán", "Mar del Plata", "Salta",
  ],
  "Colombia": [
    "Bogotá", "Medellín", "Cali", "Barranquilla", "Cartagena",
    "Cúcuta", "Bucaramanga", "Pereira",
  ],
  "Chile": ["Santiago", "Valparaíso", "Concepción", "Antofagasta", "Temuco"],
  "Peru": ["Lima", "Arequipa", "Trujillo", "Chiclayo", "Piura"],
  "Venezuela": ["Caracas", "Maracaibo", "Valencia", "Barquisimeto"],
  "Ecuador": ["Guayaquil", "Quito", "Cuenca", "Manta"],
  "Bolivia": ["La Paz", "Santa Cruz de la Sierra", "Cochabamba"],
  "Paraguay": ["Asunción", "Ciudad del Este"],
  "Uruguay": ["Montevideo", "Salto"],

  // ── Western Europe ─────────────────────────────────────────────────────────
  "United Kingdom": [
    "London", "Birmingham", "Manchester", "Glasgow", "Leeds", "Liverpool",
    "Sheffield", "Edinburgh", "Bristol", "Leicester", "Cardiff", "Belfast",
    "Nottingham", "Newcastle", "Southampton", "Brighton", "Plymouth",
    "Coventry", "Reading", "Derby", "Stoke-on-Trent", "Wolverhampton",
    "Preston", "Oxford", "Cambridge", "Milton Keynes",
  ],
  "Germany": [
    "Berlin", "Hamburg", "Munich", "Cologne", "Frankfurt", "Stuttgart",
    "Düsseldorf", "Leipzig", "Dortmund", "Essen", "Bremen", "Dresden",
    "Hanover", "Nuremberg", "Duisburg", "Bochum", "Wuppertal", "Bielefeld",
    "Bonn", "Münster", "Karlsruhe", "Mannheim", "Augsburg", "Wiesbaden",
  ],
  "France": [
    "Paris", "Marseille", "Lyon", "Toulouse", "Nice", "Nantes", "Strasbourg",
    "Montpellier", "Bordeaux", "Lille", "Rennes", "Reims", "Saint-Étienne",
    "Toulon", "Le Havre", "Grenoble", "Dijon", "Angers", "Nîmes", "Villeurbanne",
  ],
  "Italy": [
    "Rome", "Milan", "Naples", "Turin", "Palermo", "Genoa", "Bologna",
    "Florence", "Bari", "Catania", "Venice", "Verona", "Messina", "Padua",
    "Trieste", "Taranto", "Brescia", "Prato",
  ],
  "Spain": [
    "Madrid", "Barcelona", "Valencia", "Seville", "Zaragoza", "Málaga",
    "Murcia", "Palma", "Las Palmas", "Bilbao", "Alicante", "Córdoba",
    "Valladolid", "Vigo", "Gijón", "Granada", "Vitoria-Gasteiz",
  ],
  "Netherlands": [
    "Amsterdam", "Rotterdam", "The Hague", "Utrecht", "Eindhoven",
    "Tilburg", "Groningen", "Almere", "Breda", "Nijmegen",
  ],
  "Belgium": ["Brussels", "Antwerp", "Ghent", "Charleroi", "Liège", "Bruges"],
  "Switzerland": ["Zurich", "Geneva", "Basel", "Bern", "Lausanne", "Winterthur"],
  "Austria": ["Vienna", "Graz", "Linz", "Salzburg", "Innsbruck"],
  "Portugal": ["Lisbon", "Porto", "Braga", "Amadora", "Setúbal", "Coimbra"],
  "Sweden": ["Stockholm", "Gothenburg", "Malmö", "Uppsala", "Västerås"],
  "Norway": ["Oslo", "Bergen", "Trondheim", "Stavanger", "Drammen"],
  "Denmark": ["Copenhagen", "Aarhus", "Odense", "Aalborg"],
  "Finland": ["Helsinki", "Espoo", "Tampere", "Vantaa", "Oulu"],
  "Ireland": ["Dublin", "Cork", "Limerick", "Galway", "Waterford"],
  "Greece": ["Athens", "Thessaloniki", "Patras", "Heraklion", "Larissa"],
  "Czech Republic": ["Prague", "Brno", "Ostrava", "Plzeň"],
  "Hungary": ["Budapest", "Debrecen", "Miskolc", "Szeged"],
  "Poland": [
    "Warsaw", "Kraków", "Łódź", "Wrocław", "Poznań", "Gdańsk",
    "Szczecin", "Bydgoszcz", "Lublin", "Katowice",
  ],
  "Romania": ["Bucharest", "Cluj-Napoca", "Timișoara", "Iași", "Constanța"],
  "Ukraine": ["Kyiv", "Kharkiv", "Odessa", "Dnipro", "Lviv"],
  "Russia": [
    "Moscow", "Saint Petersburg", "Novosibirsk", "Yekaterinburg", "Kazan",
    "Nizhny Novgorod", "Chelyabinsk", "Omsk", "Samara", "Rostov-on-Don",
  ],
  "Turkey": [
    "Istanbul", "Ankara", "Izmir", "Bursa", "Adana", "Gaziantep",
    "Konya", "Antalya", "Kayseri", "Mersin", "Eskişehir", "Diyarbakır",
  ],

  // ── Middle East ────────────────────────────────────────────────────────────
  "United Arab Emirates": [
    "Dubai", "Abu Dhabi", "Sharjah", "Ajman", "Ras Al Khaimah",
    "Fujairah", "Umm Al Quwain", "Al Ain",
  ],
  "Saudi Arabia": [
    "Riyadh", "Jeddah", "Mecca", "Medina", "Dammam", "Khobar",
    "Dhahran", "Tabuk", "Abha", "Hail", "Qatif", "Najran",
  ],
  "Qatar": ["Doha", "Al Rayyan", "Umm Salal", "Al Wakrah", "Al Khor"],
  "Kuwait": ["Kuwait City", "Salmiya", "Hawalli", "Farwaniya", "Ahmadi"],
  "Bahrain": ["Manama", "Riffa", "Muharraq", "Hamad Town"],
  "Oman": ["Muscat", "Seeb", "Salalah", "Sohar", "Nizwa"],
  "Jordan": ["Amman", "Zarqa", "Irbid", "Aqaba", "Madaba"],
  "Lebanon": ["Beirut", "Tripoli", "Sidon", "Tyre", "Jounieh"],
  "Israel": ["Tel Aviv", "Jerusalem", "Haifa", "Rishon LeZion", "Petah Tikva"],
  "Iraq": ["Baghdad", "Basra", "Mosul", "Erbil", "Sulaymaniyah"],
  "Egypt": [
    "Cairo", "Alexandria", "Giza", "Shubra El Kheima", "Port Said",
    "Suez", "Luxor", "Mansoura", "Tanta", "Asyut", "Hurghada",
  ],
  "Yemen": ["Sanaa", "Aden", "Taiz", "Hodeidah"],
  "Syria": ["Damascus", "Aleppo", "Homs", "Latakia"],
  "Iran": ["Tehran", "Mashhad", "Isfahan", "Karaj", "Tabriz", "Shiraz"],

  // ── South Asia ─────────────────────────────────────────────────────────────
  "Pakistan": [
    "Karachi", "Lahore", "Faisalabad", "Rawalpindi", "Islamabad",
    "Gujranwala", "Peshawar", "Multan", "Hyderabad", "Quetta",
    "Sialkot", "Bahawalpur", "Sargodha", "Abbottabad", "Sukkur",
  ],
  "India": [
    "Mumbai", "Delhi", "Bangalore", "Hyderabad", "Ahmedabad", "Chennai",
    "Kolkata", "Surat", "Pune", "Jaipur", "Lucknow", "Kanpur",
    "Nagpur", "Indore", "Thane", "Bhopal", "Visakhapatnam", "Coimbatore",
    "Patna", "Vadodara", "Agra", "Ludhiana", "Nashik", "Faridabad",
    "Meerut", "Varanasi", "Amritsar", "Aurangabad", "Madurai", "Kochi",
  ],
  "Bangladesh": [
    "Dhaka", "Chittagong", "Sylhet", "Rajshahi", "Khulna", "Comilla",
  ],
  "Sri Lanka": ["Colombo", "Kandy", "Galle", "Jaffna", "Negombo"],
  "Nepal": ["Kathmandu", "Pokhara", "Lalitpur", "Biratnagar"],
  "Afghanistan": ["Kabul", "Kandahar", "Herat", "Mazar-i-Sharif"],

  // ── Southeast Asia ─────────────────────────────────────────────────────────
  "Indonesia": [
    "Jakarta", "Surabaya", "Bandung", "Bekasi", "Medan", "Tangerang",
    "Depok", "Semarang", "Palembang", "Makassar", "Batam", "Bogor",
    "Padang", "Malang", "Yogyakarta", "Denpasar",
  ],
  "Philippines": [
    "Manila", "Quezon City", "Caloocan", "Davao City", "Cebu City",
    "Zamboanga City", "Taguig", "Antipolo", "Pasig", "Cagayan de Oro",
  ],
  "Vietnam": [
    "Ho Chi Minh City", "Hanoi", "Da Nang", "Hai Phong", "Can Tho",
    "Bien Hoa", "Vung Tau", "Nha Trang", "Hue",
  ],
  "Thailand": [
    "Bangkok", "Chiang Mai", "Nonthaburi", "Pak Kret", "Hat Yai",
    "Pattaya", "Phuket", "Khon Kaen", "Udon Thani",
  ],
  "Malaysia": [
    "Kuala Lumpur", "George Town", "Ipoh", "Shah Alam", "Petaling Jaya",
    "Johor Bahru", "Kota Kinabalu", "Subang Jaya", "Kuching", "Malacca",
  ],
  "Singapore": ["Singapore"],
  "Myanmar": ["Yangon", "Mandalay", "Naypyidaw", "Bago"],
  "Cambodia": ["Phnom Penh", "Siem Reap", "Sihanoukville"],
  "Laos": ["Vientiane", "Luang Prabang"],

  // ── East Asia ──────────────────────────────────────────────────────────────
  "China": [
    "Shanghai", "Beijing", "Chongqing", "Guangzhou", "Shenzhen", "Tianjin",
    "Wuhan", "Chengdu", "Nanjing", "Xi'an", "Hangzhou", "Shenyang",
    "Harbin", "Dongguan", "Foshan", "Zhengzhou", "Dalian", "Qingdao",
    "Jinan", "Changsha", "Kunming", "Nanning", "Xiamen", "Fuzhou",
  ],
  "Japan": [
    "Tokyo", "Osaka", "Nagoya", "Yokohama", "Sapporo", "Fukuoka",
    "Kobe", "Kyoto", "Kawasaki", "Saitama", "Hiroshima", "Sendai",
    "Chiba", "Kitakyushu",
  ],
  "South Korea": [
    "Seoul", "Busan", "Incheon", "Daegu", "Daejeon", "Gwangju",
    "Suwon", "Ulsan", "Changwon",
  ],
  "Taiwan": ["Taipei", "New Taipei", "Taichung", "Kaohsiung", "Tainan"],
  "Hong Kong": ["Hong Kong"],
  "Macau": ["Macau"],
  "Mongolia": ["Ulaanbaatar"],
  "North Korea": ["Pyongyang"],

  // ── Central Asia ───────────────────────────────────────────────────────────
  "Kazakhstan": ["Almaty", "Nur-Sultan", "Shymkent", "Karaganda"],
  "Uzbekistan": ["Tashkent", "Samarkand", "Namangan", "Andijan"],
  "Kyrgyzstan": ["Bishkek", "Osh"],
  "Tajikistan": ["Dushanbe", "Khujand"],
  "Turkmenistan": ["Ashgabat", "Türkmenabat"],
  "Azerbaijan": ["Baku", "Ganja", "Sumqayit"],
  "Georgia": ["Tbilisi", "Batumi", "Kutaisi"],
  "Armenia": ["Yerevan", "Gyumri"],

  // ── Africa ─────────────────────────────────────────────────────────────────
  "Nigeria": [
    "Lagos", "Kano", "Ibadan", "Abuja", "Port Harcourt", "Benin City",
    "Kaduna", "Maiduguri", "Zaria", "Aba",
  ],
  "South Africa": [
    "Johannesburg", "Cape Town", "Durban", "Pretoria", "Port Elizabeth",
    "Bloemfontein", "East London", "Nelspruit", "Kimberley",
  ],
  "Kenya": ["Nairobi", "Mombasa", "Kisumu", "Nakuru", "Eldoret"],
  "Ethiopia": ["Addis Ababa", "Dire Dawa", "Mekelle", "Gondar", "Hawassa"],
  "Ghana": ["Accra", "Kumasi", "Tamale", "Sekondi-Takoradi"],
  "Tanzania": ["Dar es Salaam", "Mwanza", "Arusha", "Dodoma"],
  "Uganda": ["Kampala", "Gulu", "Lira", "Mbarara"],
  "Morocco": ["Casablanca", "Fès", "Tangier", "Marrakech", "Salé", "Rabat"],
  "Algeria": ["Algiers", "Oran", "Constantine", "Annaba", "Batna"],
  "Tunisia": ["Tunis", "Sfax", "Sousse", "Kairouan"],
  "Libya": ["Tripoli", "Benghazi", "Misrata"],
  "Sudan": ["Khartoum", "Omdurman", "Port Sudan"],
  "Senegal": ["Dakar", "Thiès", "Saint-Louis"],
  "Ivory Coast": ["Abidjan", "Bouaké", "Daloa", "Yamoussoukro"],
  "Cameroon": ["Douala", "Yaoundé", "Bamenda"],
  "Zimbabwe": ["Harare", "Bulawayo", "Chitungwiza"],
  "Mozambique": ["Maputo", "Matola", "Beira", "Nampula"],
  "Angola": ["Luanda", "Huambo", "Lobito", "Benguela"],

  // ── Oceania ────────────────────────────────────────────────────────────────
  "Australia": [
    "Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide", "Gold Coast",
    "Newcastle", "Canberra", "Sunshine Coast", "Wollongong", "Hobart",
    "Darwin", "Geelong", "Townsville", "Cairns",
  ],
  "New Zealand": [
    "Auckland", "Wellington", "Christchurch", "Hamilton", "Tauranga",
    "Napier-Hastings", "Dunedin", "Palmerston North",
  ],
  "Papua New Guinea": ["Port Moresby", "Lae", "Mount Hagen"],
  "Fiji": ["Suva", "Nasinu", "Lautoka"],
};

// ─────────────────────────────────────────────────────────────────────────────
// All Business Categories (comprehensive)
// ─────────────────────────────────────────────────────────────────────────────
export const CATEGORIES: string[] = [
  // Food & Beverage
  "Restaurant", "Cafe", "Coffee Shop", "Fast Food", "Pizza Place",
  "Bakery", "Patisserie", "Ice Cream Shop", "Juice Bar", "Food Truck",
  "Catering Service", "Buffet Restaurant", "Sushi Restaurant",
  "Indian Restaurant", "Chinese Restaurant", "Italian Restaurant",
  "Thai Restaurant", "Mexican Restaurant", "Lebanese Restaurant",
  "Seafood Restaurant", "Steakhouse", "Vegan Restaurant",
  "Bar", "Nightclub", "Pub", "Lounge",

  // Health & Wellness
  "Dental Clinic", "Dentist", "Orthodontist", "Medical Clinic",
  "Hospital", "Pharmacy", "Optician", "Physiotherapy",
  "Chiropractor", "Dermatologist", "Psychiatrist", "Psychologist",
  "Gym", "Fitness Center", "Yoga Studio", "Pilates Studio",
  "Spa", "Massage Therapy", "Wellness Center", "Acupuncture",
  "Veterinary Clinic", "Pet Hospital", "Alternative Medicine",

  // Beauty & Personal Care
  "Hair Salon", "Barbershop", "Beauty Salon", "Nail Salon",
  "Makeup Artist", "Eyebrow Threading", "Laser Clinic",
  "Tanning Salon", "Tattoo Studio", "Piercing Studio",

  // Professional Services
  "Law Firm", "Lawyer", "Accounting Firm", "Accountant",
  "Tax Advisor", "Financial Advisor", "Insurance Agency",
  "Mortgage Broker", "Real Estate Agency", "Property Management",
  "Notary", "Immigration Consultant", "Business Consultant",
  "Marketing Agency", "PR Agency", "Advertising Agency",
  "IT Company", "Software Company", "Web Design Agency",
  "Graphic Design Studio", "Photography Studio", "Video Production",
  "Recruitment Agency", "HR Consulting", "Training Center",

  // Retail
  "Clothing Store", "Shoe Store", "Jewellery Store", "Watch Store",
  "Electronics Store", "Mobile Phone Shop", "Computer Store",
  "Furniture Store", "Home Décor Store", "Hardware Store",
  "Supermarket", "Grocery Store", "Organic Food Store",
  "Pharmacy", "Pet Store", "Toy Store", "Bookstore",
  "Sports Equipment Store", "Bicycle Shop", "Music Store",
  "Gift Shop", "Souvenir Shop", "Art Gallery", "Antique Shop",
  "Florist", "Plant Nursery",

  // Automotive
  "Car Dealership", "Auto Repair", "Car Wash", "Tire Shop",
  "Auto Parts Store", "Driving School", "Car Rental",
  "Motorcycle Dealership", "Truck Dealer",

  // Home Services
  "Plumber", "Electrician", "HVAC Contractor", "Roofer",
  "Painter", "Carpenter", "Landscaper", "Cleaning Service",
  "Pest Control", "Interior Designer", "Architect",
  "Moving Company", "Storage Facility", "Security Company",

  // Education
  "School", "Private School", "University", "College",
  "Tutoring Center", "Language School", "Music School",
  "Art School", "Cooking School", "Driving School",
  "Vocational Training", "Montessori", "Daycare",

  // Travel & Hospitality
  "Hotel", "Motel", "Hostel", "Bed & Breakfast", "Resort",
  "Vacation Rental", "Travel Agency", "Tour Operator",
  "Airport Transfer", "Taxi Service", "Car Rental",

  // Financial
  "Bank", "Credit Union", "Money Transfer", "Currency Exchange",
  "Investment Firm", "Pawn Shop", "Loan Company",

  // Technology
  "IT Support", "Computer Repair", "Phone Repair",
  "CCTV Installation", "Smart Home Installer", "Solar Panel Installer",
  "Internet Service Provider", "Cloud Services",

  // Events & Entertainment
  "Event Venue", "Wedding Venue", "Conference Center",
  "Event Planner", "Wedding Planner", "DJ Service",
  "Catering", "Florist", "Photography", "Videography",
  "Entertainment Agency", "Casino", "Bowling Alley",
  "Escape Room", "Laser Tag", "Trampoline Park",

  // Logistics
  "Courier Service", "Logistics Company", "Freight Company",
  "Warehouse", "Shipping Company", "Import Export",

  // Construction
  "Construction Company", "Building Contractor",
  "Civil Engineering", "Property Developer",
];

// Helper: get all country names sorted
export const COUNTRIES = Object.keys(GEO).sort();
