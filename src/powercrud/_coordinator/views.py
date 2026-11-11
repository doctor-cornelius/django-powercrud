"""Reusable progress polling endpoint, bound by its host application."""

import logging

from django.http import JsonResponse

log = logging.getLogger(__name__)


def progress_view(*, manager_factory, template_name=None):
    """Build the existing progress response flow around an application factory."""
    def view(request):
        task_name = request.GET.get("task_name") or request.POST.get("task_name")
        if not task_name:
            return JsonResponse({"error": "task_name required"}, status=400)
        try:
            manager = manager_factory()
            observation = manager.get_task_observation(task_name, cache_only=True)
            try:
                unknown_elapsed = int(request.GET.get("unknown_elapsed_ms", "0"))
            except (TypeError, ValueError):
                unknown_elapsed = 0
            unknown_elapsed = max(0, min(unknown_elapsed, 30_000))
            unknown_exhausted = observation["status"] == manager.STATUSES.UNKNOWN and unknown_elapsed >= 30_000
            response = {
                "task_name": task_name,
                "status": observation["status"],
                "terminal": observation["terminal"],
                "reason": observation["reason"],
                "progress": observation["progress"],
                "message": observation["message"],
                "execution_outcome": observation["execution_outcome"],
                "business_outcome": observation["business_outcome"],
                "outcome": observation["details"],
                "finished_at": observation["finished_at"],
                "expires_at": observation["expires_at"],
                "poll_interval": 1000,
                "polling_stopped": unknown_exhausted,
            }
            if unknown_exhausted:
                response["display_message"] = "Status currently unavailable"
                return JsonResponse(response, status=286)
            if observation["terminal"]:
                return JsonResponse(response, status=286)
            return JsonResponse(response)
        except Exception as exc:
            log.error("Error in progress view for task %s: %s", task_name, exc)
            return JsonResponse({"error": str(exc)}, status=500)

    return view
