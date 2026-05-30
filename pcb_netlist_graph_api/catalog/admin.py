from __future__ import annotations

from django.contrib import admin

from catalog.models import Component, Footprint, NetlistEdge

admin.site.register(Component)
admin.site.register(Footprint)
admin.site.register(NetlistEdge)
