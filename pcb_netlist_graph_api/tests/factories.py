from __future__ import annotations

import factory

from catalog.models import Component, Footprint, NetlistEdge


class ComponentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Component

    mfr_pn = factory.Sequence(lambda n: f"MPN-{n:04d}")
    lcsc_code = factory.Sequence(lambda n: f"C{n:06d}")
    category = "resistor"
    parameters: dict = factory.LazyAttribute(
        lambda _: {"resistance_ohm": 1000, "power_w": 0.1, "tolerance_pct": 1}
    )


class CapacitorFactory(ComponentFactory):
    category = "capacitor"
    parameters: dict = factory.LazyAttribute(
        lambda _: {"capacitance_nf": 100, "voltage_v": 16, "dielectric": "X5R"}
    )


class FootprintFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Footprint

    ipc_code = factory.Sequence(lambda n: f"IPC-{n:04d}")
    pad_count = 2
    pitch_mm = factory.LazyAttribute(lambda _: 0.5)


class NetlistEdgeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = NetlistEdge

    net_name = "VCC"
    component = factory.SubFactory(ComponentFactory)
    pin_name = "1"
