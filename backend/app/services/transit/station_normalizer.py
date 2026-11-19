"""
station_normalizer.py — Mandatory English Normalization Layer for WanderWise Transit

Normalizes station names, airport names, landmarks, and transit modes into clean English
while preserving original provider IDs and coordinates internally.
"""

import re
from typing import Optional

# Japanese Kanji/Kana to English station and landmark mappings
JAPANESE_NAME_MAP = {
    # Kyoto landmarks & stations
    "京都駅前": "Kyoto Station",
    "京都駅": "Kyoto Station",
    "京都": "Kyoto",
    "清水寺": "Kiyomizu-dera",
    "伏見稲荷大社": "Fushimi Inari Taisha",
    "伏見稲荷": "Fushimi Inari",
    "伏見稲荷駅": "Fushimi-Inari Station",
    "稲荷駅": "Inari Station",
    "稲荷": "Inari",
    "東福寺駅": "Tofukuji Station",
    "東福寺": "Tofukuji",
    "金閣寺": "Kinkaku-ji",
    "銀閣寺": "Ginkaku-ji",
    "二条城": "Nijo Castle",
    "二条城前駅": "Nijojo-mae Station",
    "二条駅": "Nijo Station",
    "二条": "Nijo",
    "嵐山駅": "Arashiyama Station",
    "嵐山": "Arashiyama",
    "祇園四条駅": "Gion-Shijo Station",
    "祇園": "Gion",
    "烏丸駅": "Karasuma Station",
    "烏丸御池駅": "Karasuma Oike Station",
    "烏丸": "Karasuma",
    "河原町駅": "Kawaramachi Station",
    "京都河原町駅": "Kyoto-Kawaramachi Station",
    "河原町": "Kawaramachi",
    "七条駅": "Shichijo Station",
    "七条": "Shichijo",
    "五条駅": "Gojo Station",
    "五条": "Gojo",
    "四条駅": "Shijo Station",
    "四条": "Shijo",
    "三条駅": "Sanjo Station",
    "三条": "Sanjo",
    "出町柳駅": "Demachiyanagi Station",
    "出町柳": "Demachiyanagi",
    "北野白梅町駅": "Kitano-Hakubaicho Station",
    "北野白梅町": "Kitano-Hakubaicho",
    "宇治駅": "Uji Station",
    "宇治": "Uji",
    # Osaka & Kansai
    "関西空港駅": "Kansai Airport Station",
    "関西国際空港": "Kansai International Airport",
    "関西空港": "Kansai International Airport",
    "大阪駅": "Osaka Station",
    "大阪": "Osaka",
    "新大阪駅": "Shin-Osaka Station",
    "新大阪": "Shin-Osaka",
    "難波駅": "Namba Station",
    "なんば駅": "Namba Station",
    "難波": "Namba",
    "天王寺駅": "Tennoji Station",
    "天王寺": "Tennoji",
    "梅田駅": "Umeda Station",
    "梅田": "Umeda",
    # Tokyo
    "東京駅": "Tokyo Station",
    "東京": "Tokyo",
    "新宿駅": "Shinjuku Station",
    "新宿": "Shinjuku",
    "渋谷駅": "Shibuya Station",
    "渋谷": "Shibuya",
    "品川駅": "Shinagawa Station",
    "品川": "Shinagawa",
    "上野駅": "Ueno Station",
    "上野": "Ueno",
    "羽田空港": "Haneda Airport",
    "成田空港": "Narita Airport",
}

