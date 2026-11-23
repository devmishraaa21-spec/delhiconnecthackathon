"""Road segment management for Delhi bus traffic model."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class RoadSegment:
    """Represents a single road segment in the Delhi road network."""

    segment_id: str
    start_lat: float
    start_lon: float
    end_lat: float
    end_lon: float
    length_m: float
    road_name: str
    road_type: str  # arterial / expressway / local / congested_zone


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return distance in metres between two lat/lon points."""
    R = 6_371_000.0  # Earth radius in metres
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(max(0.0, 1.0 - a)))
    return R * c


def create_delhi_road_network() -> List[RoadSegment]:
    """Create ~100 road segments representing major Delhi roads with realistic coordinates.

    Covers Ring Road, Outer Ring Road, Vikas Marg, Mathura Road, Aurobindo Marg,
    GT Road, NH-48, Old Delhi / Chandni Chowk, Central Delhi, and connecting arterials.
    Key intersection nodes share coordinates to ensure a well-connected routing graph.
    """
    # Key Hub Coordinates:
    # CP: (28.6315, 77.2167)
    # Rajiv Chowk: (28.6328, 77.2195)
    # Mandi House: (28.6258, 77.2340)
    # ITO: (28.6289, 77.2405)
    # Delhi Gate: (28.6388, 77.2414)
    # Jama Masjid: (28.6507, 77.2334)
    # Chandni Chowk: (28.6506, 77.2301)
    # Red Fort: (28.6562, 77.2410)
    # Kashmere Gate ISBT: (28.6672, 77.2284)
    # Dhaula Kuan: (28.5924, 77.1587)
    # Moti Bagh: (28.5839, 77.1737)
    # AIIMS: (28.5672, 77.2100)
    # Lajpat Nagar: (28.5700, 77.2432)
    # Ashram: (28.5796, 77.2588)
    # Sarai Kale Khan: (28.5894, 77.2567)
    # Nehru Place: (28.5491, 77.2533)
    # Saket: (28.5245, 77.2066)
    # Hauz Khas: (28.5494, 77.2001)

    corridors: list[tuple[str, str, list[tuple[float, float]]]] = [
        # 1. Inner Ring Road (Closed loop, ~18 segments)
        ("Ring Road", "arterial", [
            (28.5924, 77.1587),  # Dhaula Kuan
            (28.5839, 77.1737),  # Moti Bagh
            (28.5744, 77.1950),  # South Ext / Safdarjung
            (28.5672, 77.2100),  # AIIMS / Andrews Ganj
            (28.5700, 77.2432),  # Lajpat Nagar
            (28.5796, 77.2588),  # Ashram Chowk
            (28.5894, 77.2567),  # Sarai Kale Khan ISBT
            (28.6080, 77.2510),  # Pragati Maidan / IP Flyover
            (28.6289, 77.2405),  # ITO
            (28.6500, 77.2380),  # Shanti Van / Yamuna Bazar
            (28.6672, 77.2284),  # ISBT Kashmere Gate
            (28.6850, 77.2150),  # Majnu Ka Tila
            (28.7050, 77.2000),  # Wazirabad Bridge
            (28.7100, 77.1800),  # Mukarba Chowk / GTK Bypass
            (28.6980, 77.1650),  # Azadpur
            (28.6800, 77.1500),  # Shalimar Bagh
            (28.6688, 77.1308),  # Punjabi Bagh
            (28.6450, 77.1380),  # Raja Garden
            (28.6256, 77.1437),  # Naraina Vihar
            (28.5924, 77.1587),  # Dhaula Kuan (closed loop)
        ]),

        # 2. Outer Ring Road (~16 segments)
        ("Outer Ring Road", "expressway", [
            (28.5285, 77.1573),  # Vasant Kunj
            (28.5400, 77.1650),  # Ber Sarai
            (28.5565, 77.1734),  # Munirka
            (28.5620, 77.1850),  # IIT Flyover
            (28.5540, 77.2080),  # Panchsheel Park
            (28.5491, 77.2300),  # Chirag Delhi
            (28.5491, 77.2533),  # Nehru Place
            (28.5520, 77.2700),  # Kalkaji / Okhla
            (28.5650, 77.2850),  # Kalindi Kunj
            (28.6000, 77.2950),  # Mayur Vihar
            (28.6250, 77.3050),  # Ghazipur
            (28.6468, 77.3161),  # Anand Vihar
            (28.6800, 77.2750),  # Shahdara
            (28.7050, 77.2500),  # Yamuna Vihar
            (28.7050, 77.2000),  # Wazirabad Jn
            (28.7025, 77.1360),  # Pitampura / Rohini
            (28.6714, 77.1047),  # Paschim Vihar
            (28.6492, 77.1225),  # Rajouri Garden
        ]),

        # 3. Central Delhi & Corridors (~12 segments)
        ("Connaught Place Outer", "arterial", [
            (28.6315, 77.2167),  # CP Inner/Outer
            (28.6328, 77.2195),  # Rajiv Chowk
            (28.6256, 77.2182),  # Janpath
            (28.6258, 77.2340),  # Mandi House
            (28.6289, 77.2405),  # ITO
        ]),
        ("Barakhamba - India Gate", "arterial", [
            (28.6315, 77.2167),  # CP
            (28.6258, 77.2340),  # Mandi House
            (28.6129, 77.2295),  # India Gate
            (28.5920, 77.2280),  # Lodhi Road Junction
        ]),
        ("Kartavya Path", "arterial", [
            (28.6145, 77.1985),  # Rashtrapati Bhavan
            (28.6135, 77.2085),  # Vijay Chowk
            (28.6129, 77.2295),  # India Gate
            (28.6168, 77.2490),  # Pragati Maidan
        ]),

        # 4. Old Delhi & Heritage Core (Congested Zones, ~10 segments)
        ("Chandni Chowk Road", "congested_zone", [
            (28.6506, 77.2301),  # Chandni Chowk
            (28.6507, 77.2334),  # Jama Masjid
            (28.6562, 77.2410),  # Red Fort
            (28.6672, 77.2284),  # ISBT Kashmere Gate
        ]),
        ("Netaji Subhash Marg", "congested_zone", [
            (28.6388, 77.2414),  # Delhi Gate
            (28.6450, 77.2410),  # Turkman Gate
            (28.6507, 77.2334),  # Jama Masjid
            (28.6562, 77.2410),  # Red Fort
        ]),
        ("Chawri Bazaar Corridors", "congested_zone", [
            (28.6480, 77.2240),  # Ajmeri Gate
            (28.6495, 77.2280),  # Chawri Bazaar
            (28.6506, 77.2301),  # Chandni Chowk
        ]),

        # 5. East Delhi: Vikas Marg & Trans-Yamuna (~8 segments)
        ("Vikas Marg", "arterial", [
            (28.6289, 77.2405),  # ITO
            (28.6300, 77.2550),  # Laxmi Nagar Shakarpur
            (28.6304, 77.2773),  # Laxmi Nagar Metro
            (28.6364, 77.2956),  # Preet Vihar
            (28.6420, 77.3080),  # Karkardooma
            (28.6468, 77.3161),  # Anand Vihar ISBT
        ]),
        ("Noida Link Road", "expressway", [
            (28.6080, 77.2510),  # IP Flyover / Ring Road
            (28.6127, 77.2773),  # Akshardham
            (28.6050, 77.2950),  # Mayur Vihar Phase 1
            (28.5800, 77.3150),  # Noida Border (Chilla)
        ]),

        # 6. South Delhi Corridors (~12 segments)
        ("Aurobindo Marg", "arterial", [
            (28.6129, 77.2295),  # India Gate
            (28.5930, 77.2150),  # Jor Bagh
            (28.5744, 77.2089),  # INA Market
            (28.5672, 77.2100),  # AIIMS
            (28.5593, 77.2066),  # Green Park
            (28.5494, 77.2001),  # Hauz Khas
            (28.5245, 77.2066),  # Saket Metro
            (28.5150, 77.1950),  # Qutub Minar / Mehrauli
        ]),
        ("Mathura Road (NH-2)", "arterial", [
            (28.6289, 77.2405),  # ITO
            (28.6168, 77.2490),  # Pragati Maidan
            (28.5894, 77.2567),  # Nizamuddin / Sarai Kale Khan
            (28.5796, 77.2588),  # Ashram Chowk
            (28.5491, 77.2533),  # Nehru Place Junction
            (28.5150, 77.2950),  # Badarpur Border
        ]),
        ("Lala Lajpat Rai Marg", "arterial", [
            (28.5700, 77.2432),  # Lajpat Nagar
            (28.5742, 77.2340),  # Defence Colony
            (28.5491, 77.2533),  # Nehru Place
        ]),

        # 7. West Delhi & Rohtak Road (~12 segments)
        ("Pusa Road - Patel Road", "arterial", [
            (28.6315, 77.2167),  # CP
            (28.6400, 77.1980),  # Karol Bagh Metro
            (28.6514, 77.1907),  # Karol Bagh
            (28.6519, 77.1655),  # Patel Nagar
            (28.6550, 77.1500),  # Shadipur
            (28.6450, 77.1380),  # Raja Garden / Ring Road
        ]),
        ("Shivaji Marg / Najafgarh Road", "arterial", [
            (28.6450, 77.1380),  # Raja Garden
            (28.6492, 77.1225),  # Rajouri Garden
            (28.6450, 77.1143),  # Subhash Nagar
            (28.6407, 77.0989),  # Tilak Nagar
            (28.6219, 77.0862),  # Janakpuri
        ]),
        ("Rohtak Road (NH-10)", "arterial", [
            (28.6688, 77.1308),  # Punjabi Bagh
            (28.6750, 77.1150),  # Madipur
            (28.6714, 77.1047),  # Paschim Vihar
            (28.6800, 77.0800),  # Nangloi
        ]),

        # 8. North Delhi: GT Road (~6 segments)
        ("GT Karnal Road (NH-1)", "arterial", [
            (28.6672, 77.2284),  # ISBT Kashmere Gate
            (28.6803, 77.2240),  # Civil Lines
            (28.6981, 77.2104),  # GTB Nagar / Delhi University
            (28.7146, 77.1932),  # Model Town
            (28.7100, 77.1800),  # Mukarba Chowk
            (28.7500, 77.1450),  # Alipur GT Road
        ]),

        # 9. Airport & Dwarka Expressway Corridor (~10 segments)
        ("NH-48 Expressway (Delhi-Gurgaon)", "expressway", [
            (28.5924, 77.1587),  # Dhaula Kuan
            (28.5650, 77.1400),  # Vasant Vihar
            (28.5450, 77.1250),  # Mahipalpur Flyover
            (28.5350, 77.1050),  # Aerocity
            (28.5522, 77.0582),  # Dwarka Sec-21
        ]),
        ("Dwarka Sector Roads", "local", [
            (28.5522, 77.0582),  # Dwarka Sec-21
            (28.5812, 77.0677),  # Dwarka Sec-9
            (28.5853, 77.0439),  # Dwarka Sec-14
            (28.5916, 77.0892),  # Palam
            (28.6219, 77.0862),  # Janakpuri West
        ]),

        # 10. Local Connectors & South Delhi Local (~8 segments)
        ("Mehrauli-Badarpur Road", "local", [
            (28.5150, 77.1950),  # Mehrauli
            (28.5245, 77.2066),  # Saket
            (28.5180, 77.2350),  # Khanpur
            (28.5150, 77.2650),  # Hamdard Nagar
            (28.5150, 77.2950),  # Badarpur
        ]),
        ("Barapullah Elevated Corridor", "expressway", [
            (28.5744, 77.2089),  # INA / AIIMS
            (28.5742, 77.2340),  # JLN Stadium / Jangpura
            (28.5894, 77.2567),  # Sarai Kale Khan
        ]),

        # 11. Rohini & Outer North Corridors
        ("Bhagwan Mahavir Marg (Rohini)", "arterial", [
            (28.7025, 77.1360),  # Pitampura
            (28.7152, 77.1181),  # Rohini Sec-3
            (28.7207, 77.1070),  # Rithala
            (28.6714, 77.1047),  # Paschim Vihar
        ]),

        # 12. South-West Arterial (RK Puram / Munirka)
        ("Africa Avenue - RK Puram", "arterial", [
            (28.5839, 77.1737),  # Moti Bagh
            (28.5676, 77.1766),  # RK Puram
            (28.5565, 77.1734),  # Munirka
            (28.5285, 77.1573),  # Vasant Kunj
        ]),
    ]

    segments: list[RoadSegment] = []
    seg_counter = 0

    for road_name, road_type, waypoints in corridors:
        for i in range(len(waypoints) - 1):
            slat, slon = waypoints[i]
            elat, elon = waypoints[i + 1]
            dist_m = haversine_m(slat, slon, elat, elon)
            seg_counter += 1
            segments.append(
                RoadSegment(
                    segment_id=f"seg_{seg_counter:04d}",
                    start_lat=slat,
                    start_lon=slon,
                    end_lat=elat,
                    end_lon=elon,
                    length_m=round(dist_m, 1),
                    road_name=road_name,
                    road_type=road_type,
                )
            )

    return segments


