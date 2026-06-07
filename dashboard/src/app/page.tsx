"use client";

import Link from "next/link";

import { Card } from "@/components/ui/Card";
import { getHealth } from "@/lib/api";
import { API_BASE_URL } from "@/lib/api";
import { useResource } from "@/lib/useResource";

export default function HomePage() {
  const { data, error, loading } = useResource(getHealth, []);

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6">
      <div className="flex flex-col gap-2">
        <h1 className="text-2xl font-semibold text-ink">
          AnchorPrune — Governed State Graph Dashboard
        </h1>
        <p className="text-sm leading-relaxed text-muted">
          A microscope for governed agent state. This dashboard is{" "}
          <span className="text-ink">read-only</span>: it visualizes runs,
          anchors, quarantined payloads, milestones, audit events, and metrics
          from the AnchorPrune FastAPI service. It observes governance — it does
          not perform it.
        </p>
      </div>

      <Card className="flex items-center justify-between">
        <div className="flex flex-col gap-1">
          <span className="text-xs uppercase tracking-wide text-muted">
            API status
          </span>
          {loading ? (
            <span className="text-sm text-warn">Checking {API_BASE_URL}…</span>
          ) : error ? (
            <span className="text-sm text-danger">Unreachable — {error}</span>
          ) : (
            <span className="text-sm text-ok">
              Connected · Service v{data?.version} · {API_BASE_URL}
            </span>
          )}
        </div>
        <span
          className={`h-3 w-3 rounded-full ${
            loading ? "bg-warn" : error ? "bg-danger" : "bg-ok"
          }`}
        />
      </Card>

      {error ? (
        <Card className="text-sm text-muted">
          <p className="mb-2 font-medium text-ink">Start the API first</p>
          <pre className="overflow-x-auto rounded-lg bg-bg p-3 text-xs text-ink">
            {`anchorprune serve --db .anchorprune/anchorprune.db
# then create a run, e.g.
anchorprune run --input examples/supplier/scenario.json`}
          </pre>
          <p className="mt-2">
            Override the API URL with{" "}
            <code className="text-ink">NEXT_PUBLIC_ANCHORPRUNE_API_URL</code>.
          </p>
        </Card>
      ) : null}

      <Link
        href="/runs"
        className="inline-flex w-fit items-center gap-2 rounded-md bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-accent/80"
      >
        View runs →
      </Link>
    </div>
  );
}
