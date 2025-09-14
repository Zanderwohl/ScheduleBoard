# Timetable model: list[dict]
TIMETABLE = [
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


def _time_key(row):
    try:
        hh, mm = row.get("time", "").split(":")
        return int(hh) * 60 + int(mm)
    except Exception:
        return 24 * 60 + 59  # push malformed to bottom


