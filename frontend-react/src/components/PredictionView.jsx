import React from 'react';
import { TrendingUp, TrendingDown, Minus, AlertTriangle } from 'lucide-react';

export default function PredictionView({ predictions }) {
  if (!predictions || predictions.length === 0) return null;

  const bottlenecks = predictions.filter((p) => p.forecast_30m_kmh < 15);

  return (
    <div className="glass-panel" style={{ padding: '20px', marginTop: '20px' }}>
      <div style={{ marginBottom: '16px' }}>
        <h2 style={{ fontSize: '1.2rem', fontWeight: 700, color: '#f1f5f9', display: 'flex', alignItems: 'center', gap: '8px' }}>
          🔮 Machine Learning Traffic Forecasting
        </h2>
        <p style={{ fontSize: '0.82rem', color: '#94a3b8', marginTop: '2px' }}>
          Gradient Boosting Regressor forecasting Delhi arterial speeds 30 & 60 minutes into the future
        </p>
      </div>

      {bottlenecks.length > 0 && (
        <div style={{
          background: 'rgba(239, 68, 68, 0.12)',
          border: '1px solid rgba(239, 68, 68, 0.35)',
          borderRadius: '10px',
          padding: '12px 16px',
          marginBottom: '16px',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          fontSize: '0.85rem',
          color: '#f87171'
        }}>
          <AlertTriangle size={18} />
          <span>
            <strong>Anticipated Bottlenecks (+30m):</strong>{' '}
            {bottlenecks.slice(0, 3).map((b) => `${b.road_name} (${b.forecast_30m_kmh} km/h)`).join(', ')}
            {bottlenecks.length > 3 ? ` and ${bottlenecks.length - 3} more` : ''}. Dynamic A* router proactively routes buses around these segments.
          </span>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '12px' }}>
        {predictions.slice(0, 12).map((pred, idx) => {
          let TrendIcon = Minus;
          let trendColor = '#94a3b8';
          if (pred.trend === 'Speeding Up') {
            TrendIcon = TrendingUp;
            trendColor = '#10b981';
          } else if (pred.trend === 'Slowing Down') {
            TrendIcon = TrendingDown;
            trendColor = '#ef4444';
          }

          return (
            <div
              key={idx}
              style={{
                background: 'rgba(30, 41, 59, 0.5)',
                border: '1px solid rgba(255, 255, 255, 0.08)',
                borderRadius: '10px',
                padding: '12px 14px',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                <strong style={{ fontSize: '0.85rem', color: '#f1f5f9' }}>{pred.road_name}</strong>
                <span style={{ fontSize: '0.7rem', color: '#ff9933', background: 'rgba(255, 107, 53, 0.15)', padding: '2px 6px', borderRadius: '4px' }}>
                  {pred.road_type}
                </span>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.78rem' }}>
                <div>
                  <span style={{ color: '#94a3b8' }}>Now: </span>
                  <strong>{pred.current_speed_kmh} km/h</strong>
                </div>
                <div>
                  <span style={{ color: '#38bdf8' }}>+30m: </span>
                  <strong>{pred.forecast_30m_kmh} km/h</strong>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: trendColor }}>
                  <TrendIcon size={14} />
                  <span style={{ fontWeight: 600 }}>{pred.trend}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

