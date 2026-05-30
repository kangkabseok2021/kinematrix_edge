from __future__ import annotations

import pytest
from strawberry.test import TestClient

from tests.factories import ComponentFactory


@pytest.mark.django_db
def test_bom_explosion_single_root(gql_client: TestClient) -> None:
    root = ComponentFactory.create(category="assembly")
    result = gql_client.execute(
        f"{{ bomExplosion(rootComponentId: {root.id}) {{ id mfrPn depth }} }}"
    )
    assert result.errors is None
    nodes = result.data["bomExplosion"]
    assert len(nodes) == 1
    assert nodes[0]["id"] == root.id
    assert nodes[0]["depth"] == 0


@pytest.mark.django_db
def test_bom_explosion_two_level_hierarchy(gql_client: TestClient) -> None:
    root = ComponentFactory.create(category="assembly")
    child1 = ComponentFactory.create(category="resistor", parent=root)
    child2 = ComponentFactory.create(category="capacitor", parent=root)
    result = gql_client.execute(
        f"{{ bomExplosion(rootComponentId: {root.id}) {{ id depth }} }}"
    )
    assert result.errors is None
    nodes = result.data["bomExplosion"]
    assert len(nodes) == 3
    depths = {n["id"]: n["depth"] for n in nodes}
    assert depths[root.id] == 0
    assert depths[child1.id] == 1
    assert depths[child2.id] == 1


@pytest.mark.django_db
def test_bom_explosion_orders_by_depth(gql_client: TestClient) -> None:
    root = ComponentFactory.create(category="assembly")
    child = ComponentFactory.create(category="sub-assembly", parent=root)
    ComponentFactory.create(category="ic", parent=child)
    result = gql_client.execute(
        f"{{ bomExplosion(rootComponentId: {root.id}) {{ id depth }} }}"
    )
    assert result.errors is None
    nodes = result.data["bomExplosion"]
    assert len(nodes) == 3
    returned_depths = [n["depth"] for n in nodes]
    assert returned_depths == sorted(returned_depths)