def _point_to_segment_distance(
    px: float, py: float,
    ax: float, ay: float,
    bx: float, by: float,
) -> float:
    """Perpendicular distance (metres) from GPS point P(lat, lon) to segment A-B.

    Uses flat-Earth projection centered around Delhi (lat ~28.6 N).
    """
    cos_lat = math.cos(math.radians(28.6))
    scale_x = 111_320.0 * cos_lat  # metres per deg lon
    scale_y = 110_540.0            # metres per deg lat

    # Convert coordinates to local Cartesian metres (x=lon, y=lat)
    px_m, py_m = (py - 77.0) * scale_x, (px - 28.5) * scale_y
    ax_m, ay_m = (ay - 77.0) * scale_x, (ax - 28.5) * scale_y
    bx_m, by_m = (by - 77.0) * scale_x, (bx - 28.5) * scale_y

    dx = bx_m - ax_m
    dy = by_m - ay_m
    len_sq = dx * dx + dy * dy

    if len_sq < 1e-6:
        return math.hypot(px_m - ax_m, py_m - ay_m)

    # Projection factor clamped to [0, 1] for segment endpoints
    t = max(0.0, min(1.0, ((px_m - ax_m) * dx + (py_m - ay_m) * dy) / len_sq))
    proj_x = ax_m + t * dx
    proj_y = ay_m + t * dy

    return math.hypot(px_m - proj_x, py_m - proj_y)


def snap_to_segment(lat: float, lon: float, segments: List[RoadSegment]) -> RoadSegment:
    """Find nearest road segment for a GPS point using perpendicular distance."""
    if not segments:
        raise ValueError("Cannot snap to an empty segments list")

    best_seg = segments[0]
    best_dist = float("inf")

    for seg in segments:
        dist = _point_to_segment_distance(
            lat, lon,
            seg.start_lat, seg.start_lon,
            seg.end_lat, seg.end_lon,
        )
        if dist < best_dist:
            best_dist = dist
            best_seg = seg

    return best_seg
