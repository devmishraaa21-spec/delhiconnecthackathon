import React, { useState, useMemo } from 'react';
import { Search, Download, Filter } from 'lucide-react';

export default function BusTable({ fleet }) {
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [page, setPage] = useState(0);
  const rowsPerPage = 50;

  const filteredFleet = useMemo(() => {
    if (!fleet) return [];
    return fleet.filter((bus) => {
      const matchSearch =
        search === '' ||
        bus.bus_id.toLowerCase().includes(search.toLowerCase()) ||
        bus.route_id.toLowerCase().includes(search.toLowerCase());

      const matchStatus =
        statusFilter === 'ALL' ||
        (statusFilter === 'FREE' && bus.status === 'Free Flow') ||
        (statusFilter === 'MOD' && bus.status === 'Moderate') ||
        (statusFilter === 'SLOW' && bus.status.includes('Slow'));

      return matchSearch && matchStatus;
    });
  }, [fleet, search, statusFilter]);

  const totalPages = Math.ceil(filteredFleet.length / rowsPerPage);
  const displayedRows = filteredFleet.slice(page * rowsPerPage, (page + 1) * rowsPerPage);

  const exportCSV = () => {
    const headers = ['Bus ID', 'Route ID', 'Latitude', 'Longitude', 'Speed (km/h)', 'Status'];
    const rows = filteredFleet.map((b) => [b.bus_id, b.route_id, b.lat, b.lon, b.speed, b.status]);
    const csvContent = 'data:text/csv;charset=utf-8,' + [headers, ...rows].map((e) => e.join(',')).join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `delhi_bus_fleet_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="glass-panel" style={{ padding: '20px', marginTop: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px', marginBottom: '16px' }}>
        <div>
          <h2 style={{ fontSize: '1.2rem', fontWeight: 700, color: '#f1f5f9', display: 'flex', alignItems: 'center', gap: '8px' }}>
            🚌 Active Bus Fleet Explorer
          </h2>
          <p style={{ fontSize: '0.82rem', color: '#94a3b8', marginTop: '2px' }}>
            Showing <strong>{filteredFleet.length.toLocaleString()}</strong> of {fleet ? fleet.length.toLocaleString() : 0} live Delhi buses • Instant 0ms client-side filter
          </p>
        </div>

        <button
          onClick={exportCSV}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            background: '#1e293b',
            color: '#f1f5f9',
            border: '1px solid rgba(255, 107, 53, 0.3)',
            padding: '8px 14px',
            borderRadius: '8px',
            fontSize: '0.8rem',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          <Download size={14} /> Export CSV
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', marginBottom: '16px' }}>
        <div style={{ flex: 1, minWidth: '220px', position: 'relative' }}>
          <Search size={16} color="#94a3b8" style={{ position: 'absolute', left: '12px', top: '10px' }} />
          <input
            type="text"
            placeholder="Search Bus ID or Route (e.g. DL1PC, 729, 419, CBD...)"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(0);
            }}
            style={{
              width: '100%',
              background: '#0f172a',
              border: '1px solid rgba(255, 107, 53, 0.25)',
              borderRadius: '8px',
              padding: '8px 12px 8px 36px',
              color: '#f1f5f9',
              fontSize: '0.85rem',
            }}
          />
        </div>

        <div style={{ display: 'flex', gap: '6px' }}>
          {[
            { id: 'ALL', label: 'All Buses' },
            { id: 'FREE', label: '🟢 Free Flow (>20)' },
            { id: 'MOD', label: '🟡 Moderate (5-20)' },
            { id: 'SLOW', label: '🔴 Slow / Dwell (<5)' },
          ].map((btn) => (
            <button
              key={btn.id}
              onClick={() => {
                setStatusFilter(btn.id);
                setPage(0);
              }}
              style={{
                background: statusFilter === btn.id ? 'linear-gradient(135deg, #FF6B35 0%, #e85d04 100%)' : '#1e293b',
                color: statusFilter === btn.id ? '#ffffff' : '#cbd5e1',
                border: '1px solid rgba(255,255,255,0.08)',
                padding: '6px 12px',
                borderRadius: '8px',
                fontSize: '0.78rem',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              {btn.label}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div style={{ overflowX: 'auto', maxHeight: '420px', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '8px' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem', textAlign: 'left' }}>
          <thead style={{ background: '#1e293b', position: 'sticky', top: 0, zIndex: 10 }}>
            <tr>
              <th style={{ padding: '10px 14px', color: '#ff9933' }}>Bus ID</th>
              <th style={{ padding: '10px 14px', color: '#ff9933' }}>Route</th>
              <th style={{ padding: '10px 14px', color: '#ff9933' }}>Latitude</th>
              <th style={{ padding: '10px 14px', color: '#ff9933' }}>Longitude</th>
              <th style={{ padding: '10px 14px', color: '#ff9933', minWidth: '160px' }}>Velocity</th>
              <th style={{ padding: '10px 14px', color: '#ff9933' }}>Operational Status</th>
            </tr>
          </thead>
          <tbody>
            {displayedRows.length === 0 ? (
              <tr>
                <td colSpan={6} style={{ textAlign: 'center', padding: '24px', color: '#94a3b8' }}>
                  No vehicles matching search criteria.
                </td>
              </tr>
            ) : (
              displayedRows.map((bus, idx) => {
                const spd = bus.speed || 0;
                let barColor = '#ef4444';
                if (spd >= 20) barColor = '#10b981';
                else if (spd >= 5) barColor = '#f59e0b';

                return (
                  <tr
                    key={bus.bus_id + idx}
                    style={{
                      borderBottom: '1px solid rgba(255,255,255,0.05)',
                      background: idx % 2 === 0 ? 'rgba(15, 23, 42, 0.4)' : 'transparent',
                    }}
                  >
                    <td style={{ padding: '10px 14px', fontWeight: 700, fontFamily: "'JetBrains Mono', monospace" }}>
                      {bus.bus_id}
                    </td>
                    <td style={{ padding: '10px 14px', color: '#38bdf8' }}>{bus.route_id}</td>
                    <td style={{ padding: '10px 14px', color: '#94a3b8' }}>{bus.lat.toFixed(4)}</td>
                    <td style={{ padding: '10px 14px', color: '#94a3b8' }}>{bus.lon.toFixed(4)}</td>
                    <td style={{ padding: '10px 14px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{ minWidth: '55px', fontWeight: 600, color: barColor }}>
                          {spd.toFixed(1)} km/h
                        </span>
                        <div style={{ flex: 1, height: '6px', background: '#334155', borderRadius: '3px', overflow: 'hidden' }}>
                          <div style={{ width: `${Math.min(100, (spd / 60) * 100)}%`, height: '100%', background: barColor }} />
                        </div>
                      </div>
                    </td>
                    <td style={{ padding: '10px 14px' }}>
                      <span
                        style={{
                          padding: '3px 8px',
                          borderRadius: '12px',
                          fontSize: '0.75rem',
                          fontWeight: 600,
                          background: `${barColor}20`,
                          color: barColor,
                          border: `1px solid ${barColor}40`,
                        }}
                      >
                        {bus.status}
                      </span>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '12px', fontSize: '0.8rem', color: '#94a3b8' }}>
          <div>
            Page <strong>{page + 1}</strong> of {totalPages}
          </div>
          <div style={{ display: 'flex', gap: '6px' }}>
            <button
              disabled={page === 0}
              onClick={() => setPage((p) => p - 1)}
              style={{
                background: '#1e293b',
                color: page === 0 ? '#475569' : '#f1f5f9',
                border: 'none',
                padding: '6px 12px',
                borderRadius: '6px',
                cursor: page === 0 ? 'not-allowed' : 'pointer',
              }}
            >
              Previous
            </button>
            <button
              disabled={page >= totalPages - 1}
              onClick={() => setPage((p) => p + 1)}
              style={{
                background: '#1e293b',
                color: page >= totalPages - 1 ? '#475569' : '#f1f5f9',
                border: 'none',
                padding: '6px 12px',
                borderRadius: '6px',
                cursor: page >= totalPages - 1 ? 'not-allowed' : 'pointer',
              }}
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

