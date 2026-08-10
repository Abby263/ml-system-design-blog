import hashlib
import hmac

from .settings import settings


def partition_key(policy_name: str, identity: str) -> str:
    """Keep raw API keys, user IDs, and IP addresses out of Redis keys."""
    digest = hmac.new(
        settings.identity_secret.encode(), identity.encode(), hashlib.sha256
    ).hexdigest()[:24]
    # The hash tag keeps one bucket's state on one Redis Cluster slot.
    return f"rate-limit:v1:{policy_name}:{{{digest}}}"
