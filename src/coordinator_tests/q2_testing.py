"""q2 boundary fixtures for adapter mocks that must emit real signals."""


def q2_submission(execution_id="coordinator-test-execution", *, execute=False):
    """Return a patched enqueue function that emits registered q2 task signals."""
    def submit(func, *args, **kwargs):
        """Prepare task metadata and optionally run the original callable inline."""
        from django.utils import timezone
        from django_q.signals import post_execute_in_worker, pre_enqueue, pre_execute
        from powercrud._coordinator.q2 import _submission_binding

        binding = _submission_binding.get()
        if binding is None:
            return execution_id
        call = binding.call
        task = {
            "id": execution_id,
            "name": call.task_key,
            "args": call.args,
            "kwargs": dict(call.kwargs),
            "cached": binding.prepared.get("cached", False),
            "cluster": binding.prepared.get("cluster"),
        }
        pre_enqueue.send(sender=None, task=task)
        if execute:
            pre_execute.send(sender=None, task=task, func=call.func)
            result = call.func(*call.args, **call.kwargs)
            task.update({"result": result, "success": True, "stopped": timezone.now()})
            post_execute_in_worker.send(sender=None, task=task, func=call.func)
        return execution_id

    return submit
