import requests
from skyfield.api import EarthSatellite, load

# Celestrak NORAD IDs for Azercosmos satellites
AZERCOSMOS_SATELLITES = {
    "Azerspace-1": 39441,   # Geostationary, 46°E
    "Azerspace-2": 43234,   # Geostationary, 45°E
    "Azersky":     40014,   # Low Earth Orbit, optical imaging
}

CELESTRAK_URL = "https://celestrak.org/SATCAT/TLE.php?CATNR={norad_id}"


def fetch_tle(norad_id: int) -> tuple[str, str, str]:
    """
    Fetch TLE from Celestrak for a given NORAD ID.
    Returns (name, line1, line2).
    """
    url = CELESTRAK_URL.format(norad_id=norad_id)
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    lines = [l.strip() for l in response.text.strip().splitlines() if l.strip()]
    if len(lines) < 3:
        raise ValueError(f"Unexpected TLE format for NORAD {norad_id}: {response.text}")
    return lines[0], lines[1], lines[2]


def load_satellites() -> dict[str, EarthSatellite]:
    """
    Load all Azercosmos satellites as Skyfield EarthSatellite objects.
    Returns dict: name -> EarthSatellite
    """
    ts = load.timescale()
    satellites = {}
    for name, norad_id in AZERCOSMOS_SATELLITES.items():
        try:
            sat_name, line1, line2 = fetch_tle(norad_id)
            satellites[name] = EarthSatellite(line1, line2, sat_name, ts)
            print(f"  [OK] Loaded {name} (NORAD {norad_id})")
        except Exception as e:
            print(f"  [WARN] Could not load {name}: {e}")
    return satellites


if __name__ == "__main__":
    print("Loading Azercosmos satellites...")
    sats = load_satellites()
    print(f"\nLoaded {len(sats)} satellites.")
