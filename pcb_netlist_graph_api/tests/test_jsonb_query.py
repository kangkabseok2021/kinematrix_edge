from __future__ import annotations

import pytest
from strawberry.test import TestClient

from tests.factories import CapacitorFactory


@pytest.mark.django_db
def test_filter_by_capacitance_gte(gql_client: TestClient) -> None:
    CapacitorFactory.create(parameters={"capacitance_nf": 100, "voltage_v": 16})
    CapacitorFactory.create(parameters={"capacitance_nf": 10, "voltage_v": 16})
    pf = '{\\"capacitance_nf\\": 90}'
    query = f'{{ components(category: "capacitor", paramFilter: "{pf}") {{ parameters }} }}'
    result = gql_client.execute(query)
    assert result.errors is None
    items = result.data["components"]
    assert len(items) == 1
    assert items[0]["parameters"]["capacitance_nf"] == 100


@pytest.mark.django_db
def test_filter_by_voltage_gte(gql_client: TestClient) -> None:
    CapacitorFactory.create(parameters={"capacitance_nf": 100, "voltage_v": 16})
    CapacitorFactory.create(parameters={"capacitance_nf": 100, "voltage_v": 6})
    pf = '{\\"voltage_v\\": 10}'
    query = f'{{ components(category: "capacitor", paramFilter: "{pf}") {{ parameters }} }}'
    result = gql_client.execute(query)
    assert result.errors is None
    items = result.data["components"]
    assert len(items) == 1
    assert items[0]["parameters"]["voltage_v"] == 16


@pytest.mark.django_db
def test_filter_combined_capacitance_and_voltage(gql_client: TestClient) -> None:
    CapacitorFactory.create(parameters={"capacitance_nf": 100, "voltage_v": 16})
    CapacitorFactory.create(parameters={"capacitance_nf": 100, "voltage_v": 6})
    CapacitorFactory.create(parameters={"capacitance_nf": 10, "voltage_v": 16})
    pf = '{\\"capacitance_nf\\": 90, \\"voltage_v\\": 10}'
    result = gql_client.execute(
        f'{{ components(category: "capacitor", paramFilter: "{pf}") {{ parameters }} }}'
    )
    assert result.errors is None
    items = result.data["components"]
    assert len(items) == 1
    assert items[0]["parameters"]["capacitance_nf"] == 100
    assert items[0]["parameters"]["voltage_v"] == 16


@pytest.mark.django_db
def test_filter_no_match_returns_empty(gql_client: TestClient) -> None:
    CapacitorFactory.create(parameters={"capacitance_nf": 10, "voltage_v": 6})
    pf = '{\\"capacitance_nf\\": 9999}'
    query = f'{{ components(category: "capacitor", paramFilter: "{pf}") {{ mfrPn }} }}'
    result = gql_client.execute(query)
    assert result.errors is None
    assert result.data["components"] == []
