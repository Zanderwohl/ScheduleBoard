# Timetable model: list[dict]
# Provide a simple generated 24h timetable based on ROUTES below

TIMETABLE_OLD = [
    {"time": "08:10", "train": "ICE 511", "via": "Frankfurt(Main)Flugh., Mannheim", "dest": "Stuttgart Hbf",
     "track": "7"},
    {"time": "08:22", "train": "RE 10123", "via": "Leverkusen Mitte, Düsseldorf", "dest": "Duisburg Hbf",
     "track": "10"},
    {"time": "08:35", "train": "ICE 705", "via": "Dortmund, Hannover", "dest": "Berlin Hbf", "track": "6"},
    {"time": "08:44", "train": "S 19", "via": "Köln/Bonn Flughafen, Troisdorf", "dest": "Hennef (Sieg)", "track": "11"},
    {"time": "08:55", "train": "ICE 923", "via": "Frankfurt(Main) Hbf, Würzburg", "dest": "München Hbf", "track": "8"},
    {"time": "09:05", "train": "IC 2021", "via": "Bonn, Koblenz", "dest": "Mainz Hbf", "track": "9"},
    {"time": "09:18", "train": "RE 10542", "via": "Horrem, Aachen", "dest": "Aachen Hbf", "track": "4"},
    {"time": "09:30", "train": "ICE 1531", "via": "Düsseldorf, Essen", "dest": "Hamburg-Altona", "track": "6"},
    {"time": "09:44", "train": "S 6", "via": "Köln-Mülheim, Leverkusen", "dest": "Essen Hbf", "track": "10"},
    {"time": "09:55", "train": "ICE 122", "via": "Frankfurt(Main)Flugh., Mannheim", "dest": "Basel SBB", "track": "7"},
]

# Backing structure: routes drive the generated timetable
# Each route: {"train": str, "via": str, "dest": str, "frequency": int, "track": str, "offset": int}
ROUTES = [
    {"train": "ICE 511", "via": "Frankfurt(Main)Flugh., Mannheim", "dest": "Stuttgart Hbf", "frequency": 120, "track": "7", "offset": 10},
    {"train": "RE 10123", "via": "Leverkusen Mitte, Düsseldorf", "dest": "Duisburg Hbf", "frequency": 60, "track": "10", "offset": 22},
    {"train": "ICE 705", "via": "Dortmund, Hannover", "dest": "Berlin Hbf", "frequency": 180, "track": "6", "offset": 35},
    {"train": "S 19", "via": "Köln/Bonn Flughafen, Troisdorf", "dest": "Hennef (Sieg)", "frequency": 20, "track": "11", "offset": 44},
    {"train": "ICE 923", "via": "Frankfurt(Main) Hbf, Würzburg", "dest": "München Hbf", "frequency": 180, "track": "8", "offset": 55},
    {"train": "IC 2021", "via": "Bonn, Koblenz", "dest": "Mainz Hbf", "frequency": 120, "track": "9", "offset": 5},
    {"train": "RE 10542", "via": "Horrem, Aachen", "dest": "Aachen Hbf", "frequency": 60, "track": "4", "offset": 18},
    {"train": "ICE 1531", "via": "Düsseldorf, Essen", "dest": "Hamburg-Altona", "frequency": 180, "track": "6", "offset": 30},
    {"train": "S 6", "via": "Köln-Mülheim, Leverkusen", "dest": "Essen Hbf", "frequency": 20, "track": "10", "offset": 44},
    {"train": "ICE 122", "via": "Frankfurt(Main)Flugh., Mannheim", "dest": "Basel SBB", "frequency": 180, "track": "7", "offset": 55},
]

TIMETABLE = []


def _time_key(row):
    try:
        hh, mm = row.get("time", "").split(":")
        return int(hh) * 60 + int(mm)
    except Exception:
        return 24 * 60 + 59  # push malformed to bottom


def filter_after_time(timetable, minutes_since_midnight):
    """Return rows whose time >= given minutes, wrapping to start after midnight."""
    try:
        def to_minutes(r):
            return _time_key(r)

        sorted_rows = sorted(timetable, key=to_minutes)
        after = [r for r in sorted_rows if to_minutes(r) >= minutes_since_midnight]
        before = [r for r in sorted_rows if to_minutes(r) < minutes_since_midnight]
        return after + before
    except Exception:
        return timetable


def generate_timetable(routes, start_minutes=0, limit=20):
    """Generate next `limit` departures starting at or after start_minutes.

    Repeats over routes as needed; does not build a full 24h list.
    Uses the route's fixed track for consistency.
    """
    start = int(start_minutes) % (24 * 60)
    # Initialize next time for each route at the first multiple of freq >= start, factoring route offset
    next_times = []  # list of (next_time_abs_minutes, route_index, freq)
    for idx, route in enumerate(routes):
        try:
            freq = int(route.get("frequency", 60))
        except Exception:
            freq = 60
        if freq <= 0:
            continue
        try:
            offset = int(route.get("offset", 0)) % freq
        except Exception:
            offset = 0
        # Align to the next multiple of freq at/after start considering offset
        base = ((max(0, start - offset) // freq) * freq) + offset
        if base < start:
            base += freq
        next_times.append([base, idx, freq])

    entries = []
    if not next_times:
        return entries

    while len(entries) < limit:
        # Find the earliest next time among routes
        min_i = 0
        min_t = next_times[0][0]
        for i in range(1, len(next_times)):
            if next_times[i][0] < min_t:
                min_t = next_times[i][0]
                min_i = i
        dep_time, route_idx, freq = next_times[min_i]
        route = routes[route_idx]
        mm_tot = dep_time % (24 * 60)
        hh = mm_tot // 60
        mm = mm_tot % 60
        entries.append({
            "time": f"{hh:02d}:{mm:02d}",
            "train": route.get("train", ""),
            "via": route.get("via", ""),
            "dest": route.get("dest", ""),
            "track": str(route.get("track", "")),
        })
        # Advance this route's next time by its frequency
        next_times[min_i][0] = dep_time + freq

    return entries


# Initialize from default routes with a small upcoming window
TIMETABLE = generate_timetable(ROUTES, 0, 20)

