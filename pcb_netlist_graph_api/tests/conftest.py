from __future__ import annotations

from typing import Any

import pytest
import strawberry

from catalog.schema import schema


@pytest.fixture
def execute() -> Any:
    def _execute(query: str) -> strawberry.types.ExecutionResult:
        return schema.execute_sync(query)

    return _execute