# Indian Railways abbreviations to full English names
INDIAN_STATION_MAP = {
    "COIMBATORE JN": "Coimbatore Junction",
    "COIMBATORE JUNCTION": "Coimbatore Junction",
    "COIMBATORE": "Coimbatore Junction",
    "CBE": "Coimbatore Junction",
    "CHENNAI CENTRAL": "Chennai Central",
    "MGR CHENNAI CENTRAL": "Chennai Central",
    "M.G.R CHENNAI CENTRAL": "Chennai Central",
    "M.G.R. CHENNAI CENTRAL": "Chennai Central",
    "CHENNAI": "Chennai Central",
    "MAS": "Chennai Central",
    "CHENNAI EGMORE": "Chennai Egmore",
    "MS": "Chennai Egmore",
    "PERAMBUR": "Perambur",
    "PER": "Perambur",
    "PODANUR JN": "Podanur Junction",
    "PODANUR": "Podanur Junction",
    "PTJ": "Podanur Junction",
    "JOLARPETTAI JN": "Jolarpettai Junction",
    "JOLARPETTAI": "Jolarpettai Junction",
    "JTJ": "Jolarpettai Junction",
    "KATPADI JN": "Katpadi Junction",
    "KATPADI": "Katpadi Junction",
    "KPD": "Katpadi Junction",
    "ARAKKONAM JN": "Arakkonam Junction",
    "ARAKKONAM": "Arakkonam Junction",
    "AJJ": "Arakkonam Junction",
    "MORAPPUR": "Morappur",
    "MAP": "Morappur",
    "BOMMIDI": "Bommidi",
    "BQI": "Bommidi",
    "SANKARIDURG": "Sankaridurg",
    "SGE": "Sankaridurg",
    "UTTUKULI": "Uttukuli",
    "UKL": "Uttukuli",
    "TIRUPATTUR": "Tirupattur",
    "TPT": "Tirupattur",
    "VANIYAMBADI": "Vaniyambadi",
    "VN": "Vaniyambadi",
    "AMBUR": "Ambur",
    "AB": "Ambur",
    "WALAJAH ROAD JN": "Walajah Road Junction",
    "WJR": "Walajah Road Junction",
    "SHOLINGHUR": "Sholinghur",
    "SHU": "Sholinghur",
    "TIRUVALLUR": "Tiruvallur",
    "TRL": "Tiruvallur",
    "AVADI": "Avadi",
    "AVD": "Avadi",
    "KARUR JN.": "Karur Junction",
    "KARUR JN": "Karur Junction",
    "KARUR JUNCTION": "Karur Junction",
    "KARUR": "Karur Junction",
    "KRR": "Karur Junction",
    "ERODE JN": "Erode Junction",
    "ERODE JUNCTION": "Erode Junction",
    "ERODE": "Erode Junction",
    "ED": "Erode Junction",
    "TIRUPPUR": "Tiruppur",
    "TIRUPUR": "Tiruppur",
    "TUP": "Tiruppur",
    "SALEM JN": "Salem Junction",
    "SALEM JUNCTION": "Salem Junction",
    "SALEM": "Salem Junction",
    "SA": "Salem Junction",
    "KSR BENGALURU": "KSR Bengaluru",
    "BANGALORE CITY": "KSR Bengaluru",
    "BENGALURU": "KSR Bengaluru",
    "BANGALORE": "KSR Bengaluru",
    "SBC": "KSR Bengaluru",
    "COIMBATORE JN.": "Coimbatore Junction",
    "KARUR JN.": "Karur Junction",
    "KRISHNARAJAPURM": "Krishnarajapuram",
    "KRISHNARAJAPURAM": "Krishnarajapuram",
    "KJM": "Krishnarajapuram",
    "MADURAI JN": "Madurai Junction",
    "MADURAI": "Madurai Junction",
    "MDU": "Madurai Junction",
    "TIRUCHCHIRAPPALLI JN": "Tiruchchirappalli Junction",
    "TIRUCHIRAPPALLI": "Tiruchchirappalli Junction",
    "TRICHY": "Tiruchchirappalli Junction",
    "TPJ": "Tiruchchirappalli Junction",
    "NAGERCOIL JN": "Nagercoil Junction",
    "NAGERCOIL": "Nagercoil Junction",
    "NCJ": "Nagercoil Junction",
    "PALAKKAD JN": "Palakkad Junction",
    "PALAKKAD": "Palakkad Junction",
    "PGT": "Palakkad Junction",
    "ERNAKULAM JN": "Ernakulam Junction",
    "ERNAKULAM": "Ernakulam Junction",
    "ERS": "Ernakulam Junction",
    "THIRUVANANTHAPURAM CENTRAL": "Thiruvananthapuram Central",
    "TRIVANDRUM": "Thiruvananthapuram Central",
    "TVC": "Thiruvananthapuram Central",
    "MUMBAI CENTRAL": "Mumbai Central",
    "MMCT": "Mumbai Central",
    "MUMBAI CSMT": "Mumbai CSMT",
    "CSMT": "Mumbai CSMT",
    "MUMBAI": "Mumbai CSMT",
    "PUNE JN": "Pune Junction",
    "PUNE JUNCTION": "Pune Junction",
    "PUNE": "Pune Junction",
    "NEW DELHI": "New Delhi",
    "NDLS": "New Delhi",
    "HOWRAH JN": "Howrah Junction",
    "HWH": "Howrah Junction",
    "SECUNDERABAD JN": "Secunderabad Junction",
    "SC": "Secunderabad Junction",
}

