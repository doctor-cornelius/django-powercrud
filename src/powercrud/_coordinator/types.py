"""Plain data exchanged between coordination code and the q2 adapter."""

from dataclasses import dataclass, field
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

