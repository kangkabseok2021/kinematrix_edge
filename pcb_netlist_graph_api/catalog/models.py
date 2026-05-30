from __future__ import annotations

from typing import Any

from django.contrib.postgres.indexes import GinIndex
from django.db import models


class Component(models.Model):
    mfr_pn: models.CharField[str, str] = models.CharField(max_length=128, unique=True)
    lcsc_code: models.CharField[str, str] = models.CharField(max_length=32, blank=True, default="")
    category: models.CharField[str, str] = models.CharField(max_length=64, db_index=True)
    parameters: models.JSONField[dict[str, Any], dict[str, Any]] = models.JSONField(default=dict)
    parent: models.ForeignKey[Component | None, Component | None] = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="children"
    )

    class Meta:
        indexes = [
            models.Index(fields=["category", "mfr_pn"]),
            GinIndex(fields=["parameters"], name="component_parameters_gin"),
        ]

    def __str__(self) -> str:
        return f"{self.mfr_pn} ({self.category})"


class Footprint(models.Model):
    ipc_code: models.CharField[str, str] = models.CharField(max_length=64, unique=True)
    pad_count: models.PositiveIntegerField[int, int] = models.PositiveIntegerField()
    pitch_mm: models.DecimalField[Any, Any] = models.DecimalField(max_digits=6, decimal_places=3)

    def __str__(self) -> str:
        return self.ipc_code


class NetlistEdge(models.Model):
    net_name: models.CharField[str, str] = models.CharField(max_length=128, db_index=True)
    component: models.ForeignKey[Component, Component] = models.ForeignKey(
        Component, on_delete=models.CASCADE, related_name="netlist_edges"
    )
    pin_name: models.CharField[str, str] = models.CharField(max_length=32)

    class Meta:
        unique_together = [("net_name", "component", "pin_name")]

    def __str__(self) -> str:
        return f"{self.net_name}:{self.component_id}:{self.pin_name}"
