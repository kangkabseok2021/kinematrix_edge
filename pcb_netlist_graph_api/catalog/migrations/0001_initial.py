from __future__ import annotations

import django.contrib.postgres.indexes
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Component",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("mfr_pn", models.CharField(max_length=128, unique=True)),
                ("lcsc_code", models.CharField(blank=True, default="", max_length=32)),
                ("category", models.CharField(db_index=True, max_length=64)),
                ("parameters", models.JSONField(default=dict)),
                (
                    "parent",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="children",
                        to="catalog.component",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Footprint",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("ipc_code", models.CharField(max_length=64, unique=True)),
                ("pad_count", models.PositiveIntegerField()),
                ("pitch_mm", models.DecimalField(decimal_places=3, max_digits=6)),
            ],
        ),
        migrations.CreateModel(
            name="NetlistEdge",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("net_name", models.CharField(db_index=True, max_length=128)),
                (
                    "component",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="netlist_edges",
                        to="catalog.component",
                    ),
                ),
                ("pin_name", models.CharField(max_length=32)),
            ],
            options={
                "unique_together": {("net_name", "component", "pin_name")},
            },
        ),
        migrations.AddIndex(
            model_name="component",
            index=models.Index(fields=["category", "mfr_pn"], name="catalog_com_categor_idx"),
        ),
        migrations.AddIndex(
            model_name="component",
            index=django.contrib.postgres.indexes.GinIndex(
                fields=["parameters"], name="component_parameters_gin"
            ),
        ),
    ]
