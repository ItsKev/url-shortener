from dataclasses import dataclass
from typing import Any


@dataclass
class UrlItem:
    id: str
    short_code: str
    original_url: str

    def to_dict(self) -> dict[str, str]:
        return {
            "id": self.id,
            "short_code": self.short_code,
            "original_url": self.original_url,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UrlItem":
        return cls(
            id=data["id"],
            short_code=data["short_code"],
            original_url=data["original_url"],
        )
