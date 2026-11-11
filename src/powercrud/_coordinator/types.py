"""Plain data exchanged between coordination code and the q2 adapter."""

from dataclasses import dataclass, field
from collections.abc import Mapping
from datetime import datetime
from typing import Any, Callable


@dataclass(frozen=True)
class ManagerSpec:
    """Describe manager reconstruction metadata without importing a manager."""

    class_path: str | None = None
    config: object | None = None
    completion_style: str = "legacy"


@dataclass(frozen=True)
class TaskCall:
    """Describe a direct callable submission and its separate q2 options."""

    func: Callable[..., Any] | str
    args: tuple[Any, ...]
    kwargs: dict[str, Any]
    task_key: str
    conflict_ids: object | None = None
    user: object | None = None
    affected_objects: object | None = None
    manager: ManagerSpec | None = None
    coordination: dict[str, Any] = field(default_factory=dict)
    execution_options: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExecutionRef:
    """Identify q2 execution independently from the logical PowerCRUD key."""

    backend: str = "q2"
    id: str | None = None
    locator: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TaskIdentity:
    """Retain the selected manager, coordination location, and q2 route."""

    task_key: str
    manager: ManagerSpec
    coordination: dict[str, Any]
    execution: ExecutionRef
    version: int = 1

    def to_mapping(self) -> dict[str, Any]:
        """Return the versioned mapping stored in the selected cache."""
        return {
            "version": self.version,
            "task_key": self.task_key,
            "manager": {
                "class_path": self.manager.class_path,
                "config": self.manager.config,
                "completion_style": self.manager.completion_style,
            },
            "coordination": dict(self.coordination),
            "execution": {
                "backend": self.execution.backend,
                "id": self.execution.id,
                "locator": dict(self.execution.locator),
            },
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "TaskIdentity":
        """Validate and reconstruct a stored version-1 identity mapping."""
        if (
            not isinstance(value, Mapping)
            or type(value.get("version")) is not int
            or value.get("version") != 1
        ):
            raise ValueError("Unsupported or malformed task identity version")
        manager = value.get("manager")
        execution = value.get("execution")
        coordination = value.get("coordination")
        task_key = value.get("task_key")
        if not isinstance(manager, Mapping) or not isinstance(execution, Mapping):
            raise ValueError("Task identity requires manager and execution mappings")
        if not isinstance(coordination, Mapping) or not isinstance(task_key, str) or not task_key:
            raise ValueError("Task identity requires a task key and coordination mapping")
        try:
            from .config import CoordinatorConfig

            coordination_config = CoordinatorConfig.from_snapshot(coordination)
        except Exception as exc:
            raise ValueError("Task identity coordination snapshot is invalid") from exc
        if (
            not isinstance(coordination_config.cache_name, str)
            or not coordination_config.cache_name.strip()
            or not isinstance(coordination_config.key_namespace, str)
            or not coordination_config.key_namespace.strip()
        ):
            raise ValueError("Task identity coordination location is invalid")
        class_path = manager.get("class_path")
        completion_style = manager.get("completion_style")
        execution_id = execution.get("id")
        locator = execution.get("locator")
        if (
            not isinstance(class_path, str)
            or not class_path
            or not isinstance(completion_style, str)
            or completion_style not in {"core", "legacy"}
        ):
            raise ValueError("Task identity manager metadata is invalid")
        if execution.get("backend") != "q2" or not isinstance(execution_id, str) or not execution_id:
            raise ValueError("Task identity execution reference is invalid")
        if not isinstance(locator, Mapping):
            raise ValueError("Task identity execution locator must be a mapping")
        identity = cls(
            task_key=task_key,
            manager=ManagerSpec(class_path, manager.get("config"), completion_style),
            coordination=dict(coordination),
            execution=ExecutionRef("q2", execution_id, dict(locator)),
        )
        if type(value.get("version")) is not int:
            raise ValueError("Task identity version must be an integer")
        return identity


@dataclass(frozen=True)
class Completion:
    """Normalized execution evidence with no q2 model dependency."""

    task_key: str
    execution: ExecutionRef | None = None
    success: bool | None = None
    result: object = None
    started_at: datetime | None = None
    finished_at: datetime | None = None


@dataclass(frozen=True)
class ResultLookup:
    """Represent a successful result lookup, absence, or lookup failure."""

    kind: str
    completion: Completion | None = None
    reason: str | None = None

