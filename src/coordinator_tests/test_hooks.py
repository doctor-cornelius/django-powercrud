from __future__ import annotations

import json
from types import SimpleNamespace


from powercrud._coordinator.q2 import Q2Adapter


class DummyTask(SimpleNamespace):
    pass


def test_parse_task_kwargs_handles_json():
    task = DummyTask(kwargs=json.dumps({"foo": "bar"}))
    assert Q2Adapter().parse_task_kwargs(task) == {"foo": "bar"}, "JSON task kwargs should be parsed"

    task.kwargs = "{'foo': 'bar'}"
    assert Q2Adapter().parse_task_kwargs(task)["foo"] == "bar", "Python-dict task kwargs should remain supported"

    task.kwargs = object()
    assert Q2Adapter().parse_task_kwargs(task) == {}, "Unusable task kwargs should produce an empty mapping"


def test_extract_manager_helpers():
    task = DummyTask(
        kwargs={"manager_class": "module.Manager", "manager_config": {"foo": "bar"}}
    )
    path, config = Q2Adapter().extract_manager_metadata(task)
    assert path == "module.Manager", "Manager class path should be extracted"
    assert config == {"foo": "bar"}, "Manager configuration should be extracted"

    task.kwargs = {"manager_config": "not-a-dict"}
    _path, config = Q2Adapter().extract_manager_metadata(task)
    assert config is None, "Non-dict manager config should be ignored"
