"""Helpers for building safe PowerCRUD navigation query strings."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any
from urllib.parse import urlencode

from django.http import QueryDict

NON_NAVIGATION_QUERY_PARAM_NAMES = frozenset({"csrfmiddlewaretoken"})


def _iter_query_values(query_data: Any) -> Iterable[tuple[str, list[Any]]]:
    """Yield query names and value lists from QueryDict-like or dict-like data."""
    if not query_data:
        return
    if hasattr(query_data, "lists"):
        yield from query_data.lists()
        return
    if hasattr(query_data, "items"):
        for key, value in query_data.items():
            if isinstance(value, (list, tuple)):
                yield key, list(value)
            else:
                yield key, [value]


def build_navigation_querydict(
    query_data: Any,
    *,
    exclude: Iterable[str] = (),
    drop_blank: bool = True,
) -> QueryDict:
    """Return a QueryDict safe to reflect into list/navigation URLs."""
    ignored_names = NON_NAVIGATION_QUERY_PARAM_NAMES | frozenset(exclude)
    query = QueryDict("", mutable=True)
    for key, values in _iter_query_values(query_data):
        if key in ignored_names:
            continue
        for value in values:
            if drop_blank and not str(value).strip():
                continue
            query.appendlist(key, value)
    return query


def build_navigation_query_string(
    query_data: Any,
    *,
    exclude: Iterable[str] = (),
    drop_blank: bool = True,
) -> str:
    """Return a URL-encoded query string safe for browser navigation."""
    query = build_navigation_querydict(
        query_data,
        exclude=exclude,
        drop_blank=drop_blank,
    )
    return urlencode(list(query.lists()), doseq=True)
