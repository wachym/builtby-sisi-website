"""The public verifier and the internal append endpoint.

Reads are open on purpose: the ledger's value is that an outsider can check it.
Writes require an internal service key, and remain the only route into the
chain.
"""

from datetime import date

from ninja import Status
from ninja_extra import ControllerBase, api_controller, http_get, http_post
from ninja_extra.pagination import PageNumberPaginationExtra, PaginatedResponseSchema, paginate
from ninja_extra.permissions import AllowAny

from apps.accounts.permissions import IsInternalService

from . import services
from .models import Anchor, Event, EventType
from .schemas import (
    AnchorOut,
    ChainReportOut,
    EventIn,
    EventOut,
    EventTypeOut,
    HeadOut,
)


@api_controller("/ledger", tags=["ledger"], permissions=[AllowAny])
class LedgerController(ControllerBase):
    """Read the spine; append to it with a service key."""

    @http_get("/head", response=HeadOut, url_name="ledger-head", operation_id="ledger_head")
    def head(self):
        """Current chain head — the cheapest integrity check available."""
        seq, digest = services.head()
        return HeadOut(seq=seq, hash=digest, event_count=Event.objects.count())

    @http_get(
        "/events",
        response=PaginatedResponseSchema[EventOut],
        url_name="ledger-events",
        operation_id="ledger_list_events",
    )
    @paginate(PageNumberPaginationExtra, page_size=50)
    def list_events(self, type: str | None = None, subject: str | None = None):
        """Recorded events, newest first, optionally filtered."""
        queryset = Event.objects.select_related("actor").order_by("-seq")
        if type:
            queryset = queryset.filter(type=type)
        if subject:
            queryset = queryset.filter(subject=subject)
        return queryset

    @http_get(
        "/events/{int:seq}",
        response=EventOut,
        url_name="ledger-event",
        operation_id="ledger_get_event",
    )
    def get_event(self, seq: int):
        return self.get_object_or_exception(
            Event.objects.select_related("actor"), seq=seq
        )

    @http_get(
        "/verify",
        response=ChainReportOut,
        url_name="ledger-verify",
        operation_id="ledger_verify",
    )
    def verify(self, since_seq: int = 0, limit: int | None = None):
        """Re-derive every hash and report any break in the chain."""
        report = services.verify_chain(since_seq=since_seq, limit=limit)
        return ChainReportOut(
            ok=report.ok,
            checked=report.checked,
            head_seq=report.head_seq,
            head_hash=report.head_hash,
            problems=[{"seq": p.seq, "reason": p.reason} for p in report.problems],
        )

    @http_get(
        "/anchors",
        response=list[AnchorOut],
        url_name="ledger-anchors",
        operation_id="ledger_list_anchors",
    )
    def list_anchors(self, since: date | None = None):
        queryset = Anchor.objects.all()
        if since:
            queryset = queryset.filter(period__gte=since)
        return list(queryset[:365])

    @http_get(
        "/event-types",
        response=list[EventTypeOut],
        url_name="ledger-event-types",
        operation_id="ledger_list_event_types",
    )
    def list_event_types(self):
        """The vocabulary, so clients do not hard-code it."""
        return [EventTypeOut(value=c.value, label=c.label) for c in EventType]

    @http_post(
        "/events",
        response={201: EventOut},
        permissions=[IsInternalService],
        url_name="ledger-append",
        operation_id="ledger_append_event",
    )
    def append(self, payload: EventIn):
        """Append one event. Internal services only."""
        event = services.append_event(
            event_type=payload.type,
            payload=payload.payload,
            subject=payload.subject,
            actor=payload.actor,
            occurred_at=payload.occurred_at,
        )
        return Status(201, event)
