from __future__ import annotations

from typing import Any

import pytest

from catalog.models import Component
from tests.factories import ComponentFactory


@pytest.mark.django_db
def test_add_component_mutation(execute: Any) -> None:
    result = execute(
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
def test_list_components_returns_all(execute: Any) -> None:
    ComponentFactory.create_batch(3)
    result = execute("{ components { id mfrPn } }")
    assert result.errors is None
    assert len(result.data["components"]) == 3


@pytest.mark.django_db
def test_list_components_filtered_by_category(execute: Any) -> None:
    ComponentFactory.create(category="resistor")
    ComponentFactory.create(category="capacitor")
    result = execute('{ components(category: "resistor") { mfrPn category } }')
    assert result.errors is None
    items = result.data["components"]
    assert len(items) == 1
    assert items[0]["category"] == "resistor"


@pytest.mark.django_db
def test_add_component_duplicate_mfr_pn_returns_error(execute: Any) -> None:
    ComponentFactory.create(mfr_pn="DUPE-001")
    result = execute(
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
def test_component_parameters_round_trip(execute: Any) -> None:
    params = {"resistance_ohm": 470, "power_w": 0.25, "tolerance_pct": 5}
    ComponentFactory.create(mfr_pn="RT-001", parameters=params)
    result = execute("{ components { mfrPn parameters } }")
    assert result.errors is None
    stored = result.data["components"][0]["parameters"]
    assert stored["resistance_ohm"] == 470
    assert stored["tolerance_pct"] == 5
