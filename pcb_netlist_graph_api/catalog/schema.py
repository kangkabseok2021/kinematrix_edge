from __future__ import annotations

import hashlib
import json
from typing import Annotated, Any, Union

import strawberry
from django.core.cache import cache
from django.db import connection

from catalog.models import Component, NetlistEdge

JSON = strawberry.scalar(
    type(None),
    name="JSON",
    description="Arbitrary JSON value",
    serialize=lambda v: v,
    parse_value=lambda v: v,
)


@strawberry.type
class ComponentType:
    id: int
    mfr_pn: str
    lcsc_code: str
    category: str
    parameters: Any


@strawberry.type
class PinType:
    component_id: int
    mfr_pn: str
    pin_name: str


@strawberry.type
class NetlistGraphType:
    net_name: str
    edges: list[PinType]


@strawberry.type
class BomNodeType:
    id: int
    mfr_pn: str
    category: str
    depth: int


@strawberry.type
class ComponentSuccess:
    component: ComponentType


@strawberry.type
class Error:
    message: str


ComponentResult = Annotated[
    Union[ComponentSuccess, Error],
    strawberry.union("ComponentResult"),
]


def _to_component_type(c: Component) -> ComponentType:
    return ComponentType(
        id=int(c.pk),
        mfr_pn=c.mfr_pn,
        lcsc_code=c.lcsc_code,
        category=c.category,
        parameters=c.parameters,
    )


@strawberry.type
class Query:
    @strawberry.field
    def components(
        self,
        info: strawberry.types.Info,  # type: ignore[type-arg]
        category: str = "",
        param_filter: str = "{}",
    ) -> list[ComponentType]:
        filters: dict[str, Any] = json.loads(param_filter)
        cache_key = "cat:" + hashlib.sha256(
            json.dumps({"category": category, "filter": sorted(filters.items())}).encode()
        ).hexdigest()
        cached: list[ComponentType] | None = cache.get(cache_key)
        if cached is not None:
            return cached
        qs = Component.objects.all()
        if category:
            qs = qs.filter(category=category)
        for key, val in filters.items():
            qs = qs.filter(**{f"parameters__{key}__gte": val})
        result = [_to_component_type(c) for c in qs]
        cache.set(cache_key, result, 30)
        return result

    @strawberry.field
    def bom_explosion(
        self, info: strawberry.types.Info, root_component_id: int  # type: ignore[type-arg]
    ) -> list[BomNodeType]:
        sql = """
            WITH RECURSIVE bom(id, depth) AS (
                SELECT id, 0 FROM catalog_component WHERE id = %s
                UNION ALL
                SELECT c.id, bom.depth + 1
                FROM catalog_component c
                JOIN bom ON c.parent_id = bom.id
            )
            SELECT b.id, c.mfr_pn, c.category, b.depth
            FROM bom b
            JOIN catalog_component c ON c.id = b.id
            ORDER BY b.depth
        """
        with connection.cursor() as cur:
            cur.execute(sql, [root_component_id])
            rows = cur.fetchall()
        return [BomNodeType(id=int(r[0]), mfr_pn=str(r[1]), category=str(r[2]), depth=int(r[3])) for r in rows]

    @strawberry.field
    def netlist_graph(
        self, info: strawberry.types.Info, net_name: str  # type: ignore[type-arg]
    ) -> NetlistGraphType:
        edges_qs = NetlistEdge.objects.filter(net_name=net_name).select_related("component")
        pins = [
            PinType(component_id=int(e.component_id), mfr_pn=e.component.mfr_pn, pin_name=e.pin_name)
            for e in edges_qs
        ]
        return NetlistGraphType(net_name=net_name, edges=pins)


@strawberry.type
class Mutation:
    @strawberry.mutation
    def add_component(
        self,
        info: strawberry.types.Info,  # type: ignore[type-arg]
        mfr_pn: str,
        lcsc_code: str,
        category: str,
        parameters: str = "{}",
    ) -> ComponentResult:
        try:
            params: dict[str, Any] = json.loads(parameters)
            c = Component.objects.create(
                mfr_pn=mfr_pn, lcsc_code=lcsc_code, category=category, parameters=params
            )
            return ComponentSuccess(component=_to_component_type(c))
        except Exception as exc:
            return Error(message=str(exc))

    @strawberry.mutation
    def create_netlist_edge(
        self,
        info: strawberry.types.Info,  # type: ignore[type-arg]
        net_name: str,
        component_id: int,
        pin_name: str,
    ) -> ComponentResult:
        try:
            comp = Component.objects.get(id=component_id)
            NetlistEdge.objects.create(net_name=net_name, component=comp, pin_name=pin_name)
            return ComponentSuccess(component=_to_component_type(comp))
        except Component.DoesNotExist:
            return Error(message=f"Component {component_id} not found")
        except Exception as exc:
            return Error(message=str(exc))


schema = strawberry.Schema(query=Query, mutation=Mutation)
