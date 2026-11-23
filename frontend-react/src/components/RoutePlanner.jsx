import React from 'react';
import { MapPin, Navigation, Compass, Layers, RotateCcw } from 'lucide-react';

export default function RoutePlanner({
  stops,
  selectedSrc,
  selectedDst,
  onSelectSrc,
  onSelectDst,
  onPlanRoute,
  onResetRoute,
  corridorFocus,
  onCorridorChange,
  layerVisibility,
  onToggleLayer,
  clickPoints,
}) {
  const presets = [
    { name: '🏢 Rohini ➔ CP', src: 'Rohini Sec-3', dst: 'Connaught Place' },
    { name: '🏥 KG ➔ AIIMS', src: 'ISBT Kashmere Gate', dst: 'AIIMS' },
    { name: '✈️ Dwarka ➔ CP', src: 'Dwarka Sec-21', dst: 'Connaught Place' },
    { name: '🏛️ Janakpuri ➔ ITO', src: 'Janakpuri', dst: 'ITO' },
  ];

  return (
    <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* 1. Quick Presets */}
      <div>
        <h3 style={{ fontSize: '0.9rem', fontWeight: 700, color: '#ff9933', marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Compass size={16} /> POPULAR COMMUTER CORRIDORS
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
          {presets.map((p, idx) => (
            <button
              key={idx}
              onClick={() => {
                onSelectSrc(p.src);
                onSelectDst(p.dst);
                const sObj = stops.find((s) => s.name === p.src);
                const dObj = stops.find((s) => s.name === p.dst);
                if (sObj && dObj) {
                  onPlanRoute(sObj.lat, sObj.lon, dObj.lat, dObj.lon);
                }
              }}
              style={{
                background: 'rgba(30, 41, 59, 0.7)',
                border: '1px solid rgba(255, 107, 53, 0.25)',
                color: '#f1f5f9',
                padding: '8px 10px',
                borderRadius: '8px',
                fontSize: '0.78rem',
                fontWeight: 600,
                cursor: 'pointer',
                textAlign: 'left',
                transition: 'all 0.2s',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.borderColor = '#ff6b35')}
              onMouseLeave={(e) => (e.currentTarget.style.borderColor = 'rgba(255, 107, 53, 0.25)')}
            >
              {p.name}
            </button>
          ))}
        </div>
      </div>

      <hr style={{ border: 'none', borderTop: '1px solid rgba(255,255,255,0.08)' }} />

      {/* 2. Source & Destination Selectors */}
      <div>
        <h3 style={{ fontSize: '0.9rem', fontWeight: 700, color: '#ff9933', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Navigation size={16} /> PLAN CUSTOM JOURNEY
        </h3>

        <div style={{ marginBottom: '10px' }}>
          <label style={{ fontSize: '0.75rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>
            🟢 Origin Stop
          </label>
          <select
            value={selectedSrc}
            onChange={(e) => onSelectSrc(e.target.value)}
            style={{
              width: '100%',
              background: '#0f172a',
              color: '#f1f5f9',
              border: '1px solid rgba(255, 107, 53, 0.3)',
              borderRadius: '8px',
              padding: '8px 12px',
              fontSize: '0.85rem',
            }}
          >
            {stops.map((s) => (
              <option key={s.stop_id} value={s.name}>
                {s.name}
              </option>
            ))}
          </select>
        </div>

        <div style={{ marginBottom: '14px' }}>
          <label style={{ fontSize: '0.75rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>
            🔴 Destination Stop
          </label>
          <select
            value={selectedDst}
            onChange={(e) => onSelectDst(e.target.value)}
            style={{
              width: '100%',
              background: '#0f172a',
              color: '#f1f5f9',
              border: '1px solid rgba(255, 107, 53, 0.3)',
              borderRadius: '8px',
              padding: '8px 12px',
              fontSize: '0.85rem',
            }}
          >
            {stops.map((s) => (
              <option key={s.stop_id} value={s.name}>
                {s.name}
              </option>
            ))}
          </select>
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            onClick={() => {
              const sObj = stops.find((s) => s.name === selectedSrc);
              const dObj = stops.find((s) => s.name === selectedDst);
              if (sObj && dObj) {
                onPlanRoute(sObj.lat, sObj.lon, dObj.lat, dObj.lon);
              }
            }}
            style={{
              flex: 1,
              background: 'linear-gradient(135deg, #FF6B35 0%, #e85d04 100%)',
              color: '#ffffff',
              border: 'none',
              padding: '10px 14px',
              borderRadius: '8px',
              fontWeight: 700,
              fontSize: '0.85rem',
              cursor: 'pointer',
              boxShadow: '0 4px 14px rgba(255, 107, 53, 0.35)',
            }}
          >
            Compute Route & Live ETA
          </button>

          <button
            onClick={onResetRoute}
            title="Reset Route"
            style={{
              background: '#1e293b',
              color: '#cbd5e1',
              border: '1px solid rgba(255,255,255,0.1)',
              padding: '10px 12px',
              borderRadius: '8px',
              cursor: 'pointer',
            }}
          >
            <RotateCcw size={16} />
          </button>
        </div>

        {/* Click-to-route helper */}
        <div style={{ marginTop: '10px', fontSize: '0.75rem', color: '#64748b', lineHeight: 1.4 }}>
          💡 <em>Or click anywhere on the 2D map to set Origin & Destination directly.</em>
          {clickPoints.start && (
            <div style={{ color: '#10b981', marginTop: '4px' }}>
              ✓ Origin set: {clickPoints.start[0].toFixed(4)}, {clickPoints.start[1].toFixed(4)}
            </div>
          )}
          {clickPoints.end && (
            <div style={{ color: '#ef4444', marginTop: '2px' }}>
              ✓ Dest set: {clickPoints.end[0].toFixed(4)}, {clickPoints.end[1].toFixed(4)}
            </div>
          )}
        </div>
      </div>

      <hr style={{ border: 'none', borderTop: '1px solid rgba(255,255,255,0.08)' }} />

      {/* 3. Corridor Focal Quick-Jump */}
      <div>
        <h3 style={{ fontSize: '0.9rem', fontWeight: 700, color: '#ff9933', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <MapPin size={16} /> FOCUS DELHI REGION
        </h3>
        <select
          value={corridorFocus}
          onChange={(e) => onCorridorChange(e.target.value)}
          style={{
            width: '100%',
            background: '#0f172a',
            color: '#f1f5f9',
            border: '1px solid rgba(255, 107, 53, 0.3)',
            borderRadius: '8px',
            padding: '8px 12px',
            fontSize: '0.85rem',
          }}
        >
          <option value="all">🗺️ All Delhi (Metropolitan Overview)</option>
          <option value="central">🏛️ Central Delhi (CP / India Gate)</option>
          <option value="north">🏰 North Delhi (ISBT / Red Fort)</option>
          <option value="south">🏥 South Delhi (AIIMS / Ring Road)</option>
          <option value="east">🌉 East Delhi (Vikas Marg / Anand Vihar)</option>
          <option value="west">✈️ West Delhi (Dwarka / Janakpuri)</option>
        </select>
      </div>

      <hr style={{ border: 'none', borderTop: '1px solid rgba(255,255,255,0.08)' }} />

      {/* 4. Layer Visibility Toggles */}
      <div>
        <h3 style={{ fontSize: '0.9rem', fontWeight: 700, color: '#ff9933', marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Layers size={16} /> MAP LAYERS
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '0.8rem' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={layerVisibility.segments}
              onChange={() => onToggleLayer('segments')}
              style={{ accentColor: '#ff6b35' }}
            />
            Road Speeds
          </label>
          <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={layerVisibility.fleet}
              onChange={() => onToggleLayer('fleet')}
              style={{ accentColor: '#ff6b35' }}
            />
            Live Bus Fleet
          </label>
          <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={layerVisibility.stops}
              onChange={() => onToggleLayer('stops')}
              style={{ accentColor: '#ff6b35' }}
            />
            Bus Stops
          </label>
          <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={layerVisibility.walkshed}
              onChange={() => onToggleLayer('walkshed')}
              style={{ accentColor: '#ff6b35' }}
            />
            500m Walksheds
          </label>
        </div>
      </div>
    </div>
  );
}

