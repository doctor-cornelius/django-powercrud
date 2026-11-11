"""Versioned task identity retention in the selected coordination cache."""

from datetime import datetime, timedelta, timezone
import logging
from typing import Any

from django.core.cache import caches

from .config import CoordinatorConfig
from .types import (
    BusinessOutcome,
    Completion,
    ExecutionRef,
    ManagerSpec,
    TaskIdentity,
    bounded_business_payload,
)

log = logging.getLogger(__name__)


def identity_key(config: CoordinatorConfig, task_key: str) -> str:
    """Return the bound cache key for one logical task identity."""
    return f"{config.key_namespace}:async:task:{task_key}"


def finished_key(config: CoordinatorConfig, task_key: str, execution_id: str) -> str:
    """Return the immutable terminal/legacy retention key for one execution."""
    return f"{identity_key(config, task_key)}:finished:{execution_id}"


def unresolved_key(config: CoordinatorConfig, task_key: str, execution_id: str) -> str:
    """Return the immutable insufficient-finality evidence key for one execution."""
    return f"{identity_key(config, task_key)}:unresolved:{execution_id}"


def dispatch_key(config: CoordinatorConfig, task_key: str, execution_id: str) -> str:
    """Return the immutable callback-attempt claim key for one execution."""
    return f"{identity_key(config, task_key)}:dispatch:{execution_id}"


def claim_completion_dispatch(
    config: CoordinatorConfig, identity: TaskIdentity, *, claimed_at: datetime
) -> bool:
    """Claim one optional completion callback after terminal evidence exists."""
    retained = get_terminal_record(config, identity)
    if retained is None:
        return False
    cache = caches[config.cache_name]
    key = dispatch_key(config, identity.task_key, identity.execution.id)
    claim = {
        "version": 1,
        "task_key": identity.task_key,
        "execution_id": identity.execution.id,
        "claimed_at": _aware(claimed_at),
    }
    created = cache.add(key, claim, timeout=None)
    stored = cache.get(key)
    if not isinstance(stored, dict) or stored.get("task_key") != identity.task_key or stored.get("execution_id") != identity.execution.id:
        raise RuntimeError("Completion dispatch claim could not be verified")
    return bool(created)


def _aware(value: datetime) -> datetime:
    """Normalize a naive q2 timestamp to UTC without changing aware values."""
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def _read_retention(config: CoordinatorConfig, task_key: str, execution_id: str):
    """Read and validate either legacy retention-only or terminal state."""
    marker = caches[config.cache_name].get(finished_key(config, task_key, execution_id))
    if marker is None:
        return None
    if not isinstance(marker, dict) or marker.get("version") not in {1, 2}:
        raise ValueError("Stored task terminal record is malformed")
    expires_at = marker.get("expires_at")
    if not isinstance(expires_at, datetime) or expires_at.tzinfo is None:
        raise ValueError("Stored task terminal record expiry is invalid")
    return marker


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
    marker = _read_retention(config, task_key, identity.execution.id)
    if marker is not None:
        expires_at = marker.get("expires_at")
        if expires_at <= datetime.now(timezone.utc):
            return None
    return identity


def is_finished(config: CoordinatorConfig, identity: TaskIdentity) -> bool:
    """Return whether this execution has immutable, unexpired terminal retention."""
    marker = _read_retention(config, identity.task_key, identity.execution.id)
    return marker is not None and marker["expires_at"] > datetime.now(timezone.utc)


def get_terminal_record(config: CoordinatorConfig, identity: TaskIdentity) -> dict[str, Any] | None:
    """Return only a valid, matching version-2 terminal snapshot."""
    marker = _read_retention(config, identity.task_key, identity.execution.id)
    if marker is None or marker.get("version") != 2:
        return None
    if marker.get("task_key") != identity.task_key or marker.get("execution_id") != identity.execution.id:
        raise ValueError("Stored task terminal record does not match retained identity")
    if marker["expires_at"] <= datetime.now(timezone.utc):
        return None
    return marker


