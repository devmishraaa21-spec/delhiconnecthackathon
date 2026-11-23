import os

path = r"C:\Users\iamde\.gemini\antigravity\scratch\delhi-bus-planner\static\index.html"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

# 1. Update Route Banner to show Fare, CO2, and Turn-by-Turn Itinerary
old_route_banner = """          {/* Route Result Banner */}
          {route && (
            <div className="glass-panel glass-panel-glow" style={{
              marginBottom: '20px', padding: '14px 22px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px'
            }}>
              <div>
                <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#38bdf8', textTransform: 'uppercase' }}>
                  OPTIMIZED ROUTE CALCULATED (DYNAMIC A*)
                </span>
                <div style={{ fontSize: '0.92rem', color: '#f1f5f9', fontWeight: 600 }}>
                  Traversing {route.segments_count} Delhi transit corridors
                </div>
              </div>
              <div style={{ display: 'flex', gap: '24px', flexWrap: 'wrap' }}>
                <div><span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>DISTANCE</span><div style={{ fontSize: '1.2rem', fontWeight: 700 }}>{route.distance_km} km</div></div>
                <div><span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>DYNAMIC ETA</span><div style={{ fontSize: '1.2rem', fontWeight: 700, color: '#10b981' }}>{route.eta_minutes} mins</div></div>
                <div><span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>SPEED</span><div style={{ fontSize: '1.2rem', fontWeight: 700, color: '#ff9933' }}>{route.effective_speed_kmh} km/h</div></div>
              </div>
            </div>
          )}"""

new_route_banner = """          {/* Route Result Banner with DTC Fare, CO2 & Turn-by-Turn Navigation */}
          {route && (
            <div className="glass-panel glass-panel-glow" style={{ marginBottom: '20px', padding: '16px 22px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '14px' }}>
                <div>
                  <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#38bdf8', textTransform: 'uppercase' }}>
                    OPTIMIZED ROUTE CALCULATED (DYNAMIC A*)
                  </span>
                  <div style={{ fontSize: '0.92rem', color: '#f1f5f9', fontWeight: 600 }}>
                    Traversing {route.segments_count} Delhi transit corridors
                  </div>
                </div>
                <div style={{ display: 'flex', gap: '20px', flexWrap: 'wrap', alignItems: 'center' }}>
                  <div><span style={{ fontSize: '0.72rem', color: '#94a3b8' }}>DISTANCE</span><div style={{ fontSize: '1.15rem', fontWeight: 700 }}>{route.distance_km} km</div></div>
                  <div><span style={{ fontSize: '0.72rem', color: '#94a3b8' }}>DYNAMIC ETA</span><div style={{ fontSize: '1.15rem', fontWeight: 700, color: '#10b981' }}>{route.eta_minutes} mins</div></div>
                  <div><span style={{ fontSize: '0.72rem', color: '#94a3b8' }}>DTC FARE</span><div style={{ fontSize: '1.15rem', fontWeight: 700, color: '#38bdf8' }}>₹{route.fare_inr || 15}</div></div>
                  <div><span style={{ fontSize: '0.72rem', color: '#94a3b8' }}>CO₂ SAVED</span><div style={{ fontSize: '1.15rem', fontWeight: 700, color: '#34d399' }}>🌱 {route.carbon_saved_kg || 0.8} kg</div></div>
                  <div><span style={{ fontSize: '0.72rem', color: '#94a3b8' }}>SPEED</span><div style={{ fontSize: '1.15rem', fontWeight: 700, color: '#ff9933' }}>{route.effective_speed_kmh} km/h</div></div>
                  <button
                    onClick={() => setShowItinerary(!showItinerary)}
                    style={{
                      background: 'rgba(255, 107, 53, 0.2)', border: '1px solid rgba(255, 107, 53, 0.5)',
                      color: '#ff9933', padding: '6px 14px', borderRadius: '8px', fontSize: '0.8rem',
                      fontWeight: 700, cursor: 'pointer',
                    }}
                  >
                    {showItinerary ? '▲ Hide Steps' : `📋 Itinerary Steps (${route.itinerary ? route.itinerary.length : 0})`}
                  </button>
                </div>
              </div>

              {/* Turn-by-Turn Journey Itinerary Card */}
              {showItinerary && route.itinerary && route.itinerary.length > 0 && (
                <div style={{ marginTop: '16px', paddingTop: '14px', borderTop: '1px solid rgba(255, 255, 255, 0.1)' }}>
                  <div style={{ fontSize: '0.82rem', fontWeight: 700, color: '#ff9933', marginBottom: '10px', textTransform: 'uppercase' }}>
                    🧭 Turn-by-Turn Commuter Itinerary
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '10px' }}>
                    {route.itinerary.map((step, idx) => (
                      <div key={idx} style={{
                        background: 'rgba(15, 23, 42, 0.65)', border: '1px solid rgba(255, 255, 255, 0.08)',
                        borderRadius: '8px', padding: '10px 14px', display: 'flex', gap: '12px', alignItems: 'center'
                      }}>
                        <div style={{
                          width: '28px', height: '28px', borderRadius: '50%',
                          background: idx === 0 ? '#10b981' : (idx === route.itinerary.length - 1 ? '#ef4444' : '#0284c7'),
                          display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.8rem', fontWeight: 800, color: '#fff', flexShrink: 0
                        }}>
                          {idx === 0 ? '🟢' : (idx === route.itinerary.length - 1 ? '🏁' : idx + 1)}
                        </div>
                        <div style={{ flex: 1 }}>
                          <div style={{ fontSize: '0.84rem', fontWeight: 600, color: '#f1f5f9' }}>{step.instruction}</div>
                          <div style={{ fontSize: '0.74rem', color: '#94a3b8', marginTop: '2px' }}>
                            {step.corridor ? `Via: ${step.corridor} • ` : ''}{step.distance_km > 0 ? `${step.distance_km} km • ~${step.duration_minutes} mins` : 'Origin Boarding Point'}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}"""

