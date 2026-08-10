import ipaddress
import re
from urllib.parse import urlsplit, urlunsplit


ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
BASE = len(ALPHABET)
CUSTOM_ALIAS = re.compile(r"^[A-Za-z0-9_-]{4,32}$")
RESERVED_ALIASES = {
    "admin",
    "api",
    "docs",
    "healthz",
    "metrics",
    "openapi.json",
    "redoc",
}


def encode_base62(value: int) -> str:
    """Encode a positive integer without introducing a second ID namespace."""
    if value < 0:
        raise ValueError("value must be non-negative")
    if value == 0:
        return ALPHABET[0]

    encoded: list[str] = []
    while value:
        value, remainder = divmod(value, BASE)
        encoded.append(ALPHABET[remainder])
    return "".join(reversed(encoded))


def validate_custom_alias(alias: str) -> str:
    if not CUSTOM_ALIAS.fullmatch(alias):
        raise ValueError("alias must be 4-32 letters, numbers, underscores, or hyphens")
    if alias.lower() in RESERVED_ALIASES:
        raise ValueError("alias is reserved by the service")
    return alias


def normalize_target_url(raw_url: str) -> str:
    """Apply syntactic policy; reputation and abuse checks belong elsewhere."""
    candidate = raw_url.strip()
    if len(candidate) > 2048:
        raise ValueError("URL is longer than 2048 characters")

    parsed = urlsplit(candidate)
    if parsed.scheme.lower() not in {"http", "https"}:
        raise ValueError("only http and https URLs are accepted")
    if not parsed.hostname:
        raise ValueError("URL must include a hostname")
    if parsed.username or parsed.password:
        raise ValueError("credentials in destination URLs are not accepted")

    try:
        hostname = parsed.hostname.encode("idna").decode("ascii").lower()
    except UnicodeError as error:
        raise ValueError("hostname is not valid IDNA") from error

    try:
        parsed_port = parsed.port
    except ValueError as error:
        raise ValueError("URL contains an invalid port") from error
    port = f":{parsed_port}" if parsed_port else ""
    try:
        host_for_url = f"[{hostname}]" if ipaddress.ip_address(hostname).version == 6 else hostname
    except ValueError:
        host_for_url = hostname
    netloc = f"{host_for_url}{port}"
    path = parsed.path or "/"
    return urlunsplit((parsed.scheme.lower(), netloc, path, parsed.query, parsed.fragment))
