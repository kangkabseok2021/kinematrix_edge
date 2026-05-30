from __future__ import annotations

import pytest
from strawberry.test import Client

from catalog.models import NetlistEdge
from tests.factories import ComponentFactory, NetlistEdgeFactory


@pytest.mark.django_db
def test_netlist_graph_returns_pins_on_net(gql_client: Client) -> None:
    comp = ComponentFactory.create()
    NetlistEdgeFactory.create(net_name="VCC", component=comp, pin_name="1")
    result = gql_client.execute('{ netlistGraph(netName: "VCC") { netName edges { componentId pinName } } }')
    assert result.errors is None
    graph = result.data["netlistGraph"]
    assert graph["netName"] == "VCC"
    assert len(graph["edges"]) == 1
    assert graph["edges"][0]["pinName"] == "1"


@pytest.mark.django_db
def test_netlist_graph_multiple_components_on_net(gql_client: Client) -> None:
    c1 = ComponentFactory.create()
    c2 = ComponentFactory.create()
    NetlistEdgeFactory.create(net_name="GND", component=c1, pin_name="2")
    NetlistEdgeFactory.create(net_name="GND", component=c2, pin_name="4")
    result = gql_client.execute('{ netlistGraph(netName: "GND") { edges { componentId pinName } } }')
    assert result.errors is None
    assert len(result.data["netlistGraph"]["edges"]) == 2


@pytest.mark.django_db
def test_netlist_graph_empty_for_unknown_net(gql_client: Client) -> None:
    result = gql_client.execute('{ netlistGraph(netName: "NONEXISTENT") { netName edges { pinName } } }')
    assert result.errors is None
    assert result.data["netlistGraph"]["edges"] == []


@pytest.mark.django_db
def test_create_netlist_edge_mutation(gql_client: Client) -> None:
    comp = ComponentFactory.create()
    result = gql_client.execute(
        f"""
        mutation {{
            createNetlistEdge(netName: "PWR", componentId: {comp.id}, pinName: "VCC") {{
                ... on ComponentSuccess {{ component {{ id mfrPn }} }}
                ... on Error {{ message }}
            }}
        }}
        """
    )
    assert result.errors is None
    assert result.data["createNetlistEdge"]["component"]["id"] == comp.id
    assert NetlistEdge.objects.filter(net_name="PWR", component=comp, pin_name="VCC").exists()