# Mode name normalization to English
MODE_NORMALIZATION = {
    "WALK": "Walk",
    "WALKING": "Walk",
    "FOOT": "Walk",
    "PEDESTRIAN": "Walk",
    "BUS": "Bus",
    "RAIL": "Rail",
    "TRAIN": "Rail",
    "EXPRESS": "Rail",
    "SUBWAY": "Subway",
    "METRO": "Metro",
    "TRAM": "Tram",
    "FERRY": "Ferry",
    "DRIVING": "Driving",
    "ROAD": "Driving",
    "CAR": "Driving",
    "FLIGHT": "Flight",
    "AIR": "Flight",
    "TRANSFER": "Transfer",
    "LONG_DISTANCE": "Long Distance Rail",
    "HIGHSPEED_RAIL": "High-Speed Rail",
    "REGIONAL_RAIL": "Regional Rail",
    "NIGHT_RAIL": "Night Train",
    "SUBURBAN": "Suburban Rail",
}

# Emoji mode icons
MODE_ICONS = {
    "walk": "🚶",
    "walking": "🚶",
    "foot": "🚶",
    "pedestrian": "🚶",
    "bus": "🚌",
    "train": "🚆",
    "rail": "🚆",
    "subway": "🚇",
    "metro": "🚇",
    "tram": "🚃",
    "driving": "🚗",
    "road": "🚗",
    "car": "🚗",
    "flight": "✈️",
    "air": "✈️",
    "ferry": "⛴️",
    "transfer": "🔄",
}


def normalize_station_name(raw_name: Optional[str]) -> str:
    """
    Normalizes any station, airport, or POI name into clean English.
    Preserves original name if already clean English.
    """
    if not raw_name or not str(raw_name).strip():
        return "Unknown Station"

    name = str(raw_name).strip()

    # 1. Exact match in Japanese map
    if name in JAPANESE_NAME_MAP:
        return JAPANESE_NAME_MAP[name]

    # 2. Check if name contains any Japanese key
    for jp_key, en_val in JAPANESE_NAME_MAP.items():
        if jp_key in name:
            name = name.replace(jp_key, en_val)
            # If completely converted or mostly converted, return
            if not any('\u3000' <= char <= '\u9fff' for char in name):
                return name.strip()

    # 3. Exact match in Indian station map (case-insensitive)
    name_upper = name.upper()
    if name_upper in INDIAN_STATION_MAP:
        return INDIAN_STATION_MAP[name_upper]
    name_no_dot = name_upper.rstrip(".")
    if name_no_dot in INDIAN_STATION_MAP:
        return INDIAN_STATION_MAP[name_no_dot]

    # 4. Indian abbreviation expansions (e.g. "COIMBATORE JN" -> "Coimbatore Junction")
    cleaned = name
    if sum(1 for c in cleaned if c.isupper()) > sum(1 for c in cleaned if c.islower()):
        cleaned = cleaned.title()
    cleaned = re.sub(r'\bJn\b\.?', 'Junction', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\bCentral\b', 'Central', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\bEgmore\b', 'Egmore', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\bCantt\b\.?', 'Cantt', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\bTerm\b\.?', 'Terminal', cleaned, flags=re.IGNORECASE)

    # 5. Remove residual Japanese characters if any remain (fallback romanization or clean fallback)
    has_cjk = any('\u3000' <= char <= '\u9fff' for char in cleaned)
    if has_cjk:
        for jp_key, en_val in JAPANESE_NAME_MAP.items():
            if jp_key in cleaned:
                cleaned = cleaned.replace(jp_key, en_val)
        # If still CJK, replace common suffix characters
        cleaned = cleaned.replace("駅前", " Station").replace("駅", " Station")
        cleaned = re.sub(r'[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff]+', '', cleaned).strip()
        if not cleaned:
            return "Transit Station"

    # If all-caps, convert to Title Case
    if cleaned.isupper() and len(cleaned) > 3:
        cleaned = cleaned.title()

    return cleaned.strip()


def normalize_mode_name(raw_mode: Optional[str]) -> str:
    """Normalizes transport mode string to standardized English title."""
    if not raw_mode:
        return "Public Transit"
    m = str(raw_mode).strip().upper()
    return MODE_NORMALIZATION.get(m, m.replace("_", " ").title())


def get_mode_icon(mode: Optional[str]) -> str:
    """Returns accurate emoji icon for transport mode."""
    if not mode:
        return "🚌"
    m = str(mode).strip().lower()
    for key, icon in MODE_ICONS.items():
        if key in m:
            return icon
    return "🚌"


def is_mostly_ascii(text: Optional[str]) -> bool:
    """Checks that text contains no un-normalized CJK characters."""
    if not text:
        return True
    return not any('\u3000' <= char <= '\u9fff' for char in str(text))


