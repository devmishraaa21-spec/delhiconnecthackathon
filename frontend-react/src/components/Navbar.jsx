import React, { useState } from 'react';
import { RefreshCw, Activity, ShieldCheck, Bus } from 'lucide-react';

export default function Navbar({ status, onRefresh }) {
  const [refreshing, setRefreshing] = useState(false);

  const handleRefreshClick = async () => {
    setRefreshing(true);
    await onRefresh();
    setTimeout(() => setRefreshing(false), 1200);
  };

  return (
    <header style={{ marginBottom: '20px' }}>
      <div className="top-tricolor-bar" />
      <div className="glass-panel" style={{ padding: '20px 28px', marginTop: '12px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ fontSize: '1.8rem' }}>🚌</span>
              <h1 style={{
                fontSize: '1.75rem',
                fontWeight: 800,
                letterSpacing: '-0.02em',
                background: 'linear-gradient(90deg, #FF9933, #FF6B35, #FFA07A)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                margin: 0
              }}>
                Delhi Bus Traffic Model & Journey Planner
              </h1>
            </div>
            <p style={{ color: '#94a3b8', fontSize: '0.9rem', marginTop: '4px' }}>
              FastAPI + React 60 FPS Engine • Real-time GPS displacement velocity modeling & Dynamic A* Routing
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '6px 14px',
              borderRadius: '20px',
              background: status.is_live ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)',
              border: `1px solid ${status.is_live ? 'rgba(16, 185, 129, 0.4)' : 'rgba(245, 158, 11, 0.4)'}`,
              fontSize: '0.82rem',
              fontWeight: 700,
              color: status.is_live ? '#34d399' : '#fbbf24'
            }}>
              <span className={status.is_live ? "pulse-dot-green" : ""} style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                backgroundColor: status.is_live ? '#10b981' : '#f59e0b',
                display: 'inline-block'
              }} />
              {status.is_live ? "DELHI OTD LIVE STREAMING" : "SYNTHETIC SIMULATION BASELINE"}
            </div>

            <button
              onClick={handleRefreshClick}
              disabled={refreshing}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                background: 'linear-gradient(135deg, #FF6B35 0%, #e85d04 100%)',
                color: '#fff',
                border: 'none',
                padding: '8px 16px',
                borderRadius: '10px',
                fontWeight: 600,
                fontSize: '0.85rem',
                cursor: refreshing ? 'not-allowed' : 'pointer',
                boxShadow: '0 4px 14px rgba(255, 107, 53, 0.35)',
                transition: 'all 0.2s ease',
              }}
            >
              <RefreshCw size={15} style={{ animation: refreshing ? 'spin 1s linear infinite' : 'none' }} />
              {refreshing ? 'Syncing...' : 'Sync Live OTD'}
            </button>
          </div>
        </div>

        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginTop: '14px',
          paddingTop: '12px',
          borderTop: '1px solid rgba(255, 255, 255, 0.08)',
          fontSize: '0.85rem',
          color: '#94a3b8',
          flexWrap: 'wrap',
          gap: '8px'
        }}>
          <div>
            ⚡ Connected Fleet: <strong style={{ color: '#f1f5f9' }}>{status.total_active_fleet?.toLocaleString() || '0'} buses</strong> across Delhi NCR
          </div>
          <div>
            ⏱️ Last Telemetry Sync: <strong style={{ color: '#38bdf8' }}>{status.last_sync_time || 'Just now'}</strong> (Auto-polled every 20s)
          </div>
        </div>
      </div>
      <style>{`
        @keyframes spin { 100% { transform: rotate(360deg); } }
      `}</style>
    </header>
  );
}

