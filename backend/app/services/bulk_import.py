import csv
import io
import json
from typing import Any

from pydantic import ValidationError

from app.schemas.service import ServiceCategory, ServiceCreate

MAX_ROWS = 1000


def parse_upload(filename: str, payload: bytes) -> tuple[list[tuple[int, ServiceCreate]], list[dict[str, Any]]]:
    if len(payload) > 2_000_000:
        raise ValueError("File exceeds the 2 MB limit")

    text = None
    for encoding in ("utf-8-sig", "utf-8", "utf-16", "latin-1"):
        try:
            text = payload.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        raise ValueError("Unable to decode file. Please use a UTF-8 encoded CSV or JSON file.")

    name = (filename or "").lower()
    as_json = name.endswith(".json") or (not name.endswith(".csv") and text.lstrip().startswith(("{", "[")))
    raw_rows = _parse_json(text) if as_json else _parse_csv(text)
    if len(raw_rows) > MAX_ROWS:
        raise ValueError(f"A single upload can contain at most {MAX_ROWS} rows")

    valid: list[tuple[int, ServiceCreate]] = []
    errors: list[dict[str, Any]] = []
    start = 1 if as_json else 2
    for index, raw in enumerate(raw_rows, start=start):
        try:
            valid.append((index, _normalize(raw)))
        except (ValueError, ValidationError) as exc:
            message = exc.errors()[0]["msg"] if isinstance(exc, ValidationError) else str(exc)
            errors.append({"row": index, "message": message})
    return valid, errors


def _parse_json(text: str) -> list[dict]:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError("JSON file is not valid") from exc
    if isinstance(parsed, dict) and isinstance(parsed.get("services"), list):
        parsed = parsed["services"]
    if not isinstance(parsed, list):
        raise ValueError("JSON upload must be an array of services")
    rows = []
    for item in parsed:
        if not isinstance(item, dict):
            rows.append({})
        else:
            rows.append(item)
    return rows


def _parse_csv(text: str) -> list[dict]:
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        raise ValueError("CSV file is empty")

    clean_text = "\n".join(lines)
    sample = clean_text[:4096]
    dialect = None
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",\t;|")
    except Exception:
        pass

    reader = (
        csv.DictReader(io.StringIO(clean_text), dialect=dialect)
        if dialect
        else csv.DictReader(io.StringIO(clean_text))
    )
    if not reader.fieldnames:
        raise ValueError("CSV file needs a header row")

    required = {"name", "category", "latitude", "longitude"}
    fields = {name.strip().strip('"').strip("'").lower(): name for name in reader.fieldnames if name}
    missing = required - set(fields.keys())
    if missing:
        raise ValueError(f"CSV is missing columns: {', '.join(sorted(missing))}")

    rows = []
    for raw in reader:
        row_dict = {}
        for clean_col in required | {"rating", "address", "phone", "description", "metadata"}:
            orig_col = fields.get(clean_col)
            if orig_col and orig_col in raw and raw[orig_col] is not None:
                row_dict[clean_col] = raw[orig_col]
        rows.append(row_dict)
    return rows


def _normalize(raw: dict) -> ServiceCreate:
    metadata = raw.get("metadata")
    if isinstance(metadata, str) and metadata.strip():
        try:
            metadata = json.loads(metadata)
        except json.JSONDecodeError as exc:
            raise ValueError("metadata must be a JSON object") from exc
    if metadata is None:
        metadata = {}
    if not isinstance(metadata, dict):
        raise ValueError("metadata must be a JSON object")
    for source, target in (("address", "address"), ("phone", "phone"), ("description", "description")):
        value = raw.get(source)
        if isinstance(value, str) and value.strip():
            metadata[target] = value.strip()
    if not metadata:
        metadata = None

    category_raw = str(raw.get("category", "")).strip().lower()
    try:
        category = ServiceCategory(category_raw)
    except ValueError as exc:
        raise ValueError("category must be hospital, atm, shop, or other") from exc

    rating_raw = raw.get("rating")
    rating = None
    if rating_raw not in (None, ""):
        try:
            rating = float(rating_raw)
        except (TypeError, ValueError) as exc:
            raise ValueError("rating must be a number from 0 to 5") from exc

    try:
        latitude = float(raw.get("latitude"))
        longitude = float(raw.get("longitude"))
    except (TypeError, ValueError) as exc:
        raise ValueError("latitude and longitude must be numbers") from exc

    return ServiceCreate(
        name=str(raw.get("name") or ""),
        category=category,
        latitude=latitude,
        longitude=longitude,
        rating=rating,
        metadata=metadata,
    )