# Canonical Urban Location & Station Alias Clusters
CANONICAL_CITY_ALIASES = [
    {"bangalore", "bengaluru", "ksr bengaluru", "sbc", "yesvantpur", "ypr", "krishnarajapuram", "kjm", "blr"},
    {"delhi", "new delhi", "ndls", "hazrat nizamuddin", "nizamuddin", "nzm", "anand vihar", "anvt", "del", "old delhi", "dli"},
    {"chennai", "chennai central", "mas", "chennai egmore", "ms", "perambur", "per", "tambaram", "tbm", "maa", "puratchi thalaivar", "puratchi thalaivar dr. m.g.r. central"},
    {"coimbatore", "coimbatore junction", "cbe", "coimbatore jn", "podanur", "podanur junction", "ptj", "cjb"},
    {"mumbai", "bombay", "csmt", "chhatrapati shivaji", "mumbai central", "mmct", "dadar", "dr", "bandra", "bdts", "bom"},
    {"pune", "pune junction", "pune jn", "pnq"},
    {"hyderabad", "secunderabad", "sc", "kacheguda", "kcg", "hyd"},
    {"kolkata", "calcutta", "howrah", "hwh", "sealdah", "sda", "shalimar", "shm", "ccu"},
    {"mysuru", "mysore", "mysore junction", "mysore jn", "mys"},
    {"tokyo", "tokyo station", "haneda", "haneda airport", "hnd", "narita", "narita airport", "nrt", "shinjuku", "shibuya", "shinagawa", "ueno"},
    {"kyoto", "kyoto station"},
    {"osaka", "osaka station", "shin-osaka", "kansai", "kix", "itami", "itm", "namba"},
    {"london", "heathrow", "london heathrow", "lhr", "gatwick", "london gatwick", "lgw", "london city", "lcy", "st pancras", "kings cross", "paddington"},
    {"paris", "charles de gaulle", "paris charles de gaulle", "cdg", "orly", "paris orly", "ory", "gare du nord", "gare de lyon"},
    {"new york", "nyc", "manhattan", "jfk", "john f. kennedy", "lga", "laguardia", "ewr", "newark", "penn station", "grand central"},
    {"berlin", "berlin hauptbahnhof", "berlin hbf", "ber"},
    {"munich", "münchen", "munich hbf", "muc"},
    {"madurai", "madurai junction", "madurai jn", "mdu"},
    {"salem", "salem junction", "salem jn", "sa"},
    {"erode", "erode junction", "erode jn", "ed"},
]


def clean_place_name(name: Optional[str]) -> str:
    """Removes common stop words like Station, Junction, Airport, Central to isolate core toponym."""
    if not name:
        return ""
    cleaned = str(name).lower()
    cleaned = re.sub(r'\b(junction|jn|central|station|intl|international|airport|term|terminus|city)\b', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'[^a-z0-9]', ' ', cleaned)
    return " ".join(cleaned.split())


def are_locations_compatible(
    requested: Optional[str],
    returned: Optional[str],
    req_lat: Optional[float] = None,
    req_lon: Optional[float] = None,
    ret_lat: Optional[float] = None,
    ret_lon: Optional[float] = None,
    max_drift_km: float = 35.0,
) -> bool:
    """
    Determines if a returned transit destination/station matches the user-requested destination.
    Uses:
    1. Direct string equality and containment (after normalizing stop words like Jn, Station, Airport).
    2. Canonical urban alias clusters (e.g. Bangalore ↔ KSR Bengaluru, Delhi ↔ New Delhi/NZM).
    3. Haversine distance proximity check (<= 35 km) when coordinates are available.
    """
    if not requested or not returned:
        return True

    req_lower = str(requested).strip().lower()
    ret_lower = str(returned).strip().lower()

    if req_lower == ret_lower or req_lower in ret_lower or ret_lower in req_lower:
        return True

    req_clean = clean_place_name(requested)
    ret_clean = clean_place_name(returned)
    if req_clean and ret_clean and (req_clean == ret_clean or req_clean in ret_clean or ret_clean in req_clean):
        return True

    # Canonical alias check
    for group in CANONICAL_CITY_ALIASES:
        in_req = any(alias == req_lower or alias in req_lower or req_lower in alias or (req_clean and (alias == req_clean or alias in req_clean or req_clean in alias)) for alias in group)
        in_ret = any(alias == ret_lower or alias in ret_lower or ret_lower in alias or (ret_clean and (alias == ret_clean or alias in ret_clean or ret_clean in alias)) for alias in group)
        if in_req and in_ret:
            return True

    # Geographic proximity check (<= 35.0 km)
    if req_lat is not None and req_lon is not None and ret_lat is not None and ret_lon is not None:
        try:
            from ..maps.osrm_service import haversine_distance
            dist = haversine_distance(float(req_lat), float(req_lon), float(ret_lat), float(ret_lon))
            if dist <= max_drift_km:
                return True
        except Exception:
            pass

    return False
