# PCB Component Catalog & Netlist Graph API

Django 5 + Strawberry GraphQL service for managing a PCB component catalog and netlist connectivity graph — mirroring the Python/Django/PostgreSQL/GraphQL/Redis stack used in EDA tooling.

## Stack

| Layer | Technology |
|---|---|
| API | Django 5 + Strawberry GraphQL |
| Schema | `@strawberry.type` Query + Mutation with `mypy --strict` |
| ORM | Django ORM + PostgreSQL 16 JSONB |
| Caching | django-redis / SHA-256 keyed / 30 s TTL |
| Async tasks | Celery 5 + Redis broker |
| Tests | 20 pytest-django tests |
| Infra | Docker Compose (web + postgres + redis + celery) |
| CI | GitHub Actions — lint + mypy + test (with service containers) |

## Architecture

```
GraphQL POST /graphql
        │
        ▼
Strawberry Resolver (schema.py)
  components(category, param_filter)
    ├── SHA-256 cache key → django-redis GET
    ├── [miss] Django ORM JSONB __gte filter → PostgreSQL 16
    └── cache.set(key, result, 30)

  bom_explosion(root_component_id)
    └── WITH RECURSIVE CTE → multi-level assembly hierarchy

  netlist_graph(net_name)
    └── NetlistEdge.select_related("component") → adjacency list

Celery Worker (tasks.py)
  validate_bom.delay(component_ids)
    └── Component LCSC availability check → {valid, conflicts}

Django ORM Models (models.py)
  Component    — mfr_pn, lcsc_code, category, parameters JSONB, parent FK (self)
  Footprint    — ipc_code, pad_count, pitch_mm
  NetlistEdge  — net_name, FK Component, pin_name
```

## Quickstart

```bash
# Start postgres + redis + web + celery
docker compose up -d

# Apply migrations
docker compose exec web python manage.py migrate

# Load 50 sample components (resistors, capacitors, ICs, connectors)
docker compose exec web python manage.py loaddata fixtures/seed_components.json

# GraphQL playground
open http://localhost:8000/graphql
```

## Example Queries

```graphql
# Parametric search: capacitors with ≥ 90 nF and ≥ 10 V rating
{ components(category: "capacitor", paramFilter: "{\"capacitance_nf\": 90, \"voltage_v\": 10}") {
    mfrPn lcscCode parameters
  }
}

# BOM explosion — traverse assembly hierarchy
{ bomExplosion(rootComponentId: 1) { id mfrPn category depth } }

# Netlist adjacency for VCC net
{ netlistGraph(netName: "VCC") { netName edges { componentId mfrPn pinName } } }
```

## Tests

20 pytest-django tests across 6 suites:

| Suite | Count | What it verifies |
|---|---|---|
| `test_component_crud` | 5 | add_component mutation, list all, filter by category, duplicate mfr_pn error, parameter round-trip |
| `test_jsonb_query` | 4 | JSONB `__gte` filter by capacitance, voltage, combined params, no-match returns empty |
| `test_netlist_graph` | 4 | single-component net, multi-component net, unknown net returns empty, create_netlist_edge mutation |
| `test_bom_explosion` | 3 | single root, two-level hierarchy, depth ordering |
| `test_cache` | 2 | cache miss → hit round-trip, post_save invalidation |
| `test_celery_tasks` | 2 | valid LCSC codes → valid list, missing LCSC → conflicts list |

```bash
# Run all tests (requires PostgreSQL + Redis)
POSTGRES_HOST=localhost POSTGRES_USER=pcb POSTGRES_PASSWORD=pcb POSTGRES_DB=pcbdb \
  REDIS_URL=redis://localhost:6379/0 \
  uv run pytest tests/ -v
```

## CI

| Job | What it runs |
|---|---|
| `lint` | ruff check + format |
| `mypy` | mypy --strict on catalog/ and pcb_api/ |
| `test` | 20 pytest-django tests against PostgreSQL 16 + Redis 7 service containers |
