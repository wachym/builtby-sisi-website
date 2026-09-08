import type { Metadata } from "next";
import Link from "next/link";
import { readSpine, type LedgerEvent } from "@/lib/api/client";

export const metadata: Metadata = {
  title: "Proof of Work — Built By Sisi",
  description:
    "The live delivery ledger: every perception, decision, approval, and settlement, hash-chained and independently verifiable.",
};

// The ledger changes as work happens; never serve a build-time snapshot.
export const dynamic = "force-dynamic";

const PLANE: Record<string, "see" | "think" | "settle" | "spine"> = {
  "perception.captured": "see",
  "artifact.stored": "see",
  "brief.drafted": "think",
  "estimate.proposed": "think",
  "agent.run.started": "think",
  "agent.tool.called": "think",
  "agent.run.finished": "think",
  "human.approved": "think",
  "human.rejected": "think",
  "commit.pushed": "think",
  "milestone.delivered": "settle",
  "client.accepted": "settle",
  "invoice.issued": "settle",
  "escrow.funded": "settle",
  "escrow.released": "settle",
  "yield.accrued": "settle",
  "anchor.created": "spine",
  "system.note": "spine",
};

function planeOf(type: string) {
  return PLANE[type] ?? "spine";
}

function formatTime(value: string) {
  return new Date(value).toISOString().replace("T", " ").slice(0, 19) + "Z";
}

function EventRow({ event }: { event: LedgerEvent }) {
  return (
    <li className={`proof__event proof__event--${planeOf(event.type)}`}>
      <div className="proof__event-head">
        <span className="proof__seq">#{event.seq}</span>
        <span className="proof__type">{event.type}</span>
        {event.actor ? <span className="proof__actor">{event.actor}</span> : null}
        <time className="proof__time" dateTime={event.occurred_at}>
          {formatTime(event.occurred_at)}
        </time>
      </div>
      {event.subject ? <p className="proof__subject">{event.subject}</p> : null}
      <dl className="proof__hashes">
        <div>
          <dt>hash</dt>
          <dd>{event.hash}</dd>
        </div>
        <div>
          <dt>prev</dt>
          <dd>{event.prev_hash}</dd>
        </div>
        {event.signature ? (
          <div>
            <dt>sig</dt>
            <dd>{event.signature.slice(0, 32)}…</dd>
          </div>
        ) : null}
      </dl>
    </li>
  );
}

export default async function ProofPage() {
  const spine = await readSpine();

  return (
    <main id="main" className="proof">
      <div className="container">
        <header className="proof__masthead">
          <p className="eyebrow">Proof of work</p>
          <h1 className="proof__title">
            The ledger, <em>as it stands.</em>
          </h1>
          <p className="proof__lead">
            Every perception, decision, approval, and settlement in the studio is one
            hash-chained record. Nothing here is written by hand, and nothing can be
            edited after the fact — corrections are new events. Check the chain
            yourself: each row carries the hash before it.
          </p>
          <Link className="proof__back" href="/">
            ← Back to Built By Sisi
          </Link>
        </header>

        {!spine.available ? (
          <section className="proof__panel proof__panel--offline">
            <h2 className="proof__panel-title">The ledger is not reachable right now</h2>
            <p>
              This page reads the system of record directly. It is offline or still
              starting, so there is nothing to show rather than something invented.
            </p>
            <p className="proof__reason">{spine.reason}</p>
          </section>
        ) : (
          <>
            <section className="proof__status" aria-label="Chain status">
              <div className="proof__stat">
                <span className="proof__stat-value">#{spine.head.seq}</span>
                <span className="proof__stat-label">Chain head</span>
              </div>
              <div className="proof__stat">
                <span className="proof__stat-value">{spine.head.event_count}</span>
                <span className="proof__stat-label">Events recorded</span>
              </div>
              <div className="proof__stat">
                <span className="proof__stat-value">{spine.anchors.length}</span>
                <span className="proof__stat-label">Days anchored</span>
              </div>
              <div
                className={`proof__stat proof__stat--verdict${
                  spine.report.ok ? " is-ok" : " is-broken"
                }`}
              >
                <span className="proof__stat-value">
                  {spine.report.ok ? "Verified" : "Broken"}
                </span>
                <span className="proof__stat-label">
                  {spine.report.checked} event
                  {spine.report.checked === 1 ? "" : "s"} re-derived
                </span>
              </div>
            </section>

            <p className="proof__head-hash">
              <span>head</span>
              <code>{spine.head.hash}</code>
            </p>

            {!spine.report.ok ? (
              <section className="proof__panel proof__panel--broken">
                <h2 className="proof__panel-title">Verification failed</h2>
                <ul>
                  {spine.report.problems.map((problem) => (
                    <li key={`${problem.seq}-${problem.reason}`}>
                      #{problem.seq}: {problem.reason}
                    </li>
                  ))}
                </ul>
              </section>
            ) : null}

            <section aria-label="Recent events">
              <h2 className="proof__section-title">Most recent events</h2>
              {spine.events.length === 0 ? (
                <p className="proof__empty">
                  The chain is empty. The first recorded fact will appear here.
                </p>
              ) : (
                <ol className="proof__events">
                  {spine.events.map((event) => (
                    <EventRow key={event.seq} event={event} />
                  ))}
                </ol>
              )}
            </section>

            {spine.anchors.length > 0 ? (
              <section aria-label="Anchors">
                <h2 className="proof__section-title">Daily anchors</h2>
                <p className="proof__note">
                  Each day of the ledger reduces to one Merkle root. Publishing those
                  roots on-chain is what makes this history checkable by someone who
                  does not trust us.
                </p>
                <div className="proof__tablewrap">
                  <table className="proof__table">
                    <thead>
                      <tr>
                        <th>Period</th>
                        <th>Events</th>
                        <th>Merkle root</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {spine.anchors.map((anchor) => (
                        <tr key={anchor.period}>
                          <td>{anchor.period}</td>
                          <td>{anchor.event_count}</td>
                          <td>
                            <code>{anchor.merkle_root.slice(0, 24)}…</code>
                          </td>
                          <td>{anchor.status}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            ) : null}
          </>
        )}
      </div>
    </main>
  );
}
