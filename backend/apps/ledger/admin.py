"""Operator console v1.

Django admin is the console until the workflows have proven their shape. The
ledger is exposed strictly read-only here — the admin is a window, not a hand.
"""

from __future__ import annotations

from django.contrib import admin

from .models import ActorKey, Anchor, Event


@admin.register(ActorKey)
class ActorKeyAdmin(admin.ModelAdmin):
    list_display = ("handle", "actor_type", "is_active", "created_at", "revoked_at")
    list_filter = ("actor_type", "is_active")
    search_fields = ("handle", "public_key", "description")
    readonly_fields = ("id", "created_at")


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("seq", "type", "subject", "actor", "occurred_at", "short_hash")
    list_filter = ("type", "occurred_at")
    search_fields = ("subject", "hash", "uuid")
    date_hierarchy = "occurred_at"
    ordering = ("-seq",)

    @admin.display(description="hash")
    def short_hash(self, obj: Event) -> str:
        return f"{obj.hash[:16]}…"

    def get_readonly_fields(self, request, obj=None):
        return [field.name for field in self.model._meta.fields]

    def has_add_permission(self, request) -> bool:
        # Events are appended by services, never typed in by hand.
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False


@admin.register(Anchor)
class AnchorAdmin(admin.ModelAdmin):
    list_display = (
        "period",
        "event_count",
        "status",
        "chain",
        "short_root",
        "anchored_at",
    )
    list_filter = ("status", "chain")
    search_fields = ("merkle_root", "tx_hash")
    readonly_fields = (
        "period",
        "first_seq",
        "last_seq",
        "event_count",
        "merkle_root",
        "head_hash",
        "created_at",
    )

    @admin.display(description="merkle root")
    def short_root(self, obj: Anchor) -> str:
        return f"{obj.merkle_root[:16]}…"

    def has_add_permission(self, request) -> bool:
        return False
