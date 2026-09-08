/**
 * Typed access to the Sisi OS backend.
 *
 * Every type here comes from `schema.d.ts`, which is generated from the
 * backend's OpenAPI document (`npm run api:types`). Nothing about the API
 * shape is hand-written, so a backend change that would break this app fails
 * in CI rather than in a browser.
 *
 * Server-side only: `API_BASE_URL` is not a NEXT_PUBLIC variable, and these
 * functions are called from server components.
 */

import type { components } from "./schema";

export type LedgerEvent = components["schemas"]["EventOut"];
export type ChainHead = components["schemas"]["HeadOut"];
export type ChainReport = components["schemas"]["ChainReportOut"];
export type Anchor = components["schemas"]["AnchorOut"];
export type Health = components["schemas"]["HealthOut"];

type PagedEvents = components["schemas"]["PaginatedResponseSchema_EventOut_"];

const API_BASE_URL = process.env.API_BASE_URL ?? "http://127.0.0.1:8000";

export class ApiUnavailableError extends Error {
  constructor(
    readonly path: string,
    readonly cause?: unknown,
  ) {
    super(`Sisi OS API unavailable at ${path}`);
    this.name = "ApiUnavailableError";
  }
}

async function get<T>(path: string, params?: Record<string, string | number | undefined>): Promise<T> {
  const url = new URL(`/api/v1${path}`, API_BASE_URL);
  for (const [key, value] of Object.entries(params ?? {})) {
    if (value !== undefined) url.searchParams.set(key, String(value));
  }

  let response: Response;
  try {
    response = await fetch(url, {
      headers: { Accept: "application/json" },
      // Never cached. A proof page that serves a stale snapshot — of a chain
      // head, or of a verification result — is worse than one that says the
      // ledger is unreachable.
      cache: "no-store",
    });
  } catch (cause) {
    // A missing backend must degrade the page, never break the site.
    throw new ApiUnavailableError(path, cause);
  }

  if (!response.ok) {
    throw new ApiUnavailableError(`${path} (HTTP ${response.status})`);
  }

  return (await response.json()) as T;
}

export const ledger = {
  head: () => get<ChainHead>("/ledger/head"),
  verify: () => get<ChainReport>("/ledger/verify"),
  events: (limit = 25) =>
    get<PagedEvents>("/ledger/events", { page: 1, page_size: limit }),
  anchors: () => get<Anchor[]>("/ledger/anchors"),
};

export const system = {
  health: () => get<Health>("/system/health"),
};

/**
 * Read the spine for a page render.
 *
 * Returns a discriminated result rather than throwing: the proof page is
 * public, and an unreachable backend should produce an honest empty state
 * instead of a 500.
 */
export async function readSpine(): Promise<
  | {
      available: true;
      head: ChainHead;
      report: ChainReport;
      events: LedgerEvent[];
      anchors: Anchor[];
    }
  | { available: false; reason: string }
> {
  try {
    const [head, report, events, anchors] = await Promise.all([
      ledger.head(),
      ledger.verify(),
      ledger.events(),
      ledger.anchors(),
    ]);
    return { available: true, head, report, events: events.results ?? [], anchors };
  } catch (error) {
    return {
      available: false,
      reason: error instanceof Error ? error.message : "unknown error",
    };
  }
}
