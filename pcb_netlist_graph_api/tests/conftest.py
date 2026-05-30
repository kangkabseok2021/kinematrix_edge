from __future__ import annotations

import json

import pytest
from strawberry.test import Client

from catalog.schema import schema


@pytest.fixture
def gql_client() -> Client:
    return Client(schema)
