import React, { useState, useEffect, useCallback } from 'react';
import Navbar from './components/Navbar';
import MetricsCards from './components/MetricsCards';
import MapComponent from './components/MapComponent';
import RoutePlanner from './components/RoutePlanner';
import BusTable from './components/BusTable';
import PredictionView from './components/PredictionView';
import { Map, Bus, BrainCircuit } from 'lucide-react';

export default function App() {
  const [status, setStatus] = useState({});
  const [fleet, setFleet] = useState([]);
  const [segments, setSegments] = useState([]);
  const [stops, setStops] = useState([]);
  const [predictions, setPredictions] = useState([]);
  const [activeTab, setActiveTab] = useState('map');

  // Journey planning state
  const [selectedSrc, setSelectedSrc] = useState('Connaught Place');
  const [selectedDst, setSelectedDst] = useState('AIIMS');
  const [route, setRoute] = useState(null);
  const [clickPoints, setClickPoints] = useState({ start: null, end: null });

  // Map controls
  const [corridorFocus, setCorridorFocus] = useState('all');
  const [layerVisibility, setLayerVisibility] = useState({
    segments: true,
    fleet: true,
    stops: true,
    walkshed: false,
  });

  const toggleLayer = (layerKey) => {
    setLayerVisibility((prev) => ({ ...prev, [layerKey]: !prev[layerKey] }));
  };

  // Fetch initial base data (segments, stops, predictions)
  const fetchBaseData = async () => {
    try {
      const [segRes, stopRes, predRes] = await Promise.all([
        fetch('/api/segments'),
        fetch('/api/stops'),
        fetch('/api/predictions'),
      ]);
      if (segRes.ok) setSegments(await segRes.json());
      if (stopRes.ok) setStops(await stopRes.json());
      if (predRes.ok) setPredictions(await predRes.json());
    } catch (err) {
      console.error('Failed to load base geographic data:', err);
    }
  };

  // Poll dynamic telemetry (fleet & status) silently
  const fetchLiveTelemetry = async () => {
    try {
      const [statusRes, fleetRes] = await Promise.all([
        fetch('/api/status'),
        fetch('/api/fleet?limit=550'),
      ]);
      if (statusRes.ok) setStatus(await statusRes.json());
      if (fleetRes.ok) setFleet(await fleetRes.json());
    } catch (err) {
      console.error('Failed to poll telemetry:', err);
    }
  };

  // Initial mount
  useEffect(() => {
    fetchBaseData();
    fetchLiveTelemetry();

    // Auto-poll live fleet telemetry every 18 seconds silently in background
    const timer = setInterval(() => {
      fetchLiveTelemetry();
    }, 18000);

    return () => clearInterval(timer);
  }, []);

  // Plan Route API
  const handlePlanRoute = async (sLat, sLon, eLat, eLon) => {
    setClickPoints({ start: [sLat, sLon], end: [eLat, eLon] });
    try {
      const res = await fetch('/api/route', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          start_lat: sLat,
          start_lon: sLon,
          end_lat: eLat,
          end_lon: eLon,
        }),
      });
      if (res.ok) {
        const routeData = await res.json();
        setRoute(routeData);
      }
    } catch (err) {
      console.error('Routing failed:', err);
    }
  };

  // Map Click handler (Click-to-Route with non-stale functional state)
  const handleMapClick = (lat, lon) => {
    setClickPoints((prev) => {
      if (!prev.start || (prev.start && prev.end)) {
        setRoute(null);
        return { start: [lat, lon], end: null };
      } else {
        handlePlanRoute(prev.start[0], prev.start[1], lat, lon);
        return { start: prev.start, end: [lat, lon] };
      }
    });
  };

  const handleResetRoute = () => {
    setRoute(null);
    setClickPoints({ start: null, end: null });
  };

  const handleManualSync = async () => {
    try {
      await fetch('/api/refresh', { method: 'POST' });
      await fetchLiveTelemetry();
    } catch (err) {
      console.error('Manual refresh failed:', err);
    }
  };

  return (
    <div style={{ maxWidth: '1440px', margin: '0 auto', padding: '0 20px 40px 20px' }}>
      <Navbar status={status} onRefresh={handleManualSync} />
      <MetricsCards status={status} route={route} />

      {/* Main Tab Navigation */}
      <div style={{ display: 'flex', gap: '10px', marginBottom: '18px' }}>
        {[
          { id: 'map', label: '🗺️ Map', icon: Map },
          { id: 'fleet', label: '🚌 Active Bus Fleet Explorer', icon: Bus },
          { id: 'ml', label: '🔮 Machine Learning Predictions', icon: BrainCircuit },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                background: isActive ? 'linear-gradient(135deg, rgba(255, 107, 53, 0.25), rgba(255, 153, 51, 0.15))' : 'rgba(15, 23, 42, 0.6)',
                color: isActive ? '#ff9933' : '#94a3b8',
                border: `1px solid ${isActive ? 'rgba(255, 107, 53, 0.5)' : 'rgba(255, 255, 255, 0.08)'}`,
                padding: '10px 18px',
                borderRadius: '10px',
                fontWeight: 600,
                fontSize: '0.88rem',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
              }}
            >
              <Icon size={16} />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Tab 1: Map & Journey Planner */}
      {activeTab === 'map' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: '20px', alignItems: 'start' }}>
          <MapComponent
            fleet={fleet}
            segments={segments}
            stops={stops}
            route={route}
            corridorFocus={corridorFocus}
            layerVisibility={layerVisibility}
            onMapClick={handleMapClick}
            clickPoints={clickPoints}
          />
          <RoutePlanner
            stops={stops}
            selectedSrc={selectedSrc}
            selectedDst={selectedDst}
            onSelectSrc={setSelectedSrc}
            onSelectDst={setSelectedDst}
            onPlanRoute={handlePlanRoute}
            onResetRoute={handleResetRoute}
            corridorFocus={corridorFocus}
            onCorridorChange={setCorridorFocus}
            layerVisibility={layerVisibility}
            onToggleLayer={toggleLayer}
            clickPoints={clickPoints}
          />
        </div>
      )}

      {/* Tab 2: Bus Fleet Explorer Table */}
      {activeTab === 'fleet' && <BusTable fleet={fleet} />}

      {/* Tab 3: Machine Learning Predictions */}
      {activeTab === 'ml' && <PredictionView predictions={predictions} />}
    </div>
  );
}

