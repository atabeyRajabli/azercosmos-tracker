import streamlit as st
import time
from tracker.tle_fetcher import load_satellites
from tracker.orbit import (
    get_current_position,
    get_ground_track,
    predict_passes,
    get_elevation_from_baku,
)
from tracker.visualizer import build_ground_track_map, build_pass_table, build_elevation_chart

# ─── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Azercosmos Satellite Tracker",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Dark space theme */
    .stApp { background-color: #0d1117; color: #e6edf3; }
    .main .block-container { padding-top: 1.5rem; }
    
    /* Header */
    .tracker-header {
        background: linear-gradient(135deg, #0d1117 0%, #1a2744 100%);
        border: 1px solid #1f3a6e;
        border-radius: 12px;
        padding: 20px 28px;
        margin-bottom: 20px;
    }
    .tracker-header h1 {
        color: #00AEEF;
        font-size: 1.8rem;
        margin: 0;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    .tracker-header p { color: #8b949e; margin: 4px 0 0; font-size: 0.9rem; }
    
    /* Metric cards */
    .metric-card {
        background: #161b22;
        border: 1px solid #21262d;
        border-radius: 10px;
        padding: 16px 20px;
        text-align: center;
    }
    .metric-label { color: #8b949e; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px; }
    .metric-value { color: #e6edf3; font-size: 1.5rem; font-weight: 700; font-family: monospace; }
    .metric-sub   { color: #8b949e; font-size: 0.8rem; }
    
    /* Status badge */
    .status-online  { color: #3fb950; font-weight: 600; }
    .status-offline { color: #f85149; font-weight: 600; }
    
    /* Section headers */
    .section-title {
        color: #00AEEF;
        font-size: 1rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin: 24px 0 12px;
        border-bottom: 1px solid #21262d;
        padding-bottom: 8px;
    }
    
    /* Table styling */
    .stDataFrame { border: 1px solid #21262d !important; border-radius: 8px; }
    
    /* Streamlit overrides */
    div[data-testid="stMetric"] { background: #161b22; border-radius: 10px; padding: 16px; border: 1px solid #21262d; }
    div[data-testid="stMetricLabel"] { color: #8b949e !important; }
    div[data-testid="stMetricValue"] { color: #e6edf3 !important; }
</style>
""", unsafe_allow_html=True)

# ─── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="tracker-header">
    <h1>🛰️ Azercosmos Satellite Tracker</h1>
    <p>Real-time orbital tracking for Azerspace-1, Azerspace-2 & Azersky · Ground station: Baku, Azerbaijan</p>
</div>
""", unsafe_allow_html=True)

# ─── Load satellites (cached as resource) ───────────────────────────────────────
@st.cache_resource(show_spinner=False)
def load_satellite_objects():
    return load_satellites()

# ─── Load data (cached 60 seconds) ──────────────────────────────────────────────
@st.cache_data(ttl=60, show_spinner=False)
def load_positions_and_tracks(satellite_names):
    satellites = load_satellite_objects()
    positions = {}
    tracks = {}
    elevations = {}
    for name, sat in satellites.items():
        positions[name]  = get_current_position(sat)
        # LEO gets 2h track, GEO gets 24h (shows tight geo-drift)
        hours = 2.0 if "sky" in name.lower() else 24.0
        tracks[name]     = get_ground_track(sat, hours=hours, steps=300)
        elevations[name] = get_elevation_from_baku(sat)
    passes = predict_passes(satellites.get("Azersky"), hours_ahead=48) if "Azersky" in satellites else []
    return positions, tracks, elevations, passes

with st.spinner("Fetching live TLE data from Celestrak..."):
    satellites = load_satellite_objects()
    positions, tracks, elevations, passes = load_positions_and_tracks(tuple(load_satellite_objects().keys()))

# Debug: show what elevations we got
print(f"DEBUG: Elevations computed = {elevations}")
for name, el in elevations.items():
    print(f"  {name}: {el} (type: {type(el).__name__})")

# ─── Satellite status cards ──────────────────────────────────────────────────────
st.markdown('<div class="section-title">Live Status</div>', unsafe_allow_html=True)
cols = st.columns(3)
sat_names = ["Azerspace-1", "Azerspace-2", "Azersky"]
sat_types = ["GEO · 46°E · Telecom", "GEO · 45°E · Telecom", "LEO · Earth Observation"]
orbit_labels = ["Geostationary", "Geostationary", "Sun-Synchronous LEO"]

for i, (col, name, sat_type, orbit_label) in enumerate(zip(cols, sat_names, sat_types, orbit_labels)):
    with col:
        if name in positions:
            pos = positions[name]
            el  = elevations[name]
            import math
            if math.isnan(el):
                status_cls = "status-offline"
                status_txt = "⚠ Data unavailable"
            else:
                visible = el > 0
                status_cls = "status-online" if visible else "status-offline"
                status_txt = f"▲ {el:.1f}° above horizon" if visible else f"▼ {abs(el):.1f}° below horizon"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{name}</div>
                <div class="metric-value">{pos['altitude_km']:,.0f} km</div>
                <div class="metric-sub">{pos['latitude']:.2f}°N, {pos['longitude']:.2f}°E</div>
                <div class="metric-sub" style="margin-top:8px">
                    <span class="{status_cls}">{status_txt}</span>
                </div>
                <div class="metric-sub" style="color:#555;margin-top:4px">{orbit_label}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{name}</div>
                <div class="metric-value" style="color:#f85149">Unavailable</div>
                <div class="metric-sub">TLE fetch failed</div>
            </div>
            """, unsafe_allow_html=True)

# ─── Ground track map ────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Ground Track Map</div>', unsafe_allow_html=True)
fig_map = build_ground_track_map(tracks, positions)
st.plotly_chart(fig_map, width='stretch', config={"displayModeBar": False})

# ─── Pass predictions (Azersky only) ─────────────────────────────────────────────
st.markdown('<div class="section-title">Azersky Pass Predictions · Baku Ground Station</div>', unsafe_allow_html=True)

col_left, col_right = st.columns([1.5, 1])

with col_left:
    if passes:
        df_passes = build_pass_table(passes[:10])
        st.dataframe(df_passes, width='stretch', hide_index=True)
    else:
        st.info("No Azersky passes predicted over Baku in the next 48 hours.")

with col_right:
    fig_el = build_elevation_chart(passes[:10])
    st.plotly_chart(fig_el, width='stretch', config={"displayModeBar": False})

# ─── Technical notes ─────────────────────────────────────────────────────────────
with st.expander("ℹ️ Technical Notes"):
    st.markdown("""
    **Data source:** [Celestrak](https://celestrak.org/) — TLE data refreshed every 60 seconds.
    
    **Orbital model:** SGP4/SDP4 propagator via [Skyfield](https://rhodesmill.org/skyfield/) — the same model used by NORAD.
    
    **Satellite notes:**
    - **Azerspace-1** (NORAD 39441): Geostationary at ~46°E. Covers Europe, Central Asia, Sub-Saharan Africa.
    - **Azerspace-2** (NORAD 43234): Geostationary at ~45°E. C-band and Ku-band transponders.
    - **Azersky** (NORAD 40014): SPOT-7 heritage satellite, ~694 km sun-synchronous orbit. 1.5m resolution.
    
    **Pass predictions:** Computed using `EarthSatellite.find_events()` with a minimum horizon angle of 10°.
    
    **GEO pass notes:** Geostationary satellites appear nearly stationary from any fixed point; their elevation from Baku is ~38–41° (Azerspace-1/2 are permanently visible from Baku).
    """)

# ─── Footer ──────────────────────────────────────────────────────────────────────
st.markdown("""
---
<div style="text-align:center;color:#555;font-size:0.8rem;padding:8px 0">
    Built with Skyfield · Plotly · Streamlit &nbsp;|&nbsp;
    Data: Celestrak NORAD &nbsp;|&nbsp;
    Tracking Azercosmos constellation from 40.41°N, 49.87°E
</div>
""", unsafe_allow_html=True)

# Auto-refresh every 60 seconds
time.sleep(60)
st.rerun()
