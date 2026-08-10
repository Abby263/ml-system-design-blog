import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class Item:
    item_id: str
    creator_id: str
    topic: str
    created_at: str
    quality: float


@dataclass(frozen=True)
class ModelBundle:
    version: str
    embedding_dimension: int
    items: dict[str, Item]
    popularity: list[str]
    popularity_scores: dict[str, float]
    co_watch: dict[str, list[str]]
    item_vectors: dict[str, list[float]]
    user_vectors: dict[str, list[float]]
    user_topics: dict[str, dict[str, float]]
    user_seen: dict[str, list[str]]

    def save(self, path: str) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = asdict(self)
        target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    @classmethod
    def load(cls, path: str) -> "ModelBundle":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        payload["items"] = {
            item_id: Item(**item_payload) for item_id, item_payload in payload["items"].items()
        }
        return cls(**payload)


def bundle_version(payload: dict[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()[:16]
