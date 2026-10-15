# Azercosmos Satellite Tracker 🛰️

Real-time orbital tracker for **Azerspace-1**, **Azerspace-2**, and **Azersky** —
the three satellites operated by the Space Agency of the Republic of Azerbaijan (Azercosmos).

It pulls fresh orbital elements (TLEs) from Celestrak, propagates them with the SGP4 model, and shows where each satellite is right now, its path over the Earth, and when Azersky will next pass over Baku.


## Features
- Live subpoint (lat/lon/altitude) for all three satellites
- Ground track visualization on an interactive globe
- Pass predictions for Azersky over Baku ground station
- Elevation angle from Baku in real-time
- Auto-refreshes every 60 seconds

## Stack
- [Skyfield](https://rhodesmill.org/skyfield/) — SGP4 orbital propagator
- [Celestrak](https://celestrak.org/) — live TLE data
- [Plotly](https://plotly.com/) — ground track visualization  
- [Streamlit](https://streamlit.io/) — web dashboard

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Architecture
```
TLE fetch (Celestrak) → SGP4 propagation (Skyfield) → position/pass data → Plotly map → Streamlit UI
```

## Satellites tracked

| Satellite | NORAD | Orbit | Purpose |
|-----------|-------|-------|---------|
| Azerspace-1 | 39441 | GEO 46°E | Telecom, broadcasting |
| Azerspace-2 | 43234 | GEO 45°E | Telecom, broadband |
| Azersky | 40014 | LEO 694km | Earth observation (1.5m) |

## Ground station
Baku, Azerbaijan — 40.41°N, 49.87°E
