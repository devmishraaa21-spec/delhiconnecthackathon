"""
Delhi bus stops and routes data module.

Contains ~50 real Delhi bus stops with geographic coordinates and ~15 bus routes.
"""

BUS_STOPS: list[dict] = [
    # Central Delhi
    {"stop_id": "S01", "name": "Connaught Place", "lat": 28.6315, "lon": 77.2167},
    {"stop_id": "S02", "name": "Rajiv Chowk", "lat": 28.6328, "lon": 77.2195},
    {"stop_id": "S03", "name": "Janpath", "lat": 28.6256, "lon": 77.2182},
    {"stop_id": "S04", "name": "Mandi House", "lat": 28.6258, "lon": 77.2340},
    {"stop_id": "S05", "name": "India Gate", "lat": 28.6129, "lon": 77.2295},
    # Old Delhi / Congested Areas
    {"stop_id": "S06", "name": "ISBT Kashmere Gate", "lat": 28.6672, "lon": 77.2284},
    {"stop_id": "S07", "name": "Chandni Chowk", "lat": 28.6506, "lon": 77.2301},
    {"stop_id": "S08", "name": "Red Fort", "lat": 28.6562, "lon": 77.2410},
    {"stop_id": "S09", "name": "Jama Masjid", "lat": 28.6507, "lon": 77.2334},
    {"stop_id": "S10", "name": "Delhi Gate", "lat": 28.6388, "lon": 77.2414},
    # South Delhi
    {"stop_id": "S11", "name": "AIIMS", "lat": 28.5672, "lon": 77.2100},
    {"stop_id": "S12", "name": "INA Market", "lat": 28.5744, "lon": 77.2089},
    {"stop_id": "S13", "name": "Nehru Place", "lat": 28.5491, "lon": 77.2533},
    {"stop_id": "S14", "name": "Saket", "lat": 28.5245, "lon": 77.2066},
    {"stop_id": "S15", "name": "Hauz Khas", "lat": 28.5494, "lon": 77.2001},
    {"stop_id": "S16", "name": "Green Park", "lat": 28.5593, "lon": 77.2066},
    {"stop_id": "S17", "name": "Lajpat Nagar", "lat": 28.5700, "lon": 77.2432},
    {"stop_id": "S18", "name": "Defence Colony", "lat": 28.5742, "lon": 77.2340},
    # East Delhi
    {"stop_id": "S19", "name": "ITO", "lat": 28.6289, "lon": 77.2405},
    {"stop_id": "S20", "name": "Pragati Maidan", "lat": 28.6168, "lon": 77.2490},
    {"stop_id": "S21", "name": "Akshardham", "lat": 28.6127, "lon": 77.2773},
    {"stop_id": "S22", "name": "Anand Vihar ISBT", "lat": 28.6468, "lon": 77.3161},
    {"stop_id": "S23", "name": "Laxmi Nagar", "lat": 28.6304, "lon": 77.2773},
    {"stop_id": "S24", "name": "Preet Vihar", "lat": 28.6364, "lon": 77.2956},
    # West Delhi
    {"stop_id": "S25", "name": "Rajouri Garden", "lat": 28.6492, "lon": 77.1225},
    {"stop_id": "S26", "name": "Janakpuri", "lat": 28.6219, "lon": 77.0862},
    {"stop_id": "S27", "name": "Tilak Nagar", "lat": 28.6407, "lon": 77.0989},
    {"stop_id": "S28", "name": "Subhash Nagar", "lat": 28.6450, "lon": 77.1143},
    {"stop_id": "S29", "name": "Punjabi Bagh", "lat": 28.6688, "lon": 77.1308},
    {"stop_id": "S30", "name": "Paschim Vihar", "lat": 28.6714, "lon": 77.1047},
    # North Delhi
    {"stop_id": "S31", "name": "Civil Lines", "lat": 28.6803, "lon": 77.2240},
    {"stop_id": "S32", "name": "Model Town", "lat": 28.7146, "lon": 77.1932},
    {"stop_id": "S33", "name": "GTB Nagar", "lat": 28.6981, "lon": 77.2104},
    {"stop_id": "S34", "name": "Pitampura", "lat": 28.7025, "lon": 77.1360},
    {"stop_id": "S35", "name": "Rohini Sec-3", "lat": 28.7152, "lon": 77.1181},
    {"stop_id": "S36", "name": "Rithala", "lat": 28.7207, "lon": 77.1070},
    # Dwarka / Airport side
    {"stop_id": "S37", "name": "Dwarka Sec-21", "lat": 28.5522, "lon": 77.0582},
    {"stop_id": "S38", "name": "Dwarka Sec-14", "lat": 28.5853, "lon": 77.0439},
    {"stop_id": "S39", "name": "Dwarka Sec-9", "lat": 28.5812, "lon": 77.0677},
    {"stop_id": "S40", "name": "Palam", "lat": 28.5916, "lon": 77.0892},
    # Ring Road Corridor
    {"stop_id": "S41", "name": "Dhaula Kuan", "lat": 28.5924, "lon": 77.1587},
    {"stop_id": "S42", "name": "Naraina Vihar", "lat": 28.6256, "lon": 77.1437},
    {"stop_id": "S43", "name": "Moti Bagh", "lat": 28.5839, "lon": 77.1737},
    {"stop_id": "S44", "name": "RK Puram", "lat": 28.5676, "lon": 77.1766},
    {"stop_id": "S45", "name": "Munirka", "lat": 28.5565, "lon": 77.1734},
    {"stop_id": "S46", "name": "Vasant Kunj", "lat": 28.5285, "lon": 77.1573},
    # Additional Important Stops
    {"stop_id": "S47", "name": "Karol Bagh", "lat": 28.6514, "lon": 77.1907},
    {"stop_id": "S48", "name": "Patel Nagar", "lat": 28.6519, "lon": 77.1655},
    {"stop_id": "S49", "name": "Ashram", "lat": 28.5796, "lon": 77.2588},
    {"stop_id": "S50", "name": "Sarai Kale Khan ISBT", "lat": 28.5894, "lon": 77.2567},
]

