"use client";

import React from "react";
import { useParams } from "next/navigation";
import { Panel, MetricCard } from "./shared.jsx";

type ClaimItem = {
  id: string;
  claim: string;
  freq: number;
  mentionCount: number;
  verdict: string;
  tone: "low" | "mid" | "high";
};

type ClaimsResponse = {
  metrics: {
    totalClaims: number;
    verified: number;
    disputed: number;
    misleading: number;
  };
  claims: ClaimItem[];
};

function verdictClasses(tone: string) {
  if (tone === "low") {
    return "border-emerald-400/20 bg-emerald-400/10 text-emerald-200";
  }
  if (tone === "mid") {
    return "border-amber-400/20 bg-amber-400/10 text-amber-200";
  }
  return "border-red-400/20 bg-red-400/10 text-red-200";
}

export default function ClaimsContent() {
  const params = useParams();
  const studioId = typeof params?.studioId === "string" ? params.studioId : "";
  const movieId = typeof params?.movieId === "string" ? params.movieId : "";

  const [data, setData] = React.useState<ClaimsResponse | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    async function loadClaims() {
      if (!studioId || !movieId) {
        setError("Missing studioId or movieId.");
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);

        const baseUrl =
            (process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8010").replace(/\/+$/, "");

        const res = await fetch(
            `${baseUrl}/api/v1/studios/${studioId}/movies/${movieId}/claims`,
            { cache: "no-store" }
        );

        if (!res.ok) {
          throw new Error(`Failed to load claims: ${res.status}`);
        }

        const json: ClaimsResponse = await res.json();
        setData(json);
      } catch (err) {
        console.error(err);
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    }

    loadClaims();
  }, [studioId, movieId]);

  if (loading) {
    return <div className="text-white/70">Loading claims...</div>;
  }

  if (error) {
    return <div className="text-red-300">Error loading claims: {error}</div>;
  }

  return (
      <div className="space-y-6">
        <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 2xl:grid-cols-4">
          <MetricCard
              label="TOTAL CLAIMS"
              value={String(data?.metrics.totalClaims ?? 0)}
              sub="Across all reviews"
          />
          <MetricCard
              label="VERIFIED"
              value={String(data?.metrics.verified ?? 0)}
              sub="Claims marked verified"
          />
          <MetricCard
              label="DISPUTED"
              value={String(data?.metrics.disputed ?? 0)}
              sub="Claims marked disputed"
          />
          <MetricCard
              label="MISLEADING"
              value={String(data?.metrics.misleading ?? 0)}
              sub="Claims marked misleading"
          />
        </section>

        <Panel
            title="Claim Tracker"
            subtitle="Most frequently made claims across review transcripts"
            rightTag={null}
        >
          <div className="space-y-4">
            {(data?.claims ?? []).length === 0 ? (
                <div className="text-sm text-white/60">No claim data yet.</div>
            ) : (
                data!.claims.map((c) => (
                    <div
                        key={c.id}
                        className="flex items-start gap-3 rounded-2xl border border-white/10 bg-white/5 p-4"
                    >
                      <div className="flex-1">
                        <div className="mb-2 text-sm font-semibold text-white">
                          {c.claim}
                        </div>

                        <div className="max-w-[360px]">
                          <div className="h-2 overflow-hidden rounded-full bg-white/10">
                            <div
                                className="h-full rounded-full bg-red-400/80"
                                style={{ width: `${Math.max(0, Math.min(c.freq, 100))}%` }}
                            />
                          </div>
                        </div>

                        <div className="mt-2 text-xs text-white/55">
                          Mentioned in {c.freq}% of reviews
                          {c.mentionCount > 0 ? ` • ${c.mentionCount} mentions` : ""}
                        </div>
                      </div>

                      <div
                          className={`min-w-[88px] rounded-full border px-3 py-1 text-center text-xs font-medium ${verdictClasses(
                              c.tone
                          )}`}
                      >
                        {c.verdict}
                      </div>
                    </div>
                ))
            )}
          </div>
        </Panel>
      </div>
  );
}