if old_route_banner in text:
    text = text.replace(old_route_banner, new_route_banner, 1)
    print("Replaced route banner successfully.")
else:
    print("Route banner target not matched.")

# 2. Update Navigation Tabs to include Alerts Tab
old_tabs = """          {/* Navigation Tabs */}
          <div style={{ display: 'flex', gap: '10px', marginBottom: '18px' }}>
            {[
              { id: 'map', label: '🗺️ Map' },
              { id: 'fleet', label: '🚌 Active Bus Fleet Explorer' },
              { id: 'ml', label: '🔮 ML Traffic Forecasting' },
            ].map(tab => ("""

new_tabs = """          {/* Navigation Tabs */}
          <div style={{ display: 'flex', gap: '10px', marginBottom: '18px', flexWrap: 'wrap' }}>
            {[
              { id: 'map', label: '🗺️ Map' },
              { id: 'fleet', label: '🚌 Active Bus Fleet Explorer' },
              { id: 'ml', label: '🔮 ML Traffic Forecasting' },
              { id: 'alerts', label: `🚨 Transit Alerts & Bunching (${(alerts.bottlenecks?.length || 0) + (alerts.bunching?.length || 0)})` },
            ].map(tab => ("""

if old_tabs in text:
    text = text.replace(old_tabs, new_tabs, 1)
    print("Replaced tabs successfully.")
else:
    print("Tabs target not matched.")

# 3. Add Voice Planner & Live Stop Arrivals Drawer in the Sidebar
old_plan_btn = """                  <div style={{ display: 'flex', gap: '8px' }}>
                    <button
                      onClick={() => {
                        const sObj = stops.find(s => s.name === selectedSrc);
                        const dObj = stops.find(s => s.name === selectedDst);
                        if (sObj && dObj) handlePlanRoute(sObj.lat, sObj.lon, dObj.lat, dObj.lon);
                      }}
                      style={{
                        flex: 1, background: 'linear-gradient(135deg, #FF6B35 0%, #e85d04 100%)',
                        color: '#fff', border: 'none', padding: '10px 14px', borderRadius: '8px',
                        fontWeight: 700, fontSize: '0.85rem', cursor: 'pointer',
                      }}
                    >
                      Compute A* Route
                    </button>
                    <button
                      onClick={() => { setRoute(null); setClickPoints({ start: null, end: null }); }}
                      style={{ background: '#1e293b', color: '#cbd5e1', border: '1px solid rgba(255,255,255,0.1)', padding: '10px 12px', borderRadius: '8px', cursor: 'pointer' }}
                    >
                      Reset
                    </button>
                  </div>"""

