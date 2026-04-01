"use client";

import React from "react";
import { useParams } from "next/navigation";
import { Panel, MetricCard } from "./shared.jsx";

type NarrativesResponse = {
  metrics: {
    activeNarratives: number;
    dominantNarrative: string | null;
    counterNarratives: number;
    reviewCoverage: number;
  };
  narratives: {
    title: string;
    description?: string | null;
    strength: number;
    reviewCount: number;
    isCounterNarrative: boolean;
  }[];
};

export default function NarrativesContent() {
  const params = useParams();
  const studioId = typeof params?.studioId === "string" ? params.studioId : "";
  const movieId = typeof params?.movieId === "string" ? params.movieId : "";

  const [data, setData] = React.useState<NarrativesResponse | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    async function loadNarratives() {
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
            `${baseUrl}/api/v1/studios/${studioId}/movies/${movieId}/narratives`,
            { cache: "no-store" }
        );

        if (!res.ok) {
          throw new Error(`Failed to load narratives: ${res.status}`);
        }

        const json: NarrativesResponse = await res.json();
        setData(json);
      } catch (err) {
        console.error(err);
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    }

    loadNarratives();
  }, [studioId, movieId]);

  if (loading) {
    return <div className="text-white/70">Loading narratives...</div>;
  }

  if (error) {
    return <div className="text-red-300">Error loading narratives: {error}</div>;
  }

  return (
      <div className="space-y-6">
        <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 2xl:grid-cols-4">
          <MetricCard
              label="ACTIVE NARRATIVES"
              value={String(data?.metrics.activeNarratives ?? 0)}
              sub="Detected for this movie"
          />
          <MetricCard
              label="DOMINANT"
              value={data?.metrics.dominantNarrative ?? "N/A"}
              sub="Strongest narrative"
          />
          <MetricCard
              label="COUNTER-NARRATIVES"
              value={String(data?.metrics.counterNarratives ?? 0)}
              sub="Opposing narratives"
          />
          <MetricCard
              label="REVIEW COVERAGE"
              value={`${data?.metrics.reviewCoverage ?? 0}%`}
              sub="Strength proxy"
          />
        </section>

        <Panel
            title="Narrative Map"
            subtitle="Key storytelling themes across review content"
            rightTag={null}
        >
          <div className="space-y-0">
            {(data?.narratives ?? []).length === 0 ? (
                <div className="text-sm text-white/60">No narrative data yet.</div>
            ) : (
                data!.narratives.map((n, index) => (
                    <div
                        key={n.title}
                        className={`py-4 ${
                            index !== data!.narratives.length - 1 ? "border-b border-white/10" : ""
                        }`}
                    >
                      <div className="mb-2 flex items-start justify-between gap-4">
                        <div className="text-sm font-semibold text-white">{n.title}</div>
                        <div className="whitespace-nowrap text-xs text-white/50">
                          {n.reviewCount} reviews
                        </div>
                      </div>

                      <div className="mb-3 text-sm leading-6 text-white/70">
                        {n.description || "No narrative description available."}
                      </div>

                      <div className="flex items-center gap-3">
                        <div className="w-28 text-[10px] uppercase tracking-wide text-white/45">
                          Narrative strength
                        </div>

                        <div className="h-2 flex-1 overflow-hidden rounded-full bg-white/10">
                          <div
                              className="h-full rounded-full bg-red-400/80"
                              style={{ width: `${n.strength}%` }}
                          />
                        </div>

                        <div className="w-10 text-right text-xs font-semibold text-red-300">
                          {n.strength}%
                        </div>
                      </div>
                    </div>
                ))
            )}
          </div>
        </Panel>
      </div>
  );
}