import re
from typing import Optional, Dict

# Canonical alias lookup map
DESTINATION_ALIASES: Dict[str, str] = {
    "nyc": "new york",
    "new york city": "new york",
    "ny": "new york",
    "bombay": "mumbai",
    "bom": "mumbai",
    "blr": "bengaluru",
    "bangalore": "bengaluru",
    "hawaii": "hawaii",
    "oahu": "hawaii",
    "waikiki": "hawaii",
    "honolulu": "hawaii",
    "south korea": "seoul",
    "korea": "seoul",
    "uk": "london",
    "united kingdom": "london",
    "england": "london",
    "great britain": "london",
    "uae": "dubai",
    "united arab emirates": "dubai",
    "cochin": "kochi",
    "cok": "kochi",
    "madras": "chennai",
    "maa": "chennai",
    "calcutta": "kolkata",
    "ccu": "kolkata",
    "saigon": "ho chi minh city",
}

# Curated destination high-resolution 16:9 images (Strictly unique URLs)
CURATED_DESTINATION_IMAGES: Dict[str, str] = {
    "bali": "https://images.unsplash.com/photo-1537996194471-e657df975ab4?auto=format&fit=crop&w=1200&q=80",
    "tokyo": "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?auto=format&fit=crop&w=1200&q=80",
    "paris": "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?auto=format&fit=crop&w=1200&q=80",
    "varkala": "https://images.unsplash.com/photo-1590050752117-238cb0fb12b1?auto=format&fit=crop&w=1200&q=80",
    "london": "https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?auto=format&fit=crop&w=1200&q=80",
    "new york": "https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9?auto=format&fit=crop&w=1200&q=80",
    "rome": "https://images.unsplash.com/photo-1552832230-c0197dd311b5?auto=format&fit=crop&w=1200&q=80",
    "sydney": "https://images.unsplash.com/photo-1506973035872-a4ec16b8e8d9?auto=format&fit=crop&w=1200&q=80",
    "dubai": "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?auto=format&fit=crop&w=1200&q=80",
    "singapore": "https://images.unsplash.com/photo-1525625293386-3f8f99389edd?auto=format&fit=crop&w=1200&q=80",
    "kyoto": "https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?auto=format&fit=crop&w=1200&q=80",
    "osaka": "https://images.unsplash.com/photo-1590559899731-a382839e5549?auto=format&fit=crop&w=1200&q=80",
    "mumbai": "https://images.unsplash.com/photo-1570168007204-dfb528c6958f?auto=format&fit=crop&w=1200&q=80",
    "delhi": "https://images.unsplash.com/photo-1587474260584-136574528ed5?auto=format&fit=crop&w=1200&q=80",
    "coimbatore": "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&w=1200&q=80",
    "maldives": "https://images.unsplash.com/photo-1514282401047-d79a71a590e8?auto=format&fit=crop&w=1200&q=80",
    "amsterdam": "https://images.unsplash.com/photo-1512470876302-972faa2aa9a4?auto=format&fit=crop&w=1200&q=80",
    "barcelona": "https://images.unsplash.com/photo-1583422409516-2895a77efded?auto=format&fit=crop&w=1200&q=80",
    "seoul": "https://images.unsplash.com/photo-1538485399081-7191377e8241?auto=format&fit=crop&w=1200&q=80",
    "hawaii": "https://images.unsplash.com/photo-1542259009477-d625272157b7?auto=format&fit=crop&w=1200&q=80",
    "kochi": "https://images.unsplash.com/photo-1602216056096-3b40cc0c9944?auto=format&fit=crop&w=1200&q=80",
    "chennai": "https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?auto=format&fit=crop&w=1200&q=80",
    "kolkata": "https://images.unsplash.com/photo-1558431382-27e303142255?auto=format&fit=crop&w=1200&q=80",
    "ho chi minh city": "https://images.unsplash.com/photo-1583417319070-4a69db38a482?auto=format&fit=crop&w=1200&q=80",
    "bengaluru": "https://images.unsplash.com/photo-1596176530529-78163a4f7af2?auto=format&fit=crop&w=1200&q=80",
    "venice": "https://images.unsplash.com/photo-1514890547357-a9ee288728e0?auto=format&fit=crop&w=1200&q=80",
    "prague": "https://images.unsplash.com/photo-1519671482749-fd09be7ccebf?auto=format&fit=crop&w=1200&q=80",
    "vienna": "https://images.unsplash.com/photo-1516550893923-42d28e5677af?auto=format&fit=crop&w=1200&q=80",
    "berlin": "https://images.unsplash.com/photo-1560969184-10fe8719e047?auto=format&fit=crop&w=1200&q=80",
    "bangkok": "https://images.unsplash.com/photo-1508009603885-50cf7c579365?auto=format&fit=crop&w=1200&q=80",
    "istanbul": "https://images.unsplash.com/photo-1524231757912-21f4fe3a7200?auto=format&fit=crop&w=1200&q=80",
    "san francisco": "https://images.unsplash.com/photo-1501594907352-04cda38ebc29?auto=format&fit=crop&w=1200&q=80",
    "los angeles": "https://images.unsplash.com/photo-1580655653885-65763b2597d0?auto=format&fit=crop&w=1200&q=80",
}

