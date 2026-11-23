import math
from data.delhi_bus_stops import BUS_STOPS, BUS_ROUTES

stop_dict = {s["stop_id"]: s for s in BUS_STOPS}

def find_routes_between(origin_name: str, dest_name: str):
    o_stop = next((s for s in BUS_STOPS if s["name"].lower() == origin_name.lower()), None)
    d_stop = next((s for s in BUS_STOPS if s["name"].lower() == dest_name.lower()), None)
    if not o_stop or not d_stop:
        return None, None, []

    direct_routes = []
    indirect_routes = []

    for r in BUS_ROUTES:
        s_ids = r["stop_ids"]
        if o_stop["stop_id"] in s_ids and d_stop["stop_id"] in s_ids:
            idx_o = s_ids.index(o_stop["stop_id"])
            idx_d = s_ids.index(d_stop["stop_id"])
            is_forward = idx_o < idx_d
            sub_stops = s_ids[idx_o:idx_d+1] if is_forward else s_ids[idx_d:idx_o+1][::-1]
            direct_routes.append({
                "route_id": r["route_id"],
                "name": r["name"],
                "is_direct": True,
                "is_forward": is_forward,
                "stops": [stop_dict[sid] for sid in sub_stops],
                "stop_count": len(sub_stops),
            })
        elif o_stop["stop_id"] in s_ids or d_stop["stop_id"] in s_ids:
            indirect_routes.append({
                "route_id": r["route_id"],
                "name": r["name"],
                "is_direct": False,
                "stops": [stop_dict[sid] for sid in s_ids],
                "stop_count": len(s_ids),
            })

    return o_stop, d_stop, direct_routes, indirect_routes

o, d, direct, indirect = find_routes_between("Connaught Place", "ISBT Kashmere Gate")
print(f"Direct routes between CP and ISBT Kashmere Gate: {len(direct)}")
for r in direct:
    print(f"  - {r['route_id']}: {r['name']} ({r['stop_count']} stops)")

o, d, direct, indirect = find_routes_between("Dwarka Sec-21", "Connaught Place")
print(f"Direct routes between Dwarka Sec-21 and CP: {len(direct)}")
for r in direct:
    print(f"  - {r['route_id']}: {r['name']} ({r['stop_count']} stops)")

o, d, direct, indirect = find_routes_between("Rohini Sec-3", "Connaught Place")
print(f"Direct routes between Rohini and CP: {len(direct)}")
for r in direct:
    print(f"  - {r['route_id']}: {r['name']} ({r['stop_count']} stops)")
