"""Scoped manager construction without PowerCRUD integration imports."""

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from importlib import import_module
from typing import Any, Callable

from .config import CoordinatorConfig


@dataclass(frozen=True)
class _ConstructionBinding:
    """Values supplied by a coordinator factory to ordinary constructors."""

    config: CoordinatorConfig
    executor: object | None


_binding: ContextVar[_ConstructionBinding | None] = ContextVar(
    "powercrud_coordinator_construction", default=None
)


def current_binding() -> _ConstructionBinding | None:
    """Return the active construction scope, if any."""
    return _binding.get()


def bind_construction(
    config: CoordinatorConfig, executor: object | None = None
):
    """Bind explicit coordinator dependencies for a normal ``super()`` chain."""
    return _binding.set(_ConstructionBinding(config=config, executor=executor))


def reset_construction(token: object) -> None:
    """Restore the preceding construction scope."""
    _binding.reset(token)


@contextmanager
def construction_scope(config: CoordinatorConfig, executor: object | None = None):
    """Expose configuration to an existing application manager resolver."""
    token = bind_construction(config, executor)
    try:
        yield
    finally:
        reset_construction(token)


def import_string(class_path: str) -> type:
    """Import and return a class from a dotted path."""
    module_path, class_name = class_path.rsplit(".", 1)
    return getattr(import_module(module_path), class_name)


def construct_manager(
    spec: object,
    *,
    coordination_config: CoordinatorConfig,
    executor: object | None = None,
    legacy: bool = False,
    fallback_class_path: str | None = None,
    prepare_config: Callable[[type, Any], Any] | None = None,
) -> object:
    """Construct a configured manager under a scoped coordinator binding."""
    class_path = getattr(spec, "class_path", None) or fallback_class_path
    app_config = getattr(spec, "config", None)
    try:
        manager_cls = import_string(class_path) if class_path else None
        if manager_cls is None:
            raise ImportError("No manager class path was supplied")
        from .manager import AsyncManager

        if not isinstance(manager_cls, type) or not issubclass(manager_cls, AsyncManager):
            raise TypeError(f"{class_path} is not a coordinator AsyncManager subclass")
        prepared = app_config
        if app_config is not None:
            prepared = (
                prepare_config(manager_cls, app_config)
                if prepare_config is not None
                else manager_cls.prepare_manager_config(app_config)
            )
        token = bind_construction(coordination_config, executor)
        try:
            if prepared is not None:
                try:
                    manager = manager_cls(config=prepared)
                except TypeError:
                    if not legacy:
                        raise
                    manager = manager_cls()
            else:
                manager = manager_cls()
        finally:
            reset_construction(token)
        if app_config is not None and hasattr(manager, "_factory_manager_config"):
            manager._factory_manager_config = prepared
        return manager
    except Exception:
        if legacy and fallback_class_path and class_path != fallback_class_path:
            from .types import ManagerSpec

            return construct_manager(
                ManagerSpec(class_path=fallback_class_path),
                coordination_config=coordination_config,
                executor=executor,
                legacy=True,
                prepare_config=prepare_config,
            )
        raise
