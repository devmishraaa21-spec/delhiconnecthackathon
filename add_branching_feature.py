import os

path = r"C:\Users\iamde\.gemini\antigravity\scratch\delhi-bus-planner\static\index.html"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

# 1. Add branch state variables in App
old_state_marker = "const [alerts, setAlerts] = useState({ bottlenecks: [], bunching: [], timestamp: '' });"
new_state_marker = """const [alerts, setAlerts] = useState({ bottlenecks: [], bunching: [], timestamp: '' });
      const [branchOrigin, setBranchOrigin] = useState('Connaught Place');
      const [branchDest, setBranchDest] = useState('AIIMS');
      const [branchData, setBranchData] = useState(null);
      const [branchLoading, setBranchLoading] = useState(false);

      const fetchBranches = async (o = branchOrigin, d = branchDest) => {
        setBranchLoading(true);
        try {
          const res = await fetch(`/api/corridor-branches?origin=${encodeURIComponent(o)}&destination=${encodeURIComponent(d)}`);
          if (res.ok) {
            setBranchData(await res.json());
          }
        } catch (err) {
          console.error('Failed to load corridor branches:', err);
        } finally {
          setBranchLoading(false);
        }
      };"""

if old_state_marker in text and "const [branchData, setBranchData]" not in text:
    text = text.replace(old_state_marker, new_state_marker, 1)
    print("Added branch state variables successfully.")

# 2. Add branch fetch trigger in useEffect
old_effect_marker = "const timer = setInterval(fetchLiveTelemetry, 18000);"
new_effect_marker = """const timer = setInterval(() => {
          fetchLiveTelemetry();
          fetchBranches(branchOrigin, branchDest);
        }, 18000);
        fetchBranches(branchOrigin, branchDest);"""

if old_effect_marker in text:
    text = text.replace(old_effect_marker, new_effect_marker, 1)
    print("Added branch periodic fetch successfully.")

# 3. Add 5th navigation tab: Multi-Route Corridor & Bus Branching
old_tabs_block = """            {[
              { id: 'map', label: '🗺️ Map' },
              { id: 'fleet', label: '🚌 Active Bus Fleet Explorer' },
              { id: 'ml', label: '🔮 ML Traffic Forecasting' },
              { id: 'alerts', label: `🚨 Transit Alerts & Bunching (${(alerts.bottlenecks?.length || 0) + (alerts.bunching?.length || 0)})` },"""

new_tabs_block = """            {[
              { id: 'map', label: '🗺️ Map' },
              { id: 'fleet', label: '🚌 Active Bus Fleet Explorer' },
              { id: 'ml', label: '🔮 ML Traffic Forecasting' },
              { id: 'alerts', label: `🚨 Transit Alerts & Bunching (${(alerts.bottlenecks?.length || 0) + (alerts.bunching?.length || 0)})` },
              { id: 'branching', label: `🔀 Multi-Route Corridor & Bus Branching (${branchData?.total_buses_in_transit || 0} buses)` },"""

if old_tabs_block in text:
    text = text.replace(old_tabs_block, new_tabs_block, 1)
    print("Added Branching navigation tab successfully.")

# 4. Render CorridorBranchingComponent in activeTab === 'branching'
old_tab_render = """          {/* TAB 4: ALERTS & BUNCHING */}
          {activeTab === 'alerts' && <AlertsComponent alerts={alerts} />}
        </div>"""

new_tab_render = """          {/* TAB 4: ALERTS & BUNCHING */}
          {activeTab === 'alerts' && <AlertsComponent alerts={alerts} />}

          {/* TAB 5: MULTI-ROUTE CORRIDOR & BUS BRANCHING BETWEEN 2 POINTS */}
          {activeTab === 'branching' && (
            <CorridorBranchingComponent
              stops={stops}
              origin={branchOrigin}
              destination={branchDest}
              setOrigin={setBranchOrigin}
              setDestination={setBranchDest}
              branchData={branchData}
              loading={branchLoading}
              onRefresh={() => fetchBranches(branchOrigin, branchDest)}
            />
          )}
        </div>"""

if old_tab_render in text:
    text = text.replace(old_tab_render, new_tab_render, 1)
    print("Added Branching tab component render successfully.")

