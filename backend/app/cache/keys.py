def _coord(value: float, places: int) -> str:
    return f"{value:.{places}f}"


def list_key(version: int, category: str | None, query: str | None, page: int, page_size: int) -> str:
    return (
        f"cache:services:{version}:list:"
        f"{category or 'all'}:{query or ''}:{page}:{page_size}"
    )


def detail_key(version: int, service_id: str, lat: float | None, lng: float | None) -> str:
    origin = "none"
    if lat is not None and lng is not None:
        origin = f"{_coord(lat, 4)}:{_coord(lng, 4)}"
    return f"cache:services:{version}:detail:{service_id}:{origin}"


def nearby_key(
    version: int,
    lat: float,
    lng: float,
    radius_km: float,
    category: str | None,
    limit: int,
) -> str:
    # Four decimal places is about 11 metres. Callers inside that cell share a result.
    return (
        f"cache:services:{version}:nearby:"
        f"{_coord(lat, 4)}:{_coord(lng, 4)}:{radius_km:.2f}:{category or 'all'}:{limit}"
    )


def map_key(
    version: int,
    min_lat: float,
    min_lng: float,
    max_lat: float,
    max_lng: float,
    category: str | None,
    limit: int,
) -> str:
    return (
        f"cache:services:{version}:map:"
        f"{_coord(min_lat, 3)}:{_coord(min_lng, 3)}:{_coord(max_lat, 3)}:{_coord(max_lng, 3)}:"
        f"{category or 'all'}:{limit}"
    )


def stats_key(version: int) -> str:
    return f"cache:services:{version}:stats"