# 10 Distinct Fallback Images for Unmapped Destinations (Strictly unique URLs)
DETERMINISTIC_FALLBACK_POOL = [
    "https://images.unsplash.com/photo-1488646953014-85cb44e25828?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1476514525535-07fb3b4ae5f1?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1503220317375-aaad61436b1b?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1500835556837-99ac94a94552?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1447752875215-b2761acb3c5d?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1519046904884-53103b34b206?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1499856871958-5b9627545d1a?auto=format&fit=crop&w=1200&q=80",
]

DEFAULT_COVER_IMAGE = DETERMINISTIC_FALLBACK_POOL[0]
_IMAGE_CACHE: Dict[str, str] = {}


class CoverImageService:
    @staticmethod
    def extract_primary_city(destination: str) -> str:
        """Extract primary city name before commas, hyphens, or brackets."""
        if not destination:
            return ""
        parts = re.split(r'[,|\-]', destination)
        primary = parts[0].strip().lower()
        return primary

    @classmethod
    def normalize_destination(cls, destination: Optional[str]) -> str:
        if not destination or not destination.strip():
            return ""
        primary = cls.extract_primary_city(destination)
        if primary in DESTINATION_ALIASES:
            return DESTINATION_ALIASES[primary]
        for alias, target in DESTINATION_ALIASES.items():
            if primary == alias or primary.startswith(alias + " ") or primary.endswith(" " + alias):
                return target
        return primary

    @classmethod
    def get_cover_image(cls, destination: Optional[str], custom_image_url: Optional[str] = None) -> str:
        """Resolve cover image with priority order:
        1. Custom uploaded image_url
        2. Curated local destination map (keyed by normalized primary city)
        3. Deterministic hash fallback pool (keyed by normalized primary city)
        """
        if custom_image_url and custom_image_url.strip():
            return custom_image_url.strip()

        city = cls.normalize_destination(destination)
        if not city:
            return DEFAULT_COVER_IMAGE

        if city in _IMAGE_CACHE:
            url = _IMAGE_CACHE[city]
            print(f"[CoverImageResolver] Cache hit: '{destination}' -> Normalized City '{city}' -> '{url}'")
            return url

        # 1. Exact match in curated catalog
        if city in CURATED_DESTINATION_IMAGES:
            url = CURATED_DESTINATION_IMAGES[city]
            _IMAGE_CACHE[city] = url
            print(f"[CoverImageResolver] Curated match: '{destination}' -> Normalized City '{city}' -> '{url}'")
            return url

        # 2. Token match in curated catalog
        tokens = [t.strip() for t in city.replace(",", " ").split() if t.strip()]
        for token in tokens:
            if token in DESTINATION_ALIASES:
                canonical = DESTINATION_ALIASES[token]
                if canonical in CURATED_DESTINATION_IMAGES:
                    url = CURATED_DESTINATION_IMAGES[canonical]
                    _IMAGE_CACHE[city] = url
                    print(f"[CoverImageResolver] Token Alias match: '{destination}' -> Token '{token}' -> Canonical '{canonical}' -> '{url}'")
                    return url
            if token in CURATED_DESTINATION_IMAGES:
                url = CURATED_DESTINATION_IMAGES[token]
                _IMAGE_CACHE[city] = url
                print(f"[CoverImageResolver] Token match: '{destination}' -> Token '{token}' -> '{url}'")
                return url

        # 3. Deterministic hash fallback pool
        idx = sum(ord(c) for c in city) % len(DETERMINISTIC_FALLBACK_POOL)
        url = DETERMINISTIC_FALLBACK_POOL[idx]
        _IMAGE_CACHE[city] = url
        print(f"[CoverImageResolver] Fallback pool match: '{destination}' -> City '{city}' -> Pool Index {idx} -> '{url}'")
        return url
