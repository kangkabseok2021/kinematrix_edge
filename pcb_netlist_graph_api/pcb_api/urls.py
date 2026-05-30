from __future__ import annotations

from django.urls import path
from strawberry.django.views import GraphQLView

from catalog.schema import schema

urlpatterns = [
    path("graphql", GraphQLView.as_view(schema=schema)),
]