new_plan_btn = """                  <div style={{ display: 'flex', gap: '8px' }}>
                    <button
                      onClick={() => {
                        const sObj = stops.find(s => s.name === selectedSrc);
                        const dObj = stops.find(s => s.name === selectedDst);
                        if (sObj && dObj) handlePlanRoute(sObj.lat, sObj.lon, dObj.lat, dObj.lon);
                      }}
                      style={{
                        flex: 1, background: 'linear-gradient(135deg, #FF6B35 0%, #e85d04 100%)',
                        color: '#fff', border: 'none', padding: '10px 14px', borderRadius: '8px',
                        fontWeight: 700, fontSize: '0.85rem', cursor: 'pointer',
                      }}
                    >
                      Compute A* Route
                    </button>
                    <button
                      onClick={() => { setRoute(null); setClickPoints({ start: null, end: null }); }}
                      style={{ background: '#1e293b', color: '#cbd5e1', border: '1px solid rgba(255,255,255,0.1)', padding: '10px 12px', borderRadius: '8px', cursor: 'pointer' }}
                    >
                      Reset
                    </button>
                  </div>

                  {/* Bolo Delhi Voice-Activated Route Planner */}
                  <div style={{ marginTop: '12px' }}>
                    <button
                      onClick={handleVoiceSearch}
                      style={{
                        width: '100%',
                        background: isListening ? 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)' : 'rgba(255, 107, 53, 0.15)',
                        border: `1px solid ${isListening ? '#ef4444' : 'rgba(255, 107, 53, 0.4)'}`,
                        color: isListening ? '#ffffff' : '#ff9933',
                        padding: '10px 14px',
                        borderRadius: '8px',
                        fontWeight: 700,
                        fontSize: '0.82rem',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '8px',
                      }}
                    >
                      <span>{isListening ? '🔴' : '🎙️'}</span>
                      {isListening ? 'Listening... Speak Now' : 'Bolo Delhi (Voice Route Search)'}
                    </button>
                    {voiceStatus && (
                      <div style={{ marginTop: '6px', fontSize: '0.74rem', color: '#38bdf8', background: 'rgba(56, 189, 248, 0.1)', padding: '6px 10px', borderRadius: '6px' }}>
                        {voiceStatus}
                      </div>
                    )}
                  </div>"""

if old_plan_btn in text:
    text = text.replace(old_plan_btn, new_plan_btn, 1)
    print("Replaced plan button with voice button successfully.")
else:
    print("Plan button target not matched.")

# 4. Add Live Next-Bus ETA Drawer right above presets in sidebar
old_presets_start = """                <div>
                  <h3 style={{ fontSize: '0.9rem', fontWeight: 700, color: '#ff9933', marginBottom: '10px' }}>
                    ⚡ POPULAR COMMUTER PRESETS
                  </h3>"""

new_presets_start = """                {/* Live Next-Bus ETA Countdown Board */}
                {selectedStopData && (
                  <div style={{
                    background: 'rgba(2, 132, 199, 0.12)', border: '1px solid rgba(56, 189, 248, 0.4)',
                    borderRadius: '10px', padding: '12px 14px', marginBottom: '6px'
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                      <div style={{ fontSize: '0.84rem', fontWeight: 700, color: '#38bdf8' }}>
                        🚏 {selectedStopData.stop_name}
                      </div>
                      <button
                        onClick={() => setSelectedStopData(null)}
                        style={{ background: 'transparent', border: 'none', color: '#94a3b8', fontSize: '0.8rem', cursor: 'pointer', padding: '0 4px' }}
                      >
                        ✕
                      </button>
                    </div>
                    <div style={{ fontSize: '0.72rem', color: '#94a3b8', marginBottom: '8px' }}>
                      Incoming real-time arrivals (within 7.5km):
                    </div>
                    {selectedStopData.arrivals && selectedStopData.arrivals.length > 0 ? (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', maxHeight: '180px', overflowY: 'auto' }}>
                        {selectedStopData.arrivals.slice(0, 6).map((arr, i) => (
                          <div key={i} style={{
                            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                            background: 'rgba(15, 23, 42, 0.7)', padding: '6px 10px', borderRadius: '6px', fontSize: '0.76rem'
                          }}>
                            <div>
                              <strong style={{ color: '#f1f5f9' }}>Route {arr.route_id}</strong>
                              <span style={{ fontSize: '0.7rem', color: '#64748b', marginLeft: '6px' }}>#{arr.bus_id}</span>
                            </div>
                            <div style={{ textAlign: 'right' }}>
                              <span style={{ fontWeight: 800, color: arr.eta_minutes <= 5 ? '#10b981' : '#ff9933' }}>
                                {arr.eta_minutes} mins
                              </span>
                              <div style={{ fontSize: '0.68rem', color: '#94a3b8' }}>{arr.distance_km}km • {arr.speed_kmh}km/h</div>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div style={{ fontSize: '0.75rem', color: '#f59e0b', fontStyle: 'italic' }}>
                        No incoming buses detected within 7.5km right now.
                      </div>
                    )}
                  </div>
                )}

                <div>
                  <h3 style={{ fontSize: '0.9rem', fontWeight: 700, color: '#ff9933', marginBottom: '10px' }}>
                    ⚡ POPULAR COMMUTER PRESETS
                  </h3>"""

if old_presets_start in text:
    text = text.replace(old_presets_start, new_presets_start, 1)
    print("Added live arrivals drawer successfully.")
else:
    print("Presets start target not matched.")

# 5. Add TAB 4: AlertsComponent at the bottom of the tabs
old_tab_end = """          {/* TAB 3: PREDICTIONS */}
          {activeTab === 'ml' && <PredictionsComponent predictions={predictions} />}
        </div>"""

