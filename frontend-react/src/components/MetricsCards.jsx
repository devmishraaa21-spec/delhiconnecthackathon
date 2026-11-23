import React from 'react';
import { Bus, Gauge, Navigation, Clock, Activity, Zap } from 'lucide-react';

export default function MetricsCards({ status, route }) {
  const kpis = [
    {
      label: 'TOTAL ACTIVE FLEET',
      value: status.total_active_fleet?.toLocaleString() || '0',
      icon: Bus,
      color: '#ff9933',
      sub: 'Ingested live vehicle units',
    },
    {
      label: 'VEHICLES IN MOTION',
      value: status.moving_buses?.toLocaleString() || '0',
      icon: Navigation,
      color: '#10b981',
      sub: 'Active velocity ≥ 5 km/h',
    },
    {
      label: 'IDLE / DWELL / SIGNALS',
      value: status.idle_buses?.toLocaleString() || '0',
      icon: Clock,
      color: '#f59e0b',
      sub: 'At terminals & intersections',
    },
    {
      label: 'FLEET AVERAGE SPEED',
      value: `${status.fleet_avg_speed_kmh || 0} km/h`,
      icon: Gauge,
      color: '#38bdf8',
      sub: 'Instantaneous GPS displacement',
    },
  ];

  return (
    <div style={{ marginBottom: '20px' }}>
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))',
        gap: '14px',
      }}>
        {kpis.map((kpi, idx) => {
          const Icon = kpi.icon;
          return (
            <div key={idx} className="glass-panel" style={{
              padding: '16px 20px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              transition: 'transform 0.2s ease, border-color 0.2s ease',
            }}>
              <div>
                <span style={{
                  fontSize: '0.72rem',
                  fontWeight: 700,
                  color: '#94a3b8',
                  letterSpacing: '0.05em',
                  textTransform: 'uppercase'
                }}>
                  {kpi.label}
                </span>
                <div style={{
                  fontSize: '1.75rem',
                  fontWeight: 800,
                  color: '#ffffff',
                  fontFamily: "'JetBrains Mono', monospace",
                  marginTop: '4px'
                }}>
                  {kpi.value}
                </div>
                <span style={{ fontSize: '0.75rem', color: '#64748b' }}>
                  {kpi.sub}
                </span>
              </div>
              <div style={{
                background: `rgba(${parseInt(kpi.color.slice(1,3),16)}, ${parseInt(kpi.color.slice(3,5),16)}, ${parseInt(kpi.color.slice(5,7),16)}, 0.12)`,
                border: `1px solid ${kpi.color}40`,
                borderRadius: '12px',
                padding: '10px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}>
                <Icon size={24} color={kpi.color} />
              </div>
            </div>
          );
        })}
      </div>

      {route && (
        <div className="glass-panel glass-panel-glow" style={{
          marginTop: '14px',
          padding: '14px 22px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '12px',
          background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.85) 100%)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Zap size={20} color="#00f0ff" />
            <div>
              <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#38bdf8', textTransform: 'uppercase' }}>
                OPTIMIZED COMMUTE ROUTE CALCULATED
              </span>
              <div style={{ fontSize: '0.92rem', color: '#f1f5f9', fontWeight: 600 }}>
                Traversing {route.segments_count} Delhi priority transit corridors
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '24px', flexWrap: 'wrap' }}>
            <div>
              <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>DISTANCE</span>
              <div style={{ fontSize: '1.2rem', fontWeight: 700, color: '#f1f5f9' }}>{route.distance_km} km</div>
            </div>
            <div>
              <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>DYNAMIC ETA</span>
              <div style={{ fontSize: '1.2rem', fontWeight: 700, color: '#10b981' }}>{route.eta_minutes} mins</div>
            </div>
            <div>
              <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>EFFECTIVE SPEED</span>
              <div style={{ fontSize: '1.2rem', fontWeight: 700, color: '#ff9933' }}>{route.effective_speed_kmh} km/h</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

