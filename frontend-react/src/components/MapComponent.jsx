import React, { useEffect, useRef } from 'react';
import L from 'leaflet';

// Congestion colors
const CONGESTION_COLORS = {
  free_flow: '#2ecc71',
  moderate: '#f1c40f',
  heavy: '#e67e22',
  gridlock: '#e74c3c',
  severe: '#e74c3c',
};

export default function MapComponent({
  fleet,
  segments,
  stops,
  route,
  corridorFocus,
  layerVisibility,
  onMapClick,
  clickPoints,
}) {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);

  // Layers references
  const roadLayerGroupRef = useRef(null);
  const fleetLayerGroupRef = useRef(null);
  const stopsLayerGroupRef = useRef(null);
  const walkshedLayerGroupRef = useRef(null);
  const routeLayerGroupRef = useRef(null);
  const clickMarkersGroupRef = useRef(null);

  // 1. Initialize Map once
  const onMapClickRef = useRef(onMapClick);
  useEffect(() => {
    onMapClickRef.current = onMapClick;
  }, [onMapClick]);

  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    const map = L.map(mapContainerRef.current, {
      center: [28.6139, 77.2090],
      zoom: 12,
      zoomControl: true,
    });
    mapInstanceRef.current = map;

    // Basemaps
    const streetTiles = L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; CARTO',
      maxZoom: 19,
    }).addTo(map);

    const satelliteTiles = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
      attribution: 'Tiles &copy; Esri',
      maxZoom: 19,
    });

    const lightTiles = L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; CARTO &copy; OpenStreetMap',
      maxZoom: 19,
    });

    const baseMaps = {
      '🗺️ Street Map': streetTiles,
      '🛰️ Esri Satellite': satelliteTiles,
      '☀️ Clean Light': lightTiles,
    };

    // Layer groups
    roadLayerGroupRef.current = L.layerGroup().addTo(map);
    fleetLayerGroupRef.current = L.layerGroup().addTo(map);
    stopsLayerGroupRef.current = L.layerGroup().addTo(map);
    walkshedLayerGroupRef.current = L.layerGroup().addTo(map);
    routeLayerGroupRef.current = L.layerGroup().addTo(map);
    clickMarkersGroupRef.current = L.layerGroup().addTo(map);

    const overlays = {
      '🛣️ Road Velocities': roadLayerGroupRef.current,
      '🚌 Live Bus Fleet': fleetLayerGroupRef.current,
      '🚏 Bus Stops': stopsLayerGroupRef.current,
      '🚶 500m Walksheds': walkshedLayerGroupRef.current,
      '⚡ Active Route': routeLayerGroupRef.current,
    };

    L.control.layers(baseMaps, overlays, { collapsed: true, position: 'topright' }).addTo(map);

    setTimeout(() => {
      if (map) map.invalidateSize();
    }, 200);

    // Click handler for Click-to-Route
    map.on('click', (e) => {
      if (onMapClickRef.current) {
        onMapClickRef.current(e.latlng.lat, e.latlng.lng);
      }
    });

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // 2. Pan / FlyTo on Corridor Selection
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map || !corridorFocus) return;

    const corridorCoords = {
      'all': [[28.6139, 77.2090], 12],
      'central': [[28.6200, 77.2180], 13],
      'north': [[28.6672, 77.2284], 14],
      'south': [[28.5672, 77.2100], 13],
      'east': [[28.6364, 77.2956], 13],
      'west': [[28.5950, 77.0700], 13],
    };

    const target = corridorCoords[corridorFocus] || corridorCoords['all'];
    map.flyTo(target[0], target[1], { duration: 1.2, easeLinearity: 0.25 });
  }, [corridorFocus]);

  // 3. Render Road Segments
  useEffect(() => {
    const group = roadLayerGroupRef.current;
    if (!group) return;
    group.clearLayers();

    if (!layerVisibility.segments || !segments) return;

    segments.forEach((seg) => {
      const color = CONGESTION_COLORS[seg.congestion_level] || '#2ecc71';
      const weight = ['heavy', 'gridlock', 'severe'].includes(seg.congestion_level) ? 6 : 4;

      const polyline = L.polyline(seg.coordinates, {
        color: color,
        weight: weight,
        opacity: 0.88,
      });

      polyline.bindPopup(`
        <div style="font-family: inherit; font-size: 12px; min-width: 170px;">
          <div style="font-weight: 700; color: ${color}; font-size: 13px; margin-bottom: 4px;">
            🛣️ ${seg.road_name}
          </div>
          <div><b>Speed:</b> ${seg.speed_kmh} km/h</div>
          <div><b>State:</b> ${seg.congestion_level.toUpperCase()}</div>
          <div><b>Type:</b> ${seg.road_type} (${Math.round(seg.length_m)}m)</div>
        </div>
      `);

      polyline.bindTooltip(`${seg.road_name}: ${seg.speed_kmh} km/h`, { sticky: true });
      polyline.addTo(group);
    });
  }, [segments, layerVisibility.segments]);

  // 4. Render Live Bus Fleet
  useEffect(() => {
    const group = fleetLayerGroupRef.current;
    if (!group) return;
    group.clearLayers();

    if (!layerVisibility.fleet || !fleet) return;

    // Render up to 500 active buses smoothly
    fleet.slice(0, 500).forEach((bus) => {
      const spd = bus.speed || 0;
      let color = '#ef4444'; // Slow / Dwell
      if (spd >= 20) color = '#10b981'; // Free Flow
      else if (spd >= 5) color = '#f59e0b'; // Moderate

      const marker = L.circleMarker([bus.lat, bus.lon], {
        radius: 6,
        fillColor: color,
        color: '#ffffff',
        weight: 1.5,
        opacity: 0.9,
        fillOpacity: 0.85,
      });

      marker.bindPopup(`
        <div style="font-family: inherit; font-size: 12px; min-width: 160px;">
          <div style="font-weight: 700; color: #ff9933; font-size: 13px; margin-bottom: 4px;">
            🚌 Bus #${bus.bus_id}
          </div>
          <div><b>Route:</b> ${bus.route_id}</div>
          <div><b>Velocity:</b> <span style="font-weight: bold; color: ${color};">${spd.toFixed(1)} km/h</span></div>
          <div><b>Status:</b> ${bus.status}</div>
        </div>
      `);

      marker.bindTooltip(`Bus #${bus.bus_id} (${spd.toFixed(1)} km/h)`, { direction: 'top' });
      marker.addTo(group);
    });
  }, [fleet, layerVisibility.fleet]);

  // 5. Render Bus Stops & Walksheds
  useEffect(() => {
    const stopsGroup = stopsLayerGroupRef.current;
    const walkshedGroup = walkshedLayerGroupRef.current;
    if (!stopsGroup || !walkshedGroup) return;

    stopsGroup.clearLayers();
    walkshedGroup.clearLayers();

    if (!stops) return;

    if (layerVisibility.stops) {
      stops.forEach((stop) => {
        const marker = L.circleMarker([stop.lat, stop.lon], {
          radius: 5,
          fillColor: '#38bdf8',
          color: '#0284c7',
          weight: 1.5,
          fillOpacity: 0.9,
        });

        marker.bindPopup(`
          <div style="font-family: inherit; font-size: 12px; min-width: 160px;">
            <div style="font-weight: 700; color: #38bdf8; font-size: 13px; margin-bottom: 4px;">
              🚏 ${stop.name}
            </div>
            <div><b>Stop ID:</b> ${stop.stop_id}</div>
            <div><b>Routes:</b> ${stop.routes ? stop.routes.length : 0} lines</div>
          </div>
        `);
        marker.addTo(stopsGroup);

        if (layerVisibility.walkshed) {
          L.circle([stop.lat, stop.lon], {
            radius: 500,
            color: '#0ea5e9',
            fillColor: '#0ea5e9',
            fillOpacity: 0.07,
            weight: 1,
            dashArray: '4 4',
          }).addTo(walkshedGroup);
        }
      });
    }
  }, [stops, layerVisibility.stops, layerVisibility.walkshed]);

  // 6. Render Planned Route
  useEffect(() => {
    const group = routeLayerGroupRef.current;
    const map = mapInstanceRef.current;
    if (!group) return;
    group.clearLayers();

    if (route && route.geojson) {
      const routeLayer = L.geoJSON(route.geojson, {
        style: {
          color: '#00f0ff',
          weight: 6,
          opacity: 0.95,
          dashArray: '8 4',
        },
      }).addTo(group);

      if (map && routeLayer.getBounds().isValid()) {
        map.fitBounds(routeLayer.getBounds(), { padding: [40, 40] });
      }
    }
  }, [route]);

  // 7. Render Click-to-Route Markers
  useEffect(() => {
    const group = clickMarkersGroupRef.current;
    if (!group) return;
    group.clearLayers();

    if (clickPoints.start) {
      const originHtml = `
        <div style="transform: translate(-50%, -100%); display: flex; flex-direction: column; align-items: center; pointer-events: auto; cursor: pointer;">
          <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: #ffffff; padding: 4px 10px; border-radius: 20px; font-weight: 800; font-size: 11px; letter-spacing: 0.05em; display: flex; align-items: center; gap: 5px; box-shadow: 0 4px 14px rgba(16, 185, 129, 0.65); border: 2px solid #ffffff; white-space: nowrap;">
            🟢 ORIGIN
          </div>
          <div style="width: 0; height: 0; border-left: 6px solid transparent; border-right: 6px solid transparent; border-top: 8px solid #059669; margin-top: -1px;"></div>
        </div>`;
      const originIcon = L.divIcon({ className: 'origin-pin-icon', html: originHtml, iconSize: [0, 0] });
      L.marker(clickPoints.start, { icon: originIcon, zIndexOffset: 2000 })
        .bindPopup(`<b>🟢 Journey Origin</b><br/>GPS: ${clickPoints.start[0].toFixed(4)}, ${clickPoints.start[1].toFixed(4)}`)
        .addTo(group);
      L.circleMarker(clickPoints.start, { radius: 7, fillColor: '#10b981', color: '#ffffff', weight: 2.5, fillOpacity: 1 }).addTo(group);
    }

    if (clickPoints.end) {
      const destHtml = `
        <div style="transform: translate(-50%, -100%); display: flex; flex-direction: column; align-items: center; pointer-events: auto; cursor: pointer;">
          <div style="background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); color: #ffffff; padding: 4px 10px; border-radius: 20px; font-weight: 800; font-size: 11px; letter-spacing: 0.05em; display: flex; align-items: center; gap: 5px; box-shadow: 0 4px 14px rgba(239, 68, 68, 0.65); border: 2px solid #ffffff; white-space: nowrap;">
            🔴 DESTINATION
          </div>
          <div style="width: 0; height: 0; border-left: 6px solid transparent; border-right: 6px solid transparent; border-top: 8px solid #dc2626; margin-top: -1px;"></div>
        </div>`;
      const destIcon = L.divIcon({ className: 'dest-pin-icon', html: destHtml, iconSize: [0, 0] });
      L.marker(clickPoints.end, { icon: destIcon, zIndexOffset: 2000 })
        .bindPopup(`<b>🔴 Journey Destination</b><br/>GPS: ${clickPoints.end[0].toFixed(4)}, ${clickPoints.end[1].toFixed(4)}`)
        .addTo(group);
      L.circleMarker(clickPoints.end, { radius: 7, fillColor: '#ef4444', color: '#ffffff', weight: 2.5, fillOpacity: 1 }).addTo(group);
    }
  }, [clickPoints]);

  return (
    <div style={{ position: 'relative', width: '100%', height: '620px', borderRadius: '14px', overflow: 'hidden' }}>
      <div ref={mapContainerRef} style={{ width: '100%', height: '100%' }} />

      {/* Floating Glassmorphic Legend */}
      <div style={{
        position: 'absolute',
        bottom: '24px',
        right: '24px',
        width: '180px',
        background: 'rgba(15, 23, 42, 0.92)',
        border: '1px solid rgba(255, 107, 53, 0.45)',
        borderRadius: '12px',
        padding: '12px 14px',
        backdropFilter: 'blur(12px)',
        boxShadow: '0 8px 32px rgba(0,0,0,0.6)',
        zIndex: 1000,
        fontSize: '11px',
        lineHeight: 1.5,
      }}>
        <b style={{ color: '#ff9933', fontSize: '11.5px', display: 'block', marginBottom: '6px', letterSpacing: '0.04em' }}>
          🚦 TRAFFIC VELOCITY
        </b>
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: '3px' }}>
          <span style={{ display: 'inline-block', width: '14px', height: '4px', background: '#2ecc71', marginRight: '8px', borderRadius: '2px' }} />
          <span>Free Flow (&gt;28 km/h)</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: '3px' }}>
          <span style={{ display: 'inline-block', width: '14px', height: '4px', background: '#f1c40f', marginRight: '8px', borderRadius: '2px' }} />
          <span>Moderate (18-28)</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: '3px' }}>
          <span style={{ display: 'inline-block', width: '14px', height: '4px', background: '#e67e22', marginRight: '8px', borderRadius: '2px' }} />
          <span>Heavy (10-18)</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: '6px' }}>
          <span style={{ display: 'inline-block', width: '14px', height: '4px', background: '#e74c3c', marginRight: '8px', borderRadius: '2px' }} />
          <span>Gridlock (&lt;10 km/h)</span>
        </div>
        <hr style={{ border: 'none', borderTop: '1px solid rgba(255,255,255,0.12)', margin: '4px 0 6px 0' }} />
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <span style={{ display: 'inline-block', width: '14px', height: '4px', background: '#00f0ff', marginRight: '8px', borderRadius: '2px' }} />
          <span>Optimal Route</span>
        </div>
      </div>
    </div>
  );
}

