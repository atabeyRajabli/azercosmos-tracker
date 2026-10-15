from datetime import datetime, timedelta, timezone
import math
from skyfield.api import load, wgs84, EarthSatellite
import pandas as pd

# Baku ground station coordinates
BAKU_LAT = 40.4093
BAKU_LON = 49.8671
BAKU_ELEVATION_M = 0


def get_timescale():
    """Get fresh timescale to avoid stale state."""
    return load.timescale()


def get_current_position(satellite: EarthSatellite) -> dict:
    """
    Returns the satellite's current subpoint (lat, lon, altitude).
    """
    ts = get_timescale()
    t = ts.now()
    geocentric = satellite.at(t)
    subpoint = wgs84.subpoint(geocentric)
    
    return {
        "latitude":  subpoint.latitude.degrees,
        "longitude": subpoint.longitude.degrees,
        "altitude_km": subpoint.elevation.km,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def get_ground_track(satellite: EarthSatellite, hours: float = 2.0, steps: int = 200) -> pd.DataFrame:
    """
    Compute ground track (lat/lon path) over the next `hours` hours.
    Returns a DataFrame with columns: lat, lon, time_utc.
    
    Note: for GEO satellites the track is nearly a dot.
    For Azersky (LEO) it traces a visible path.
    """
    ts = get_timescale()
    now = datetime.now(timezone.utc)
    times = [now + timedelta(minutes=(hours * 60 / steps) * i) for i in range(steps)]
    t_array = ts.utc([t.year for t in times],
                     [t.month for t in times],
                     [t.day for t in times],
                     [t.hour for t in times],
                     [t.minute for t in times],
                     [t.second for t in times])
    
    geocentric = satellite.at(t_array)
    subpoints = wgs84.subpoint(geocentric)
    
    return pd.DataFrame({
        "lat": subpoints.latitude.degrees,
        "lon": subpoints.longitude.degrees,
        "alt_km": subpoints.elevation.km,
        "time_utc": [t.isoformat() for t in times],
    })


def predict_passes(satellite: EarthSatellite,
                   hours_ahead: float = 48.0,
                   min_elevation_deg: float = 10.0) -> list[dict]:
    """
    Predict upcoming passes of `satellite` over Baku.
    
    Returns a list of pass dicts, each with:
      - rise_time, max_time, set_time (UTC ISO strings)
      - max_elevation_deg
      - duration_minutes
    
    Only relevant for LEO satellites (Azersky).
    GEO satellites (Azerspace-1/2) are always visible if above horizon.
    """
    ts = get_timescale()
    baku = wgs84.latlon(BAKU_LAT, BAKU_LON, elevation_m=BAKU_ELEVATION_M)
    
    t0 = ts.now()
    t1 = ts.tt_jd(t0.tt + hours_ahead / 24.0)
    
    # find_events returns times and event types: 0=rise, 1=culminate, 2=set
    times, events = satellite.find_events(baku, t0, t1, altitude_degrees=min_elevation_deg)
    
    passes = []
    current_pass = {}
    
    for t, event in zip(times, events):
        dt = t.utc_iso()
        if event == 0:   # rise
            current_pass = {"rise_time": dt}
        elif event == 1: # culminate (max elevation)
            difference = satellite - baku
            topocentric = difference.at(t)
            alt, az, _ = topocentric.altaz()
            current_pass["max_time"] = dt
            current_pass["max_elevation_deg"] = round(alt.degrees, 2)
            current_pass["azimuth_deg"] = round(az.degrees, 2)
        elif event == 2: # set
            if current_pass.get("rise_time"):
                current_pass["set_time"] = dt
                # compute duration
                rise_dt = datetime.fromisoformat(current_pass["rise_time"].replace("Z", "+00:00"))
                set_dt  = datetime.fromisoformat(dt.replace("Z", "+00:00"))
                current_pass["duration_minutes"] = round((set_dt - rise_dt).total_seconds() / 60, 1)
                passes.append(current_pass)
                current_pass = {}
    
    return passes


def get_elevation_from_baku(satellite: EarthSatellite) -> float:
    """
    Returns the current elevation angle (degrees) of the satellite as seen from Baku.
    Positive = above horizon, negative = below.
    Returns NaN if computation fails.
    """
    try:
        ts = get_timescale()
        t = ts.now()
        print(f"  [DEBUG] get_elevation_from_baku: timescale={ts}, t={t}")
        
        baku = wgs84.latlon(BAKU_LAT, BAKU_LON)
        print(f"  [DEBUG] Baku location: {baku}")
        
        difference = satellite - baku
        print(f"  [DEBUG] difference object created: {difference}")
        
        topocentric = difference.at(t)
        print(f"  [DEBUG] topocentric: {topocentric}")
        
        alt, az, distance = topocentric.altaz()
        print(f"  [DEBUG] alt={alt}, az={az}, distance={distance}")
        print(f"  [DEBUG] alt.degrees={alt.degrees}")
        
        return float(alt.degrees)
    except Exception as e:
        import traceback
        print(f"  [ERROR] Elevation computation failed: {e}")
        traceback.print_exc()
        return math.nan
