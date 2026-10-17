"""media_urls validation for report create and update (#1174)."""

import pytest
from pydantic import ValidationError

from src.core.config import get_settings
from src.modules.reports.media import validate_media_url
from src.modules.reports.schemas import CreateReportRequest, UpdateReportRequest

GOOD = "https://cdn.example.com/reports/photo.jpg"


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _base_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "title": "Pothole on Main Street",
        "description": "Deep pothole next to the crossing",
        "category": "infrastructure",
    }
    payload.update(overrides)
    return payload


def test_https_url_is_accepted():
    assert validate_media_url(GOOD) == GOOD


@pytest.mark.parametrize(
    "url",
    [
        "http://cdn.example.com/reports/photo.jpg",  # plain http
        "ftp://cdn.example.com/reports/photo.jpg",  # wrong scheme
        "not-a-url",
        "/relative/path.jpg",
        "https://" + "a" * 3000 + ".com/x.jpg",  # over the length cap
    ],
)
def test_bad_urls_are_rejected(url):
    with pytest.raises(ValueError):
        validate_media_url(url)


def test_create_schema_rejects_plain_http():
    with pytest.raises(ValidationError):
        CreateReportRequest(**_base_payload(media_urls=["http://cdn.example.com/a.jpg"]))


def test_update_schema_rejects_non_https_too():
    with pytest.raises(ValidationError):
        UpdateReportRequest(media_urls=["http://cdn.example.com/a.jpg"])


def test_create_and_update_share_the_same_rule():
    payload = _base_payload(media_urls=[GOOD])
    assert CreateReportRequest(**payload).media_urls == [GOOD]
    assert UpdateReportRequest(media_urls=[GOOD]).media_urls == [GOOD]


def test_allowed_hosts_are_configurable(monkeypatch):
    monkeypatch.setenv("MEDIA_ALLOWED_HOSTS", '["uploads.example.com"]')
    get_settings.cache_clear()

    assert validate_media_url("https://uploads.example.com/a.jpg") == "https://uploads.example.com/a.jpg"
    # subdomains of an allowed host are fine
    assert validate_media_url("https://eu.uploads.example.com/a.jpg").endswith("/a.jpg")

    with pytest.raises(ValueError, match="not allowed"):
        validate_media_url(GOOD)


def test_empty_allow_list_keeps_any_https_host(monkeypatch):
    monkeypatch.delenv("MEDIA_ALLOWED_HOSTS", raising=False)
    get_settings.cache_clear()
    assert validate_media_url("https://some-other-cdn.test/a.jpg").startswith("https://")


def test_length_cap_is_configurable(monkeypatch):
    monkeypatch.setenv("MEDIA_URL_MAX_LENGTH", "40")
    get_settings.cache_clear()
    with pytest.raises(ValueError, match="longer than 40"):
        validate_media_url("https://cdn.example.com/reports/a-very-long-name.jpg")
