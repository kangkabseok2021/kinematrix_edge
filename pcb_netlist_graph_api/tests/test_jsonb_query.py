from __future__ import annotations

import pytest
from strawberry.test import Client

from tests.factories import CapacitorFactory, ComponentFactory


@pytest.mark.django_db
def test_filter_by_capacitance_gte(gql_client: Client) -> None:
    CapacitorFactory.create(parameters={"capacitance_nf": 100, "voltage_v": 16})
    CapacitorFactory.create(parameters={"capacitance_nf": 10, "voltage_v": 16})
    result = gql_client.execute(
        '{ components(category: "capacitor", paramFilter: "{\\"capacitance_nf\\": 90}") { mfrPn parameters } }'
    )
    assert result.errors is None
    items = result.data["components"]
    assert len(items) == 1
    assert items[0]["parameters"]["capacitance_nf"] == 100


@pytest.mark.django_db
def test_filter_by_voltage_gte(gql_client: Client) -> None:
    CapacitorFactory.create(parameters={"capacitance_nf": 100, "voltage_v": 16})
    CapacitorFactory.create(parameters={"capacitance_nf": 100, "voltage_v": 6})
    result = gql_client.execute(
        '{ components(category: "capacitor", paramFilter: "{\\"voltage_v\\": 10}") { mfrPn parameters } }'
    )
    assert result.errors is None
    items = result.data["components"]
    assert len(items) == 1
    assert items[0]["parameters"]["voltage_v"] == 16


@pytest.mark.django_db
def test_filter_combined_capacitance_and_voltage(gql_client: Client) -> None:
    CapacitorFactory.create(parameters={"capacitance_nf": 100, "voltage_v": 16})
    CapacitorFactory.create(parameters={"capacitance_nf": 100, "voltage_v": 6})
    CapacitorFactory.create(parameters={"capacitance_nf": 10, "voltage_v": 16})
    result = gql_client.execute(
        '{ components(category: "capacitor", paramFilter: "{\\"capacitance_nf\\": 90, \\"voltage_v\\": 10}") { parameters } }'
    )
    assert result.errors is None
    items = result.data["components"]
    assert len(items) == 1
    assert items[0]["parameters"]["capacitance_nf"] == 100
    assert items[0]["parameters"]["voltage_v"] == 16


@pytest.mark.django_db
def test_filter_no_match_returns_empty(gql_client: Client) -> None:
    CapacitorFactory.create(parameters={"capacitance_nf": 10, "voltage_v": 6})
    result = gql_client.execute(
        '{ components(category: "capacitor", paramFilter: "{\\"capacitance_nf\\": 9999}") { mfrPn } }'
    )
    assert result.errors is None
    assert result.data["components"] == []
