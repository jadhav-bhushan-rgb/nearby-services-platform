from app.cache.keys import detail_key, list_key, nearby_key
from app.cache.rate_limit import RateLimiter
from app.core.exceptions import AppError
from app.core.security import hash_password, verify_password
from app.schemas.service import ServiceCreate, ServiceUpdate
from app.services.bulk_import import parse_upload
import pytest


class FakeRedis:
    def __init__(self):
        self.values = {}
        self.expiry = {}

    def incr(self, key):
        self.values[key] = int(self.values.get(key, 0)) + 1
        return self.values[key]

    def expire(self, key, seconds):
        self.expiry[key] = seconds

    def ttl(self, key):
        return self.expiry.get(key, -1)


def test_password_round_trip():
    hashed = hash_password("ChangeMe123!")
    assert verify_password("ChangeMe123!", hashed)
    assert not verify_password("wrong-password", hashed)


def test_cache_keys_round_nearby_coordinates():
    first = nearby_key(3, 12.97162, 77.59461, 5, "hospital", 50)
    second = nearby_key(3, 12.97164, 77.59464, 5, "hospital", 50)
    assert first == second
    assert "hospital" in first
    assert list_key(1, None, "atm", 2, 20) != list_key(2, None, "atm", 2, 20)
    assert "none" in detail_key(1, "abc", None, None)


def test_rate_limiter_blocks_after_limit():
    limiter = RateLimiter(FakeRedis())
    assert limiter.enforce("public:1", 2, 60, fail_closed=True)["remaining"] == 1
    assert limiter.enforce("public:1", 2, 60, fail_closed=True)["remaining"] == 0
    with pytest.raises(AppError) as caught:
        limiter.enforce("public:1", 2, 60, fail_closed=True)
    assert caught.value.status_code == 429
    assert caught.value.headers["Retry-After"]


def test_service_schema_rejects_impossible_coordinates():
    with pytest.raises(ValueError):
        ServiceCreate(
            name="Test",
            category="hospital",
            latitude=120,
            longitude=77,
        )


def test_update_requires_both_coordinates():
    with pytest.raises(ValueError):
        ServiceUpdate(latitude=12.9)


def test_csv_and_json_bulk_parser():
    csv_payload = (
        "name,category,latitude,longitude,rating,address\n"
        "City Hospital,hospital,12.97,77.59,4.2,MG Road\n"
        "Bad,clinic,12.97,77.59,4\n"
    ).encode()
    valid, errors = parse_upload("services.csv", csv_payload)
    assert len(valid) == 1
    assert valid[0][1].metadata["address"] == "MG Road"
    assert errors[0]["row"] == 3

    json_payload = b'[{"name":"ATM","category":"atm","latitude":12.9,"longitude":77.5}]'
    valid_json, json_errors = parse_upload("services.json", json_payload)
    assert len(valid_json) == 1
    assert json_errors == []
    assert valid_json[0][1].rating is None