# Zone classification for speed modelling
CONGESTED_STOPS = {"S06", "S07", "S08", "S09", "S10"}  # Old Delhi area
RING_ROAD_STOPS = {"S41", "S42", "S43", "S44", "S45", "S46"}  # Ring Road
EXPRESSWAY_STOPS = {"S37", "S38", "S39", "S40"}  # Dwarka expressway corridor

BUS_ROUTES: list[dict] = [
    {
        "route_id": "R01",
        "name": "Connaught Place - ISBT Kashmere Gate via Chandni Chowk",
        "stop_ids": ["S01", "S02", "S19", "S10", "S09", "S07", "S06"],
    },
    {
        "route_id": "R02",
        "name": "AIIMS - Nehru Place via Lajpat Nagar",
        "stop_ids": ["S11", "S12", "S16", "S15", "S17", "S18", "S13"],
    },
    {
        "route_id": "R03",
        "name": "Dwarka Sec-21 - Connaught Place via Dhaula Kuan",
        "stop_ids": ["S37", "S38", "S39", "S40", "S41", "S43", "S47", "S48", "S01"],
    },
    {
        "route_id": "R04",
        "name": "ISBT Kashmere Gate - Anand Vihar ISBT",
        "stop_ids": ["S06", "S31", "S08", "S19", "S20", "S21", "S23", "S24", "S22"],
    },
    {
        "route_id": "R05",
        "name": "Rohini - Connaught Place via Pitampura",
        "stop_ids": ["S36", "S35", "S34", "S30", "S29", "S47", "S02", "S01"],
    },
    {
        "route_id": "R06",
        "name": "Ring Road: Dhaula Kuan - Sarai Kale Khan",
        "stop_ids": ["S41", "S43", "S44", "S45", "S11", "S12", "S17", "S49", "S50"],
    },
    {
        "route_id": "R07",
        "name": "Janakpuri - ITO via Rajouri Garden",
        "stop_ids": ["S26", "S27", "S28", "S25", "S48", "S47", "S02", "S19"],
    },
    {
        "route_id": "R08",
        "name": "Model Town - AIIMS via Karol Bagh",
        "stop_ids": ["S32", "S33", "S31", "S06", "S07", "S02", "S01", "S03", "S16", "S11"],
    },
    {
        "route_id": "R09",
        "name": "Saket - India Gate via AIIMS",
        "stop_ids": ["S14", "S15", "S16", "S11", "S12", "S03", "S05"],
    },
    {
        "route_id": "R10",
        "name": "Dwarka Sec-21 - ISBT Kashmere Gate Express",
        "stop_ids": ["S37", "S38", "S40", "S41", "S42", "S29", "S47", "S02", "S06"],
    },
    {
        "route_id": "R11",
        "name": "Nehru Place - Anand Vihar via Ashram",
        "stop_ids": ["S13", "S49", "S50", "S20", "S21", "S23", "S24", "S22"],
    },
    {
        "route_id": "R12",
        "name": "Vasant Kunj - Connaught Place",
        "stop_ids": ["S46", "S45", "S44", "S43", "S41", "S48", "S47", "S01"],
    },
    {
        "route_id": "R13",
        "name": "Rithala - Red Fort via Punjabi Bagh",
        "stop_ids": ["S36", "S35", "S34", "S30", "S29", "S25", "S28", "S47", "S07", "S08"],
    },
    {
        "route_id": "R14",
        "name": "Sarai Kale Khan - Dwarka via Ring Road",
        "stop_ids": ["S50", "S49", "S17", "S18", "S11", "S44", "S43", "S41", "S40", "S39", "S37"],
    },
    {
        "route_id": "R15",
        "name": "Laxmi Nagar - Saket via ITO",
        "stop_ids": ["S23", "S19", "S10", "S04", "S05", "S03", "S16", "S15", "S14"],
    },
]
