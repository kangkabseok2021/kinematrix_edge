from __future__ import annotations

import pytest
from django.test import override_settings

from catalog.tasks import validate_bom
from tests.factories import ComponentFactory


@pytest.mark.django_db
@override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
def test_validate_bom_valid_components() -> None:
    c1 = ComponentFactory.create(lcsc_code="C100001")
    c2 = ComponentFactory.create(lcsc_code="C100002")
    result = validate_bom.delay([c1.id, c2.id]).get()
    assert set(result["valid"]) == {c1.id, c2.id}
    assert result["conflicts"] == []


@pytest.mark.django_db
@override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
def test_validate_bom_flags_missing_lcsc() -> None:
    valid_comp = ComponentFactory.create(lcsc_code="C200001")
    conflict_comp = ComponentFactory.create(lcsc_code="")
    result = validate_bom.delay([valid_comp.id, conflict_comp.id]).get()
    assert valid_comp.id in result["valid"]
    assert conflict_comp.id in result["conflicts"]
