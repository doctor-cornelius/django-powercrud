"""Versioned task identity retention in the selected coordination cache."""

from datetime import datetime, timedelta, timezone
from typing import Any

from django.core.cache import caches

from .config import CoordinatorConfig
from .types import ExecutionRef, ManagerSpec, TaskIdentity


def identity_key(config: CoordinatorConfig, task_key: str) -> str:
    """Return the bound cache key for one logical task identity."""
    return f"{config.key_namespace}:async:task:{task_key}"


def finished_key(config: CoordinatorConfig, task_key: str, execution_id: str) -> str:
    """Return the immutable retention marker key for one execution."""
    return f"{identity_key(config, task_key)}:finished:{execution_id}"


def put_identity(config: CoordinatorConfig, identity: TaskIdentity) -> TaskIdentity:
    """Create a task identity once and reject conflicting retained values."""
    mapping = identity.to_mapping()
    TaskIdentity.from_mapping(mapping)
    embedded_config = CoordinatorConfig.from_snapshot(identity.coordination)
    if (embedded_config.cache_name, embedded_config.key_namespace) != (
        config.cache_name,
        config.key_namespace,
    ):
        raise ValueError("Task identity cannot redirect its configured cache or namespace")
    cache = caches[config.cache_name]
    key = identity_key(config, identity.task_key)
    created = cache.add(key, mapping, timeout=None)
    existing = cache.get(key)
    if existing is None:
        raise RuntimeError(f"Task identity could not be retained at {key!r}")
    stored = TaskIdentity.from_mapping(existing)
    if stored != identity:
        if created:
            raise RuntimeError(f"Task identity verification failed for {identity.task_key!r}")
        raise RuntimeError(f"A conflicting task identity already exists for {identity.task_key!r}")
    return stored


def get_identity(config: CoordinatorConfig, task_key: str) -> TaskIdentity | None:
    """Read identity only from its configured cache and namespace."""
    value = caches[config.cache_name].get(identity_key(config, task_key))
    if value is None:
        return None
    identity = TaskIdentity.from_mapping(value)
    if identity.task_key != task_key:
        raise ValueError("Stored task identity key does not match the requested task")
    stored_config = CoordinatorConfig.from_snapshot(identity.coordination)
    if (stored_config.cache_name, stored_config.key_namespace) != (
        config.cache_name,
        config.key_namespace,
    ):
        raise ValueError("Stored task identity cannot redirect its cache or namespace")
    marker = caches[config.cache_name].get(
        finished_key(config, task_key, identity.execution.id)
    )
    if marker is not None:
        if not isinstance(marker, dict) or marker.get("version") != 1:
            raise ValueError("Stored task retention marker is malformed")
        expires_at = marker.get("expires_at")
        if not isinstance(expires_at, datetime) or expires_at.tzinfo is None:
            raise ValueError("Stored task retention marker expiry is invalid")
        if expires_at <= datetime.now(timezone.utc):
            return None
    return identity


def is_finished(config: CoordinatorConfig, identity: TaskIdentity) -> bool:
    """Return whether this execution has immutable, unexpired finish evidence."""
    marker = caches[config.cache_name].get(
        finished_key(config, identity.task_key, identity.execution.id)
    )
    if marker is None:
        return False
    if not isinstance(marker, dict) or marker.get("version") != 1:
        raise ValueError("Stored task retention marker is malformed")
    expires_at = marker.get("expires_at")
    if not isinstance(expires_at, datetime) or expires_at.tzinfo is None:
        raise ValueError("Stored task retention marker expiry is invalid")
    return expires_at > datetime.now(timezone.utc)


def attach_execution(
    *,
    task_key: str,
    manager: ManagerSpec,
    coordination: dict[str, Any],
    execution: ExecutionRef,
) -> TaskIdentity:
    """Build the complete identity after q2 assigns its execution reference."""
    if not execution.id:
        raise ValueError("Cannot attach a missing q2 execution identifier")
    return TaskIdentity(task_key, manager, dict(coordination), execution)


def mark_finished(
    config: CoordinatorConfig,
    identity: TaskIdentity,
    *,
    finished_at: datetime,
) -> bool:
    """Create immutable terminal retention evidence without refreshing it."""
    if (
        isinstance(config.terminal_result_ttl, bool)
        or not isinstance(config.terminal_result_ttl, int)
        or config.terminal_result_ttl <= 0
    ):
        raise ValueError("terminal_result_ttl must be a positive integer")
    if finished_at.tzinfo is None:
        finished_at = finished_at.replace(tzinfo=timezone.utc)
    marker = {
        "version": 1,
        "finished_at": finished_at,
        "expires_at": finished_at + timedelta(seconds=config.terminal_result_ttl),
    }
    return caches[config.cache_name].add(
        finished_key(config, identity.task_key, identity.execution.id),
        marker,
        timeout=None,
    )
