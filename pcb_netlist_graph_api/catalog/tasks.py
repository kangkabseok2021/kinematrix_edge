from __future__ import annotations

from typing import Any

from celery import shared_task

from catalog.models import Component


@shared_task(bind=True)  # type: ignore[misc]
def validate_bom(self: Any, component_ids: list[int]) -> dict[str, list[int]]:
    rows = Component.objects.filter(id__in=component_ids).values("id", "mfr_pn", "lcsc_code")
    valid: list[int] = []
    conflicts: list[int] = []
    for row in rows:
        if row["lcsc_code"]:
            valid.append(int(row["id"]))
        else:
            conflicts.append(int(row["id"]))
    return {"valid": valid, "conflicts": conflicts}
