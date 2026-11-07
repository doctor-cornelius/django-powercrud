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
        manager = manager_factory()
        try:
            status = manager.get_task_status_cache_only(task_name)
            is_complete = manager.is_task_complete_cache_only(task_name)
            raw_progress = manager.get_progress(task_name)
            progress_data = None if raw_progress == manager.STATUSES.PENDING else raw_progress
            if is_complete:
                display_status = (
                    manager.STATUSES.SUCCESS
                    if status == "completed"
                    else (status or manager.STATUSES.SUCCESS)
                )
                return JsonResponse(
                    {
                        "task_name": task_name,
                        "status": display_status,
                        "progress": progress_data or "Completed successfully!",
                        "message": "Task completed",
                    },
                    status=286,
                )
            if progress_data is not None:
                return JsonResponse(
                    {"task_name": task_name, "status": status, "progress": progress_data}
                )
            status = manager.get_task_status_nowait(task_name)
            return JsonResponse(
                {
                    "task_name": task_name,
                    "status": status or "unknown",
                    "progress": None,
                    "poll_interval": 1000,
                }
            )
        except Exception as exc:
            log.error("Error in progress view for task %s: %s", task_name, exc)
            return JsonResponse({"error": str(exc)}, status=500)

    return view