new_tab_end = """          {/* TAB 3: PREDICTIONS */}
          {activeTab === 'ml' && <PredictionsComponent predictions={predictions} />}

          {/* TAB 4: ALERTS & BUNCHING */}
          {activeTab === 'alerts' && <AlertsComponent alerts={alerts} />}
        </div>"""

if old_tab_end in text:
    text = text.replace(old_tab_end, new_tab_end, 1)
    print("Added Alerts tab view successfully.")
else:
    print("Tab end target not matched.")

# 6. Add AlertsComponent definition
alerts_comp = """
    // Alerts & Bunching Component
    function AlertsComponent({ alerts }) {
      const bnecks = alerts.bottlenecks || [];
      const bunch = alerts.bunching || [];

      return (
        <div className="glass-panel" style={{ padding: '24px', marginTop: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '10px' }}>
            <div>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#f1f5f9' }}>
                🚨 Transit Congestion & Fleet Bunching Feed
              </h2>
              <p style={{ fontSize: '0.82rem', color: '#94a3b8' }}>
                Real-time bottleneck detection & automated headway gap restoration algorithms
              </p>
            </div>
            <div style={{ fontSize: '0.75rem', color: '#64748b', background: '#1e293b', padding: '6px 12px', borderRadius: '8px' }}>
              Last scan: {alerts.timestamp || 'Live'}
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', alignItems: 'start' }}>
            {/* Left Column: Arterial Bottlenecks */}
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                <span style={{ fontSize: '1.1rem' }}>🛑</span>
                <h3 style={{ fontSize: '0.98rem', fontWeight: 700, color: '#ef4444' }}>
                  Arterial Bottlenecks ({bnecks.length})
                </h3>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', maxHeight: '520px', overflowY: 'auto' }}>
                {bnecks.map((b, i) => (
                  <div key={i} style={{
                    background: 'rgba(239, 68, 68, 0.08)', border: '1px solid rgba(239, 68, 68, 0.3)',
                    borderRadius: '8px', padding: '12px 14px'
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                      <strong style={{ fontSize: '0.88rem', color: '#f87171' }}>{b.road_name}</strong>
                      <span style={{
                        fontSize: '0.7rem', fontWeight: 700, padding: '2px 8px', borderRadius: '12px',
                        background: '#ef444430', color: '#f87171', border: '1px solid #ef444450'
                      }}>
                        {b.congestion_level.toUpperCase()}
                      </span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', color: '#94a3b8', marginTop: '6px' }}>
                      <span>Speed: <b style={{ color: '#f87171' }}>{b.speed_kmh} km/h</b> (Free flow: {b.free_flow_kmh} km/h)</span>
                      <span>Delay: <b style={{ color: '#fbbf24' }}>+{b.delay_index}x</b></span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Right Column: Fleet Bunching */}
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                <span style={{ fontSize: '1.1rem' }}>⚠️</span>
                <h3 style={{ fontSize: '0.98rem', fontWeight: 700, color: '#f59e0b' }}>
                  Fleet Bunching / "Bus Clumping" ({bunch.length})
                </h3>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', maxHeight: '520px', overflowY: 'auto' }}>
                {bunch.slice(0, 50).map((clump, i) => (
                  <div key={i} style={{
                    background: 'rgba(245, 158, 11, 0.08)', border: '1px solid rgba(245, 158, 11, 0.3)',
                    borderRadius: '8px', padding: '12px 14px'
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                      <strong style={{ fontSize: '0.88rem', color: '#fbbf24' }}>Route {clump.route_id}</strong>
                      <span style={{
                        fontSize: '0.72rem', fontWeight: 700, color: '#f59e0b', background: '#f59e0b25',
                        padding: '2px 8px', borderRadius: '10px'
                      }}>
                        Headway Gap: {clump.distance_m}m
                      </span>
                    </div>
                    <div style={{ fontSize: '0.78rem', color: '#cbd5e1', marginTop: '4px' }}>
                      Clumped units: <b>#{clump.bus_1_id}</b> ({clump.speed_1_kmh} km/h) & <b>#{clump.bus_2_id}</b> ({clump.speed_2_kmh} km/h)
                    </div>
                    <div style={{ fontSize: '0.73rem', color: '#38bdf8', marginTop: '6px', background: 'rgba(56, 189, 248, 0.1)', padding: '5px 8px', borderRadius: '6px' }}>
                      💡 <b>Dispatch Action:</b> {clump.recommendation}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      );
    }
"""

if "function AlertsComponent" not in text:
    text = text.replace("ReactDOM.createRoot(document.getElementById('root')).render(<App />);", alerts_comp + "\n    ReactDOM.createRoot(document.getElementById('root')).render(<App />);")
    print("Added AlertsComponent definition successfully.")

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("Saved updated static/index.html successfully.")