# 5. Define CorridorBranchingComponent and BranchMapContainer
branch_components = """
    // Branch Map Container (Leaflet)
    function BranchMapContainer({ origin, destination, branches, selectedBranchId, onSelectBranch }) {
      const bMapRef = useRef(null);
      const bInstanceRef = useRef(null);
      const bLayerGroup = useRef(null);

      useEffect(() => {
        if (!bMapRef.current || bInstanceRef.current) return;
        const bmap = L.map(bMapRef.current, { center: [28.6139, 77.2090], zoom: 12 });
        bInstanceRef.current = bmap;

        L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
          maxZoom: 19,
          attribution: '&copy; OpenStreetMap contributors',
        }).addTo(bmap);

        bLayerGroup.current = L.layerGroup().addTo(bmap);

        setTimeout(() => { if (bmap) bmap.invalidateSize(); }, 250);

        return () => {
          bmap.remove();
          bInstanceRef.current = null;
          bLayerGroup.current = null;
        };
      }, []);

      // Draw Branches, Origin, Destination & All Buses
      useEffect(() => {
        const bmap = bInstanceRef.current;
        if (!bmap || !bLayerGroup.current || !origin || !destination) return;
        bLayerGroup.current.clearLayers();

        const allBounds = [];

        // 1. Origin Marker
        const oLatLon = [origin.lat, origin.lon];
        allBounds.push(oLatLon);
        const oHtml = `
          <div style="transform: translate(-50%, -100%); display: flex; flex-direction: column; align-items: center;">
            <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: #fff; padding: 4px 10px; border-radius: 20px; font-weight: 800; font-size: 11px; border: 2px solid #fff; box-shadow: 0 4px 14px rgba(16,185,129,0.7); white-space: nowrap;">
              🟢 POINT A: ${origin.name}
            </div>
            <div style="width: 0; height: 0; border-left: 6px solid transparent; border-right: 6px solid transparent; border-top: 8px solid #059669;"></div>
          </div>`;
        L.marker(oLatLon, { icon: L.divIcon({ className: 'b-o-pin', html: oHtml, iconSize: [0, 0] }) }).addTo(bLayerGroup.current);
        L.circleMarker(oLatLon, { radius: 7, fillColor: '#10b981', color: '#fff', weight: 2.5, fillOpacity: 1 }).addTo(bLayerGroup.current);

        // 2. Destination Marker
        const dLatLon = [destination.lat, destination.lon];
        allBounds.push(dLatLon);
        const dHtml = `
          <div style="transform: translate(-50%, -100%); display: flex; flex-direction: column; align-items: center;">
            <div style="background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); color: #fff; padding: 4px 10px; border-radius: 20px; font-weight: 800; font-size: 11px; border: 2px solid #fff; box-shadow: 0 4px 14px rgba(239,68,68,0.7); white-space: nowrap;">
              🔴 POINT B: ${destination.name}
            </div>
            <div style="width: 0; height: 0; border-left: 6px solid transparent; border-right: 6px solid transparent; border-top: 8px solid #dc2626;"></div>
          </div>`;
        L.marker(dLatLon, { icon: L.divIcon({ className: 'b-d-pin', html: dHtml, iconSize: [0, 0] }) }).addTo(bLayerGroup.current);
        L.circleMarker(dLatLon, { radius: 7, fillColor: '#ef4444', color: '#fff', weight: 2.5, fillOpacity: 1 }).addTo(bLayerGroup.current);

        // 3. Draw Branches and their Buses
        (branches || []).forEach(branch => {
          const isSelected = selectedBranchId === 'ALL' || selectedBranchId === branch.branch_id;
          const opacity = isSelected ? 0.95 : 0.25;
          const weight = isSelected ? 6 : 3;

          if (branch.coordinates && branch.coordinates.length > 1) {
            const poly = L.polyline(branch.coordinates, {
              color: branch.color,
              weight: weight,
              opacity: opacity,
              dashArray: branch.branch_id === 'BR_ALPHA' ? null : '6 4',
            }).addTo(bLayerGroup.current);

            poly.bindPopup(`
              <div style="font-family: inherit; padding: 2px;">
                <b style="color: ${branch.color}; font-size: 13px;">${branch.name}</b><br/>
                <span style="font-size: 11px; color: #cbd5e1;">Via: ${branch.via}</span><br/>
                <span style="font-size: 11px; color: #94a3b8;">Active Buses: <b>${branch.total_active_buses}</b> | Speed: <b>${branch.corridor_speed_kmh} km/h</b></span>
              </div>
            `);

            branch.coordinates.forEach(c => allBounds.push(c));
          }

          // Plot active buses for this branch
          if (isSelected) {
            (branch.buses || []).forEach(bus => {
              const bMarker = L.circleMarker([bus.lat, bus.lon], {
                radius: 7,
                fillColor: branch.color,
                color: '#ffffff',
                weight: 2,
                fillOpacity: 0.95,
              });

              bMarker.bindPopup(`
                <div style="font-family: inherit; min-width: 170px; padding: 2px;">
                  <div style="font-weight: 700; color: ${branch.color}; font-size: 13px;">🚌 Bus #${bus.bus_id}</div>
                  <div style="font-size: 11px; color: #94a3b8; margin: 2px 0 6px 0;">Route: <b>${bus.route_id}</b> | Branch: <b>${branch.name.split(':')[0]}</b></div>
                  <div style="background: rgba(15, 23, 42, 0.8); padding: 6px 8px; border-radius: 6px; font-size: 11px; line-height: 1.5;">
                    <div>Velocity: <b style="color: #10b981;">${bus.speed_kmh} km/h</b></div>
                    <div>Progress: <b>${bus.progress_pct}%</b> along corridor</div>
                    <div>Distance to Dest: <b>${bus.dist_to_destination_km} km</b></div>
                    <div>ETA to Destination: <b style="color: #ff9933;">${bus.eta_to_dest_mins} mins</b></div>
                    <div style="color: #38bdf8; font-weight: 600; margin-top: 2px;">Status: ${bus.status}</div>
                  </div>
                </div>
              `);

              bMarker.addTo(bLayerGroup.current);
            });
          }
        });

        if (allBounds.length > 0) {
          bmap.fitBounds(allBounds, { padding: [50, 50] });
        }
      }, [origin, destination, branches, selectedBranchId]);

      return (
        <div style={{ position: 'relative', width: '100%', height: '540px', borderRadius: '12px', overflow: 'hidden', border: '1px solid rgba(255, 107, 53, 0.3)' }}>
          <div ref={bMapRef} style={{ width: '100%', height: '100%' }} />
          <div style={{
            position: 'absolute', bottom: '16px', right: '16px', background: 'rgba(15, 23, 42, 0.92)',
            border: '1px solid rgba(255, 255, 255, 0.15)', borderRadius: '10px', padding: '10px 14px',
            backdropFilter: 'blur(10px)', zIndex: 1000, fontSize: '11px', minWidth: '180px'
          }}>
            <b style={{ color: '#ff9933', display: 'block', marginBottom: '6px' }}>🔀 CORRIDOR BRANCHES</b>
            {(branches || []).map(b => (
              <div key={b.branch_id} style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px', cursor: 'pointer' }} onClick={() => onSelectBranch(b.branch_id)}>
                <span style={{ width: '12px', height: '12px', borderRadius: '50%', background: b.color, display: 'inline-block' }} />
                <span style={{ color: '#f1f5f9', fontWeight: 600 }}>{b.name.split(':')[0]}</span>
                <span style={{ color: '#94a3b8', marginLeft: 'auto' }}>({b.total_active_buses} buses)</span>
              </div>
            ))}
          </div>
        </div>
      );
    }

    // Main Multi-Route Corridor & Bus Branching Component
    function CorridorBranchingComponent({ stops, origin, destination, setOrigin, setDestination, branchData, loading, onRefresh }) {
      const [selectedBranchId, setSelectedBranchId] = useState('ALL');

      const handleSwap = () => {
        const temp = origin;
        setOrigin(destination);
        setDestination(temp);
      };

      const branches = branchData?.branches || [];
      const recommended = branches[0];

      return (
        <div className="glass-panel" style={{ padding: '24px', marginTop: '20px' }}>
          {/* Header Controls */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px', marginBottom: '20px' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span style={{ fontSize: '1.5rem' }}>🔀</span>
                <h2 style={{ fontSize: '1.4rem', fontWeight: 800, color: '#f1f5f9' }}>
                  Multi-Route Corridor & Bus Branching Engine
                </h2>
              </div>
              <p style={{ fontSize: '0.84rem', color: '#94a3b8', marginTop: '4px' }}>
                Reads every Delhi bus route, groups parallel transit corridors into branches, and tracks all live buses running between 2 points in real-time
              </p>
            </div>

            <button
              onClick={onRefresh}
              disabled={loading}
              style={{
                background: 'linear-gradient(135deg, #FF6B35 0%, #e85d04 100%)',
                color: '#fff', border: 'none', padding: '8px 16px', borderRadius: '8px',
                fontWeight: 600, fontSize: '0.85rem', cursor: loading ? 'not-allowed' : 'pointer'
              }}
            >
              {loading ? 'Analyzing Corridors...' : '🔄 Recalculate Live Branches'}
            </button>
          </div>

          {/* OD Selection Bar */}
          <div style={{
            background: 'rgba(15, 23, 42, 0.75)', border: '1px solid rgba(255, 107, 53, 0.35)',
            borderRadius: '12px', padding: '16px 20px', marginBottom: '20px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
              <div style={{ flex: 1, minWidth: '220px' }}>
                <label style={{ fontSize: '0.75rem', fontWeight: 700, color: '#10b981', display: 'block', marginBottom: '4px' }}>
                  🟢 POINT A (ORIGIN)
                </label>
                <select
                  value={origin}
                  onChange={e => setOrigin(e.target.value)}
                  style={{ width: '100%', background: '#0f172a', color: '#f1f5f9', border: '1px solid rgba(16, 185, 129, 0.4)', borderRadius: '8px', padding: '10px 12px', fontWeight: 600 }}
                >
                  {stops.map(s => <option key={s.stop_id} value={s.name}>{s.name}</option>)}
                </select>
              </div>

              <button
                onClick={handleSwap}
                title="Swap Origin and Destination"
                style={{
                  background: 'rgba(30, 41, 59, 0.8)', border: '1px solid rgba(255, 255, 255, 0.2)',
                  color: '#ff9933', width: '40px', height: '40px', borderRadius: '50%',
                  cursor: 'pointer', fontSize: '1.1rem', display: 'flex', alignItems: 'center', justifyContent: 'center',
                  alignSelf: 'flex-end', marginBottom: '2px'
                }}
              >
                ⇄
              </button>

              <div style={{ flex: 1, minWidth: '220px' }}>
                <label style={{ fontSize: '0.75rem', fontWeight: 700, color: '#ef4444', display: 'block', marginBottom: '4px' }}>
                  🔴 POINT B (DESTINATION)
                </label>
                <select
                  value={destination}
                  onChange={e => setDestination(e.target.value)}
                  style={{ width: '100%', background: '#0f172a', color: '#f1f5f9', border: '1px solid rgba(239, 68, 68, 0.4)', borderRadius: '8px', padding: '10px 12px', fontWeight: 600 }}
                >
                  {stops.map(s => <option key={s.stop_id} value={s.name}>{s.name}</option>)}
                </select>
              </div>
            </div>

            {/* Quick 1-Click Delhi OD Presets */}
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginTop: '12px', flexWrap: 'wrap' }}>
              <span style={{ fontSize: '0.75rem', color: '#94a3b8', fontWeight: 600 }}>Quick Delhi Pairs:</span>
              {[
                { label: '🏢 CP ➔ AIIMS', o: 'Connaught Place', d: 'AIIMS' },
                { label: '✈️ Dwarka ➔ CP', o: 'Dwarka Sec-21', d: 'Connaught Place' },
                { label: '🏰 Rohini ➔ AIIMS', o: 'Rohini Sec-3', d: 'AIIMS' },
                { label: '🌉 ISBT ➔ Anand Vihar', o: 'ISBT Kashmere Gate', d: 'Anand Vihar ISBT' },
                { label: '🏛️ Janakpuri ➔ ITO', o: 'Janakpuri', d: 'ITO' },
              ].map((p, idx) => (
                <button
                  key={idx}
                  onClick={() => { setOrigin(p.o); setDestination(p.d); }}
                  style={{
                    background: (origin === p.o && destination === p.d) ? 'rgba(255, 107, 53, 0.35)' : 'rgba(30, 41, 59, 0.6)',
                    border: `1px solid ${(origin === p.o && destination === p.d) ? '#ff6b35' : 'rgba(255, 255, 255, 0.08)'}`,
                    color: (origin === p.o && destination === p.d) ? '#ff9933' : '#cbd5e1',
                    padding: '4px 10px', borderRadius: '6px', fontSize: '0.74rem', fontWeight: 600, cursor: 'pointer'
                  }}
                >
                  {p.label}
                </button>
              ))}
            </div>
          </div>

          {/* High-Level Corridor Branching KPI Banner */}
          {branchData && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))', gap: '14px', marginBottom: '20px' }}>
              <div style={{ background: 'rgba(15, 23, 42, 0.6)', border: '1px solid rgba(255, 255, 255, 0.08)', borderRadius: '10px', padding: '14px 18px' }}>
                <span style={{ fontSize: '0.72rem', color: '#94a3b8', fontWeight: 700 }}>BUSES RUNNING IN BETWEEN</span>
                <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#38bdf8', fontFamily: "'JetBrains Mono', monospace", marginTop: '4px' }}>
                  {branchData.total_buses_in_transit} buses
                </div>
                <span style={{ fontSize: '0.74rem', color: '#64748b' }}>Live GPS tracked in corridor</span>
              </div>

              <div style={{ background: 'rgba(15, 23, 42, 0.6)', border: '1px solid rgba(255, 255, 255, 0.08)', borderRadius: '10px', padding: '14px 18px' }}>
                <span style={{ fontSize: '0.72rem', color: '#94a3b8', fontWeight: 700 }}>CORRIDOR BRANCHES</span>
                <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#a855f7', fontFamily: "'JetBrains Mono', monospace", marginTop: '4px' }}>
                  {branchData.total_branches} branches
                </div>
                <span style={{ fontSize: '0.74rem', color: '#64748b' }}>Clustered parallel transit lines</span>
              </div>

              <div style={{ background: 'rgba(15, 23, 42, 0.6)', border: '1px solid rgba(255, 255, 255, 0.08)', borderRadius: '10px', padding: '14px 18px' }}>
                <span style={{ fontSize: '0.72rem', color: '#94a3b8', fontWeight: 700 }}>RECOMMENDED FASTEST BRANCH</span>
                <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#10b981', marginTop: '4px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {recommended ? recommended.name.split(':')[0] : 'N/A'}
                </div>
                <span style={{ fontSize: '0.74rem', color: '#34d399' }}>Next bus in ~{recommended?.next_bus_eta_mins} mins</span>
              </div>

              <div style={{ background: 'rgba(15, 23, 42, 0.6)', border: '1px solid rgba(255, 255, 255, 0.08)', borderRadius: '10px', padding: '14px 18px' }}>
                <span style={{ fontSize: '0.72rem', color: '#94a3b8', fontWeight: 700 }}>DIRECT DISPLACEMENT</span>
                <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#ff9933', fontFamily: "'JetBrains Mono', monospace", marginTop: '4px' }}>
                  {branchData.direct_distance_km} km
                </div>
                <span style={{ fontSize: '0.74rem', color: '#64748b' }}>Great-circle point-to-point</span>
              </div>
            </div>
          )}

          {/* Interactive Map Visualizer */}
          <div style={{ marginBottom: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px', flexWrap: 'wrap', gap: '10px' }}>
              <div style={{ fontSize: '0.92rem', fontWeight: 700, color: '#ff9933' }}>
                🗺️ Live Multi-Branch Corridor Map
              </div>

              {/* Branch Filter Tabs */}
              <div style={{ display: 'flex', gap: '6px' }}>
                <button
                  onClick={() => setSelectedBranchId('ALL')}
                  style={{
                    background: selectedBranchId === 'ALL' ? '#ff6b35' : '#1e293b',
                    color: '#fff', border: 'none', padding: '5px 12px', borderRadius: '6px', fontSize: '0.76rem', fontWeight: 700, cursor: 'pointer'
                  }}
                >
                  All Branches ({branchData?.total_buses_in_transit || 0})
                </button>
                {branches.map(b => (
                  <button
                    key={b.branch_id}
                    onClick={() => setSelectedBranchId(b.branch_id)}
                    style={{
                      background: selectedBranchId === b.branch_id ? b.color : 'rgba(30, 41, 59, 0.8)',
                      color: selectedBranchId === b.branch_id ? '#0f172a' : '#cbd5e1',
                      border: `1px solid ${b.color}40`,
                      padding: '5px 12px', borderRadius: '6px', fontSize: '0.76rem', fontWeight: 700, cursor: 'pointer'
                    }}
                  >
                    {b.name.split(':')[0]} ({b.total_active_buses})
                  </button>
                ))}
              </div>
            </div>

            <BranchMapContainer
              origin={branchData?.origin}
              destination={branchData?.destination}
              branches={branches}
              selectedBranchId={selectedBranchId}
              onSelectBranch={setSelectedBranchId}
            />
          </div>

          {/* Branched Route Families & Active Buses Cards */}
          <div>
            <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#f1f5f9', marginBottom: '14px' }}>
              🚍 Branched Corridor Families & Buses Running in Between
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              {branches.filter(b => selectedBranchId === 'ALL' || selectedBranchId === b.branch_id).map(branch => (
                <div key={branch.branch_id} style={{
                  background: 'rgba(15, 23, 42, 0.7)',
                  border: `1px solid ${branch.color}60`,
                  borderLeft: `6px solid ${branch.color}`,
                  borderRadius: '12px',
                  padding: '20px',
                  boxShadow: `0 4px 20px ${branch.color}15`
                }}>
                  {/* Branch Title & Metrics */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '14px', marginBottom: '14px' }}>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{ background: branch.color, color: '#0f172a', fontWeight: 800, fontSize: '0.72rem', padding: '2px 8px', borderRadius: '12px' }}>
                          {branch.branch_id}
                        </span>
                        <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: '#f1f5f9' }}>
                          {branch.name}
                        </h3>
                      </div>
                      <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: '4px' }}>
                        Via: <strong style={{ color: branch.color }}>{branch.via}</strong> • Associated Routes: <b>{branch.routes.join(', ')}</b>
                      </div>
                    </div>

                    <div style={{ display: 'flex', gap: '18px', flexWrap: 'wrap' }}>
                      <div style={{ textAlign: 'center' }}>
                        <span style={{ fontSize: '0.7rem', color: '#94a3b8' }}>ACTIVE FLEET</span>
                        <div style={{ fontSize: '1.15rem', fontWeight: 800, color: branch.color }}>{branch.total_active_buses} buses</div>
                      </div>
                      <div style={{ textAlign: 'center' }}>
                        <span style={{ fontSize: '0.7rem', color: '#94a3b8' }}>NEXT BUS</span>
                        <div style={{ fontSize: '1.15rem', fontWeight: 800, color: '#10b981' }}>~{branch.next_bus_eta_mins} mins</div>
                      </div>
                      <div style={{ textAlign: 'center' }}>
                        <span style={{ fontSize: '0.7rem', color: '#94a3b8' }}>HEADWAY</span>
                        <div style={{ fontSize: '1.15rem', fontWeight: 800, color: '#38bdf8' }}>{branch.avg_headway_mins} mins</div>
                      </div>
                      <div style={{ textAlign: 'center' }}>
                        <span style={{ fontSize: '0.7rem', color: '#94a3b8' }}>CORRIDOR SPEED</span>
                        <div style={{ fontSize: '1.15rem', fontWeight: 800, color: '#ff9933' }}>{branch.corridor_speed_kmh} km/h</div>
                      </div>
                    </div>
                  </div>

                  {/* Corridor Stop Sequence Track */}
                  <div style={{ background: 'rgba(30, 41, 59, 0.45)', padding: '10px 14px', borderRadius: '8px', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '6px', overflowX: 'auto' }}>
                    <span style={{ fontSize: '0.72rem', color: '#94a3b8', fontWeight: 700, whiteSpace: 'nowrap' }}>CORRIDOR TRACK:</span>
                    {branch.stops.map((st, sIdx) => (
                      <React.Fragment key={sIdx}>
                        <span style={{
                          background: sIdx === 0 ? '#10b981' : (sIdx === branch.stops.length - 1 ? '#ef4444' : '#334155'),
                          color: '#fff', fontSize: '0.72rem', fontWeight: 700, padding: '3px 8px', borderRadius: '6px', whiteSpace: 'nowrap'
                        }}>
                          {st}
                        </span>
                        {sIdx < branch.stops.length - 1 && <span style={{ color: '#64748b', fontSize: '0.8rem' }}>➔</span>}
                      </React.Fragment>
                    ))}
                  </div>

                  {/* Table of Buses Running on this Branch between Point A & B */}
                  {branch.buses && branch.buses.length > 0 ? (
                    <div>
                      <div style={{ fontSize: '0.82rem', fontWeight: 700, color: '#cbd5e1', marginBottom: '8px' }}>
                        Active Buses In Transit on this Branch ({branch.buses.length}):
                      </div>
                      <div style={{ overflowX: 'auto', maxHeight: '280px', border: '1px solid rgba(255, 255, 255, 0.08)', borderRadius: '8px' }}>
                        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem', textAlign: 'left' }}>
                          <thead style={{ background: '#1e293b', position: 'sticky', top: 0 }}>
                            <tr>
                              <th style={{ padding: '8px 12px', color: '#ff9933' }}>Bus Unit</th>
                              <th style={{ padding: '8px 12px', color: '#ff9933' }}>Route</th>
                              <th style={{ padding: '8px 12px', color: '#ff9933' }}>Velocity</th>
                              <th style={{ padding: '8px 12px', color: '#ff9933', minWidth: '160px' }}>Corridor Progress (A ➔ B)</th>
                              <th style={{ padding: '8px 12px', color: '#ff9933' }}>Dist to Dest</th>
                              <th style={{ padding: '8px 12px', color: '#ff9933' }}>Live ETA</th>
                              <th style={{ padding: '8px 12px', color: '#ff9933' }}>Status</th>
                            </tr>
                          </thead>
                          <tbody>
                            {branch.buses.map((b, bIdx) => {
                              const isNext = bIdx === 0;
                              return (
                                <tr key={b.bus_id + bIdx} style={{
                                  borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
                                  background: isNext ? `${branch.color}12` : (bIdx % 2 === 0 ? 'rgba(15, 23, 42, 0.4)' : 'transparent')
                                }}>
                                  <td style={{ padding: '8px 12px', fontWeight: 800, fontFamily: "'JetBrains Mono', monospace" }}>
                                    {isNext && <span style={{ color: '#10b981', marginRight: '4px' }}>⚡</span>}
                                    {b.bus_id}
                                  </td>
                                  <td style={{ padding: '8px 12px', color: '#38bdf8', fontWeight: 600 }}>{b.route_id}</td>
                                  <td style={{ padding: '8px 12px' }}>
                                    <span style={{ fontWeight: 700, color: b.speed_kmh >= 20 ? '#10b981' : (b.speed_kmh >= 8 ? '#f59e0b' : '#ef4444') }}>
                                      {b.speed_kmh} km/h
                                    </span>
                                  </td>
                                  <td style={{ padding: '8px 12px' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                      <div style={{ flex: 1, height: '6px', background: '#334155', borderRadius: '3px', overflow: 'hidden' }}>
                                        <div style={{ width: `${b.progress_pct}%`, height: '100%', background: branch.color }} />
                                      </div>
                                      <span style={{ fontSize: '0.72rem', color: '#cbd5e1', minWidth: '35px' }}>{b.progress_pct}%</span>
                                    </div>
                                  </td>
                                  <td style={{ padding: '8px 12px', color: '#94a3b8' }}>{b.dist_to_destination_km} km</td>
                                  <td style={{ padding: '8px 12px' }}>
                                    <span style={{
                                      fontWeight: 800,
                                      color: isNext ? '#10b981' : '#cbd5e1',
                                      padding: isNext ? '2px 6px' : '0',
                                      borderRadius: '4px',
                                      background: isNext ? '#10b98120' : 'transparent'
                                    }}>
                                      {b.eta_to_dest_mins} mins
                                    </span>
                                  </td>
                                  <td style={{ padding: '8px 12px' }}>
                                    <span style={{
                                      fontSize: '0.72rem', padding: '2px 8px', borderRadius: '10px',
                                      background: b.status.includes('Near') ? '#10b98125' : (b.status.includes('Mid') ? '#38bdf825' : '#f59e0b25'),
                                      color: b.status.includes('Near') ? '#34d399' : (b.status.includes('Mid') ? '#38bdf8' : '#fbbf24')
                                    }}>
                                      {b.status}
                                    </span>
                                  </td>
                                </tr>
                              );
                            })}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  ) : (
                    <div style={{ fontSize: '0.78rem', color: '#f59e0b', fontStyle: 'italic', padding: '10px 0' }}>
                      No buses detected mid-transit along this specific branch corridor right now.
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      );
    }
"""

if "function CorridorBranchingComponent" not in text:
    text = text.replace("ReactDOM.createRoot(document.getElementById('root')).render(<App />);", branch_components + "\n    ReactDOM.createRoot(document.getElementById('root')).render(<App />);")
    print("Added CorridorBranchingComponent and BranchMapContainer definitions successfully.")

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("Updated static/index.html with Multi-Route Corridor & Bus Branching feature!")
