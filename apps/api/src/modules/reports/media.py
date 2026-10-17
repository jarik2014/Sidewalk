"""Validation for media URLs attached to reports (#1174).

One implementation shared by create and update: the previous copy in both
schemas only checked the string prefix, so `http://`, arbitrary external hosts
and unbounded lengths all passed and were rendered by the web and mobile
clients.
"""

from pydantic import HttpUrl, TypeAdapter, ValidationError

from src.core.config import get_settings

_URL_ADAPTER: TypeAdapter[HttpUrl] = TypeAdapter(HttpUrl)


def normalise_host(host: str) -> str:
    return host.strip().lower().rstrip(".")


def validate_media_url(raw: str) -> str:
    """Return the URL unchanged if acceptable, otherwise raise ``ValueError``.

    Rules:
    * must be a syntactically valid absolute URL with a host (``HttpUrl``);
    * scheme must be https — plain http is refused, it is not end-to-end
      protected and mixed content is blocked by browsers anyway;
    * length is capped (``MEDIA_URL_MAX_LENGTH``, 2048 by default);
    * if ``MEDIA_ALLOWED_HOSTS`` is configured, the host must be in it, including
      its subdomains (``cdn.example.com`` matches ``example.com``).
    """

    settings = get_settings()

    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("Media URL must not be empty")

    candidate = raw.strip()
    max_length = settings.MEDIA_URL_MAX_LENGTH
    if len(candidate) > max_length:
        raise ValueError(f"Media URL is longer than {max_length} characters")

    try:
        parsed = _URL_ADAPTER.validate_python(candidate)
    except ValidationError as exc:
        raise ValueError(f"Invalid media URL: {candidate}") from exc

    if parsed.scheme != "https":
        raise ValueError("Media URL must use https")

    allowed = [normalise_host(h) for h in settings.MEDIA_ALLOWED_HOSTS if h.strip()]
    if allowed:
        host = normalise_host(parsed.host or "")
        if not any(host == entry or host.endswith(f".{entry}") for entry in allowed):
            raise ValueError(f"Media host is not allowed: {host or 'unknown'}")

    return candidate


def validate_media_urls(urls: list[str] | None) -> list[str] | None:
    if urls is None:
        return None
    return [validate_media_url(url) for url in urls]
