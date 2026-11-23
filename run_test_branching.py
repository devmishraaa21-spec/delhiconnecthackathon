import urllib.request, json
from routing.branching import get_corridor_branches

try:
    fleet_req = urllib.request.urlopen("http://localhost:8000/api/fleet?limit=1000")
    fleet = json.loads(fleet_req.read().decode())
except Exception as e:
    print("Could not fetch fleet:", e)
    fleet = []

res = get_corridor_branches("Connaught Place", "AIIMS", fleet)
print("Origin:", res["origin"]["name"], "-> Destination:", res["destination"]["name"])
print("Total branches:", res["total_branches"])
print("Total buses in transit between points:", res["total_buses_in_transit"])
for b in res["branches"]:
    print(f"  Branch: {b['name']} ({b['color']})")
    print(f"    Via: {b['via']} | Routes: {b['routes']}")
    print(f"    Active buses: {b['total_active_buses']} | Next bus ETA: {b['next_bus_eta_mins']} mins | Speed: {b['corridor_speed_kmh']} km/h")
    if b["buses"]:
        top = b["buses"][0]
        print(f"    Top bus: #{top['bus_id']} (Route {top['route_id']}) - {top['progress_pct']}% progress, ETA {top['eta_to_dest_mins']}m")
