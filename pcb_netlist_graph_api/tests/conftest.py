from __future__ import annotations

import pytest
from strawberry.test import TestClient

from catalog.schema import schema


@pytest.fixture
def gql_client() -> TestClient:
    return TestClient(schema)
