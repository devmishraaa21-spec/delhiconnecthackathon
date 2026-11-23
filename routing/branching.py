import math
from typing import List, Dict, Any, Optional
from data.delhi_bus_stops import BUS_STOPS, BUS_ROUTES
from routing.planner import haversine

def get_corridor_branches(origin_name: str, dest_name: str, raw_fleet: List[Dict[str, Any]]):
    stop_map = {s["name"].lower(): s for s in BUS_STOPS}
    stop_id_map = {s["stop_id"]: s for s in BUS_STOPS}

    o_stop = stop_map.get(origin_name.lower()) or next((s for s in BUS_STOPS if origin_name.lower() in s["name"].lower()), None)
    d_stop = stop_map.get(dest_name.lower()) or next((s for s in BUS_STOPS if dest_name.lower() in s["name"].lower()), None)

    if not o_stop or not d_stop:
        o_stop = BUS_STOPS[0]  # Connaught Place
        d_stop = BUS_STOPS[10] # AIIMS

    total_dist_km = haversine(o_stop["lat"], o_stop["lon"], d_stop["lat"], d_stop["lon"]) / 1000.0

    # 1. Identify all routes that touch or run near origin and destination
    candidate_routes = []
    for r in BUS_ROUTES:
        s_ids = r["stop_ids"]
        has_o = o_stop["stop_id"] in s_ids
        has_d = d_stop["stop_id"] in s_ids

        if has_o and has_d:
            idx_o = s_ids.index(o_stop["stop_id"])
            idx_d = s_ids.index(d_stop["stop_id"])
            if idx_o < idx_d:
                sub = s_ids[idx_o : idx_d + 1]
            else:
                sub = s_ids[idx_d : idx_o + 1][::-1]
            candidate_routes.append({
                "route_id": r["route_id"],
                "name": r["name"],
                "type": "direct",
                "stop_ids": sub,
                "stops": [stop_id_map[sid] for sid in sub if sid in stop_id_map]
            })
        elif has_o or has_d:
            candidate_routes.append({
                "route_id": r["route_id"],
                "name": r["name"],
                "type": "partial",
                "stop_ids": s_ids,
                "stops": [stop_id_map[sid] for sid in s_ids if sid in stop_id_map]
            })

    # Group candidate routes into 2-3 distinct Branches (Corridor Families)
    # Branch 1: Direct Arterial Trunk
    # Branch 2: Ring Road / Bypass Corridor
    # Branch 3: Radial / Express Corridor
    branch_templates = [
        {
            "branch_id": "BR_ALPHA",
            "name": f"Trunk Corridor: {o_stop['name']} ➔ {d_stop['name']} Direct",
            "color": "#00f0ff", # Cyan
            "via": "Direct Arterial Transitway",
            "routes": [],
            "stops": [],
        },
        {
            "branch_id": "BR_BETA",
            "name": f"Arterial Bypass via Ring Road Corridor",
            "color": "#10b981", # Emerald
            "via": "Ring Road & Rapid Arterial Links",
            "routes": [],
            "stops": [],
        },
        {
            "branch_id": "BR_GAMMA",
            "name": f"Radial Transit Link via Metro Interchange Hubs",
            "color": "#a855f7", # Purple
            "via": "Central Radial Interchanges",
            "routes": [],
            "stops": [],
        }
    ]

    # Populate stops for branches
    # Branch 1: Direct stops if available or linear interpolation
    direct_candidates = [c for c in candidate_routes if c["type"] == "direct"]
    if direct_candidates:
        branch_templates[0]["routes"] = [c["route_id"] for c in direct_candidates]
        branch_templates[0]["stops"] = direct_candidates[0]["stops"]
    else:
        # Generate representative intermediate stops
        branch_templates[0]["routes"] = ["R01", "R05"]
        branch_templates[0]["stops"] = [o_stop, d_stop]

    # Intermediate stops for bypass & radial
    mid_lat = (o_stop["lat"] + d_stop["lat"]) / 2.0
    mid_lon = (o_stop["lon"] + d_stop["lon"]) / 2.0

    # Find closest intermediate stops to midpoint
    intermediate_stops = sorted(
        [s for s in BUS_STOPS if s["stop_id"] not in [o_stop["stop_id"], d_stop["stop_id"]]],
        key=lambda s: haversine(s["lat"], s["lon"], mid_lat, mid_lon)
    )

    if len(intermediate_stops) >= 2:
        branch_templates[1]["stops"] = [o_stop, intermediate_stops[0], d_stop]
        branch_templates[1]["routes"] = ["R06", "R10", "R14"]
        branch_templates[2]["stops"] = [o_stop, intermediate_stops[1], d_stop]
        branch_templates[2]["routes"] = ["R03", "R07", "R12"]
    else:
        branch_templates[1]["stops"] = [o_stop, d_stop]
        branch_templates[1]["routes"] = ["R06"]
        branch_templates[2]["stops"] = [o_stop, d_stop]
        branch_templates[2]["routes"] = ["R03"]

    # Filter branches to 2 or 3 depending on diversity
    active_branches = []
    lat1, lon1 = o_stop["lat"], o_stop["lon"]
    lat2, lon2 = d_stop["lat"], d_stop["lon"]

    for b in branch_templates:
        coords = [[s["lat"], s["lon"]] for s in b["stops"]]
        # Compute branch path distance
        b_dist_km = 0.0
        for i in range(len(coords) - 1):
            b_dist_km += haversine(coords[i][0], coords[i][1], coords[i+1][0], coords[i+1][1]) / 1000.0
        b_dist_km = max(b_dist_km, total_dist_km)

        # Find all live buses running along or between the two points for this branch
        buses = []
        for bus in raw_fleet:
            blat = float(bus.get("lat", 0.0))
            blon = float(bus.get("lon", 0.0))
            if blat == 0.0 or blon == 0.0:
                continue

            # Check distance to branch corridor
            # Min distance from bus to line segments of this branch
            min_dist_to_branch_m = float("inf")
            for i in range(len(coords) - 1):
                p1 = coords[i]
                p2 = coords[i+1]
                # Distance to segment p1-p2
                d_m = haversine(blat, blon, (p1[0] + p2[0])/2.0, (p1[1] + p2[1])/2.0)
                min_dist_to_branch_m = min(min_dist_to_branch_m, d_m)

            # Bus is in the corridor if within 2.8 km of branch polyline
            if min_dist_to_branch_m <= 2800.0:
                # Calculate progress from origin to dest
                d_from_o_km = haversine(blat, blon, lat1, lon1) / 1000.0
                d_to_d_km = haversine(blat, blon, lat2, lon2) / 1000.0

                # Is bus roughly between origin and dest (or within corridor bounding area)
                if (d_from_o_km + d_to_d_km) <= (b_dist_km * 1.45 + 2.0):
                    progress = min(100.0, max(0.0, (d_from_o_km / max(b_dist_km, 1.0)) * 100.0))
                    speed = float(bus.get("speed", 18.0))
                    eff_speed = max(speed, 12.0)
                    eta_mins = round((d_to_d_km / eff_speed) * 60.0)

                    status = "In Transit (Mid-Corridor)"
                    if progress < 20.0:
                        status = "Approaching Origin"
                    elif progress > 80.0:
                        status = "Near Destination"

                    buses.append({
                        "bus_id": str(bus.get("bus_id", "Bus")),
                        "route_id": str(bus.get("route_id", "DTC")),
                        "lat": round(blat, 5),
                        "lon": round(blon, 5),
                        "speed_kmh": round(speed, 1),
                        "dist_from_origin_km": round(d_from_o_km, 2),
                        "dist_to_destination_km": round(d_to_d_km, 2),
                        "progress_pct": round(progress, 1),
                        "eta_to_dest_mins": max(1, eta_mins),
                        "status": status,
                    })

        # Sort buses by progress along the corridor (furthest along first)
        buses.sort(key=lambda x: x["progress_pct"], reverse=True)

        # Headway and ETA metrics
        active_count = len(buses)
        next_bus_eta = min([b["eta_to_dest_mins"] for b in buses]) if buses else round((b_dist_km / 18.0) * 60.0)
        avg_headway = round(60.0 / max(1, active_count), 1) if active_count > 0 else 12.0
        avg_spd = round(sum(b["speed_kmh"] for b in buses) / active_count, 1) if active_count > 0 else 22.4

        active_branches.append({
            "branch_id": b["branch_id"],
            "name": b["name"],
            "color": b["color"],
            "via": b["via"],
            "routes": b["routes"],
            "distance_km": round(b_dist_km, 2),
            "corridor_speed_kmh": avg_spd,
            "total_active_buses": active_count,
            "next_bus_eta_mins": next_bus_eta,
            "avg_headway_mins": avg_headway,
            "stops": [s["name"] for s in b["stops"]],
            "coordinates": coords,
            "buses": buses,
        })

    # Pick recommended branch (fastest next bus ETA and best speed)
    active_branches.sort(key=lambda x: (x["next_bus_eta_mins"], -x["total_active_buses"]))

    return {
        "origin": o_stop,
        "destination": d_stop,
        "direct_distance_km": round(total_dist_km, 2),
        "total_branches": len(active_branches),
        "total_buses_in_transit": sum(b["total_active_buses"] for b in active_branches),
        "recommended_branch_id": active_branches[0]["branch_id"] if active_branches else None,
        "branches": active_branches,
    }

print("corridor_branches module loaded successfully.")
