from __future__ import annotations

import json

import pytest
from django.test import override_settings
from strawberry.test import Client

from tests.factories import CapacitorFactory

LOCMEM_CACHE = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}


@pytest.mark.django_db
@override_settings(CACHES=LOCMEM_CACHE)
def test_cache_miss_then_hit(gql_client: Client) -> None:
    from django.core.cache import cache

    cache.clear()
    CapacitorFactory.create(parameters={"capacitance_nf": 100, "voltage_v": 16})
    query = '{ components(category: "capacitor") { mfrPn } }'
    result1 = gql_client.execute(query)
    result2 = gql_client.execute(query)
    assert result1.errors is None
    assert result2.errors is None
    assert result1.data == result2.data


@pytest.mark.django_db
@override_settings(CACHES=LOCMEM_CACHE)
def test_cache_invalidated_on_component_save(gql_client: Client) -> None:
    from django.core.cache import cache

    cache.clear()
    comp = CapacitorFactory.create(mfr_pn="CAP-CACHE-001", parameters={"capacitance_nf": 10, "voltage_v": 6})
    result1 = gql_client.execute('{ components(category: "capacitor") { mfrPn } }')
    assert len(result1.data["components"]) == 1
    CapacitorFactory.create(mfr_pn="CAP-CACHE-002", parameters={"capacitance_nf": 100, "voltage_v": 16})
    result2 = gql_client.execute('{ components(category: "capacitor") { mfrPn } }')
    assert len(result2.data["components"]) == 2
