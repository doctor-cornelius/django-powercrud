"""Exercise launch ordering across an isolated q2 ORM queue and worker process."""

import os
import subprocess
import sys
import uuid

from django.conf import settings
from django.test import TransactionTestCase

from coordinator_tests.managers import CoordinatorAsyncManager


class TestLaunchDelivery(TransactionTestCase):
    """Use the real ORM broker and run q2 worker and monitor in a child process."""

    def test_worker_finishes_before_broker_enqueue_returns(self):
        """Completion and cleanup must hold when the launcher receives its ID late."""
        from django_q.brokers.orm import ORM

        manager = CoordinatorAsyncManager()
        task_key = f"fast-worker-{uuid.uuid4()}"
        before_return = []
        child_code = (
            "import sys; import django; django.setup(); "
            "from django_q.tasks import _sync; _sync(sys.stdin.read())"
        )

        class FastWorkerBroker(ORM):
            """Pause q2's enqueue return until a worker processes the signed package."""

            def enqueue(self, package):
                """Round-trip through the ORM queue and hand the payload to a child."""
                receipt = super().enqueue(package)
                if not manager.is_active_task(task_key):
                    raise AssertionError("Active membership must exist before the broker delivers")
                deliveries = self.dequeue()
                if len(deliveries) != 1 or deliveries[0][0] != receipt:
                    raise AssertionError("The isolated queue should deliver its one submitted task")
                subprocess.run(
                    [sys.executable, "-c", child_code],
                    input=deliveries[0][1],
                    text=True,
                    env={**os.environ, "POWERCRUD_COORDINATOR_CACHE_DIR": settings.TEST_CACHE_DIR},
                    check=True,
                    timeout=15,
                    capture_output=True,
                )
                self.acknowledge(receipt)
                before_return.append(manager.get_task_observation(task_key))
                return receipt

        broker = FastWorkerBroker()
        broker.list_key = task_key
        try:
            returned = manager.launch(
                "coordinator_tests.workers.signal_context_worker",
                "delivered",
                task_key=task_key,
                execution_options={"broker": broker, "sync": False, "cached": 60},
            )
            self.assertEqual(returned, task_key, "The logical key remains the return value")
            self.assertEqual(len(before_return), 1, "The broker must finish one delivery before returning")
            self.assertEqual(before_return[0]["status"], "success", "Worker completion must precede the enqueue return")
            self.assertEqual(
                manager.get_task_observation(task_key), before_return[0],
                "Late launch return must preserve the terminal observation and timestamps",
            )
            self.assertFalse(manager.is_active_task(task_key), "Launch return must not undo worker cleanup")
            self.assertIsNone(manager.get_progress(task_key), "Launch return must not recreate pending progress")
        finally:
            broker.purge_queue()
