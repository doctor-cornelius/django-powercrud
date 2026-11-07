"""Explicit, PowerCRUD-independent coordination configuration."""

from dataclasses import asdict, dataclass
from typing import Any, Mapping


@dataclass(frozen=True, kw_only=True)
class CoordinatorConfig:
    """Resolved configuration needed by the coordinator in one process."""

    enabled: bool = False
    cache_name: str = "default"
    key_namespace: str = "powercrud"
    key_prefixes: dict[str, str] | None = None
    conflict_ttl: int = 3600
    progress_ttl: int = 7200
    cleanup_grace_period: int = 86400
    max_task_duration: int | None = 3600
    terminal_result_ttl: int = 86400

    def resolved_key_prefixes(self) -> dict[str, str]:
        """Return the effective cache-key prefixes, including legacy defaults."""
        defaults = {
            "active_prefix": f"{self.key_namespace}:async:active_tasks",
            "conflict_prefix": f"{self.key_namespace}:async:conflict:",
            "conflict_model_prefix": f"{self.key_namespace}:conflict:model:",
            "progress_prefix": f"{self.key_namespace}:async:progress:",
        }
        if self.key_prefixes is not None:
            defaults.update(self.key_prefixes)
        return defaults

    def to_snapshot(self) -> dict[str, Any]:
        """Return a versioned primitive mapping for worker reconstruction."""
        values = asdict(self)
        values["key_prefixes"] = self.resolved_key_prefixes()
        return {"version": 1, **values}

    @classmethod
    def from_snapshot(cls, mapping: Mapping[str, Any]) -> "CoordinatorConfig":
        """Recreate configuration from a version-1 snapshot."""
        if mapping.get("version") != 1:
            raise ValueError("Unsupported coordinator configuration snapshot version")
        fields = {
            "enabled",
            "cache_name",
            "key_namespace",
            "key_prefixes",
            "conflict_ttl",
            "progress_ttl",
            "cleanup_grace_period",
            "max_task_duration",
            "terminal_result_ttl",
        }
        return cls(**{key: mapping[key] for key in fields if key in mapping})


DEFAULT_COORDINATOR_CONFIG = CoordinatorConfig()