def get_unresolved_record(config: CoordinatorConfig, identity: TaskIdentity) -> dict[str, Any] | None:
    """Return validated insufficient-finality evidence for one execution."""
    marker = caches[config.cache_name].get(unresolved_key(config, identity.task_key, identity.execution.id))
    if marker is None:
        return None
    if (
        not isinstance(marker, dict)
        or marker.get("version") != 1
        or marker.get("task_key") != identity.task_key
        or marker.get("execution_id") != identity.execution.id
        or not isinstance(marker.get("reason"), str)
        or not isinstance(marker.get("observed_at"), datetime)
    ):
        raise ValueError("Stored unresolved execution evidence is malformed")
    return marker


def record_unresolved(
    config: CoordinatorConfig,
    identity: TaskIdentity,
    *,
    reason: str,
    observed_at: datetime,
) -> dict[str, Any]:
    """Keep the first compact observation when a failed attempt is not final."""
    retained = get_identity(config, identity.task_key)
    if retained != identity:
        raise ValueError("Cannot retain unresolved evidence without matching identity")
    marker = {
        "version": 1,
        "task_key": identity.task_key,
        "execution_id": identity.execution.id,
        "reason": reason[:512],
        "observed_at": _aware(observed_at),
    }
    key = unresolved_key(config, identity.task_key, identity.execution.id)
    cache = caches[config.cache_name]
    cache.add(key, marker, timeout=None)
    stored = cache.get(key)
    if not isinstance(stored, dict) or stored.get("task_key") != identity.task_key or stored.get("execution_id") != identity.execution.id:
        raise RuntimeError("Unresolved execution evidence could not be verified")
    return stored


def publish_terminal(
    config: CoordinatorConfig,
    identity: TaskIdentity,
    completion: Completion,
    *,
    status: str | None = None,
    observed_at: datetime | None = None,
) -> dict[str, Any] | None:
    """Publish one bounded, immutable terminal outcome for the retained execution."""
    if completion.execution and completion.execution.id != identity.execution.id:
        raise ValueError("Completion execution does not match retained identity")
    retained = get_identity(config, identity.task_key)
    if retained != identity:
        raise ValueError("Cannot publish terminal outcome without matching retained identity")
    if completion.finality is not True:
        return None
    finished_at = _aware(completion.finished_at or observed_at or datetime.now(timezone.utc))
    ttl = config.terminal_result_ttl
    if isinstance(ttl, bool) or not isinstance(ttl, int) or ttl <= 0:
        raise ValueError("terminal_result_ttl must be a positive integer")
    if isinstance(config.terminal_result_max_bytes, bool) or not isinstance(config.terminal_result_max_bytes, int) or config.terminal_result_max_bytes < 1024:
        raise ValueError("terminal_result_max_bytes must be an integer of at least 1024")
    expires_at = finished_at + timedelta(seconds=ttl)
    if expires_at <= datetime.now(timezone.utc):
        return None
    result = completion.result
    business = result if isinstance(result, BusinessOutcome) else None
    if status is None:
        if business is not None:
            status = "success" if business.status == "success" else "failed"
        elif completion.success is True:
            status = "success"
        elif completion.success is False:
            status = "failed"
        else:
            status = "unknown"
    payload, truncated, unrepresentable = bounded_business_payload(
        business, result=None if business else result,
        max_bytes=config.terminal_result_max_bytes,
    )
    record = {
        "version": 2,
        "task_key": identity.task_key,
        "execution_id": identity.execution.id,
        "execution_outcome": "success" if completion.success is True else "failed" if completion.success is False else "unknown",
        "business_outcome": business.status if business else None,
        "status": status,
        "reason": completion.finality_reason,
        "finished_at": finished_at,
        "expires_at": expires_at,
        "details": payload,
        "truncated": truncated,
        "unrepresentable": unrepresentable,
    }
    cache = caches[config.cache_name]
    key = finished_key(config, identity.task_key, identity.execution.id)
    cache.add(key, record, timeout=None)
    stored = cache.get(key)
    if not isinstance(stored, dict) or stored.get("version") not in {1, 2}:
        raise RuntimeError("Terminal outcome could not be verified")
    if stored.get("version") == 2 and (
        stored.get("task_key") != identity.task_key
        or stored.get("execution_id") != identity.execution.id
    ):
        raise RuntimeError("Stored terminal outcome does not match retained identity")
    if stored != record:
        log.warning("Conflicting terminal evidence for task %s; retaining first outcome", identity.task_key)
    return stored


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
    """Create legacy retention-only evidence without refreshing it."""
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
