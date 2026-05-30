from __future__ import annotations

import pytest
from strawberry.test import TestClient

from catalog.models import Component
from tests.factories import ComponentFactory


@pytest.mark.django_db
def test_add_component_mutation(gql_client: TestClient) -> None:
    result = gql_client.execute(
        """
        mutation {
            addComponent(
                mfrPn: "RES-001", lcscCode: "C123456",
                category: "resistor",
                parameters: "{\\"resistance_ohm\\": 1000}"
            ) {
                ... on ComponentSuccess { component { id mfrPn category } }
                ... on Error { message }
            }
        }
        """
    )
    assert result.errors is None
    data = result.data["addComponent"]
    assert data["component"]["mfrPn"] == "RES-001"
    assert data["component"]["category"] == "resistor"
    assert Component.objects.filter(mfr_pn="RES-001").exists()


@pytest.mark.django_db
def test_list_components_returns_all(gql_client: TestClient) -> None:
    ComponentFactory.create_batch(3)
    result = gql_client.execute("{ components { id mfrPn } }")
    assert result.errors is None
    assert len(result.data["components"]) == 3


@pytest.mark.django_db
def test_list_components_filtered_by_category(gql_client: TestClient) -> None:
    ComponentFactory.create(category="resistor")
    ComponentFactory.create(category="capacitor")
    result = gql_client.execute('{ components(category: "resistor") { mfrPn category } }')
    assert result.errors is None
    items = result.data["components"]
    assert len(items) == 1
    assert items[0]["category"] == "resistor"


@pytest.mark.django_db
def test_add_component_duplicate_mfr_pn_returns_error(gql_client: TestClient) -> None:
    ComponentFactory.create(mfr_pn="DUPE-001")
    result = gql_client.execute(
        """
        mutation {
            addComponent(mfrPn: "DUPE-001", lcscCode: "", category: "ic",
                         parameters: "{}") {
                ... on ComponentSuccess { component { id } }
                ... on Error { message }
            }
        }
        """
    )
    assert result.errors is None
    assert "message" in result.data["addComponent"]


@pytest.mark.django_db
def test_component_parameters_round_trip(gql_client: TestClient) -> None:
    params = {"resistance_ohm": 470, "power_w": 0.25, "tolerance_pct": 5}
    ComponentFactory.create(mfr_pn="RT-001", parameters=params)
    result = gql_client.execute("{ components { mfrPn parameters } }")
    assert result.errors is None
    stored = result.data["components"][0]["parameters"]
    assert stored["resistance_ohm"] == 470
    assert stored["tolerance_pct"] == 5
