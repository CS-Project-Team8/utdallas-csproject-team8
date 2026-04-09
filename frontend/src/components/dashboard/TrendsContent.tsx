"use client";

import React from "react";
import { useParams } from "next/navigation";
import { Panel, MetricCard, LegendDot, SignalBar } from "./shared.jsx";

type TrendsResponse = {
    metrics: {
        trendingTopics: number;
        peakWeek: string | null;
        growthRate: number | null;
        viralReviews: number;
    };
    sentimentTimeline: {
        periodStart: string;
        periodEnd: string;
        avgSentiment: number | null;
        posPct: number | null;
        negPct: number | null;
        neuPct: number | null;
        reviewVideoCount: number;
    }[];
    reviewVolume: {
        weekStart: string;
        reviewsThisWeek: number;
        cumulativeReviews: number;
    }[];
    risingSignals: {
        label: string;
        value: number;
    }[];
    topWords: string[];
};

function AnimatedBar({
                         targetHeight,
                         delay,
                     }: {
    targetHeight: number;
    delay: number;
}) {
    const [height, setHeight] = React.useState(0);

    React.useEffect(() => {
        const timeout = setTimeout(() => {
            const duration = 1000;
            let startTime: number | null = null;
            const easeOut = (t: number) => 1 - Math.pow(1 - t, 5);

            const animate = (timestamp: number) => {
                if (!startTime) startTime = timestamp;
                const elapsed = timestamp - startTime;
                const progress = Math.min(elapsed / duration, 1);
                setHeight(easeOut(progress) * targetHeight);
                if (progress < 1) requestAnimationFrame(animate);
            };

            requestAnimationFrame(animate);
        }, delay);

        return () => clearTimeout(timeout);
    }, [targetHeight, delay]);

    return (
        <div
            className="w-full rounded-t-md bg-white/70"
            style={{ height: `${height}%` }}
        />
    );
}

function SentimentTimelineChart({
                                    points,
                                }: {
    points: TrendsResponse["sentimentTimeline"];
}) {
    const width = 900;
    const height = 260;
    const padX = 28;
    const padY = 20;
    const innerW = width - padX * 2;
    const innerH = height - padY * 2;

    const safePoints = points.map((p) => ({
        label: new Date(p.periodStart).toLocaleDateString(undefined, {
            month: "numeric",
            day: "numeric",
        }),
        pos: p.posPct ?? 0,
        neg: p.negPct ?? 0,
        avg: p.avgSentiment ?? 0,
    }));

    const xFor = (index: number) =>
        safePoints.length === 1
            ? width / 2
            : padX + (index / (safePoints.length - 1)) * innerW;

    const yPct = (value: number) => padY + (1 - value) * innerH;
    const yAvg = (value: number) => {
        const normalized = Math.max(-1, Math.min(1, value));
        return padY + (1 - (normalized + 1) / 2) * innerH;
    };

    const makePath = (
        values: number[],
        yFn: (value: number) => number
    ) =>
        values
            .map((value, index) => {
                const x = xFor(index);
                const y = yFn(value);
                return `${index === 0 ? "M" : "L"} ${x} ${y}`;
            })
            .join(" ");

    const posPath = makePath(
        safePoints.map((p) => p.pos),
        yPct
    );
    const negPath = makePath(
        safePoints.map((p) => p.neg),
        yPct
    );
    const avgPath = makePath(
        safePoints.map((p) => p.avg),
        yAvg
    );

    return (
        <div>
            <div className="rounded-2xl border border-white/10 bg-black/20 p-4">
                <svg
                    viewBox={`0 0 ${width} ${height}`}
                    className="h-64 w-full overflow-visible"
                    preserveAspectRatio="none"
                >
                    {[0, 0.25, 0.5, 0.75, 1].map((tick) => {
                        const y = yPct(tick);
                        return (
                            <line
                                key={tick}
                                x1={padX}
                                y1={y}
                                x2={width - padX}
                                y2={y}
                                stroke="rgba(255,255,255,0.08)"
                                strokeWidth="1"
                            />
                        );
                    })}

                    <line
                        x1={padX}
                        y1={yAvg(0)}
                        x2={width - padX}
                        y2={yAvg(0)}
                        stroke="rgba(16,185,129,0.2)"
                        strokeDasharray="4 4"
                        strokeWidth="1"
                    />

                    <path
                        d={posPath}
                        fill="none"
                        stroke="rgba(248,113,113,0.95)"
                        strokeWidth="3"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                    />
                    <path
                        d={negPath}
                        fill="none"
                        stroke="rgba(255,255,255,0.55)"
                        strokeWidth="3"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                    />
                    <path
                        d={avgPath}
                        fill="none"
                        stroke="rgba(110,231,183,0.95)"
                        strokeWidth="3"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                    />

                    {safePoints.map((p, i) => {
                        const x = xFor(i);
                        return (
                            <g key={p.label}>
                                <circle cx={x} cy={yPct(p.pos)} r="4" fill="rgba(248,113,113,1)" />
                                <circle cx={x} cy={yPct(p.neg)} r="4" fill="rgba(255,255,255,0.85)" />
                                <circle cx={x} cy={yAvg(p.avg)} r="4" fill="rgba(110,231,183,1)" />
                            </g>
                        );
                    })}
                </svg>

                <div className="mt-3 flex items-center justify-between gap-2 text-xs text-white/55">
                    {safePoints.map((p, index) => {
                        const showLabel =
                            safePoints.length <= 6 ||
                            index === 0 ||
                            index === safePoints.length - 1 ||
                            index % Math.ceil(safePoints.length / 4) === 0;

                        return (
                            <div
                                key={`${p.label}-${index}`}
                                className="min-w-0 flex-1 text-center"
                            >
                                {showLabel ? (
                                    <span className="block truncate">
            {new Date(points[index].periodStart).toLocaleDateString(undefined, {
                month: "numeric",
                day: "numeric",
            })}
          </span>
                                ) : (
                                    <span className="block opacity-0">.</span>
                                )}
                            </div>
                        );
                    })}
                </div>
            </div>
        </div>
    );
}




export default function TrendsContent() {
    const params = useParams();
    const studioId = typeof params?.studioId === "string" ? params.studioId : "";
    const movieId = typeof params?.movieId === "string" ? params.movieId : "";

    const [data, setData] = React.useState<TrendsResponse | null>(null);
    const [loading, setLoading] = React.useState(true);
    const [error, setError] = React.useState<string | null>(null);

    React.useEffect(() => {
        async function loadTrends() {
            if (!studioId || !movieId) {
                setError("Missing studioId or movieId.");
                setLoading(false);
                return;
            }

            try {
                setLoading(true);
                setError(null);

                const baseUrl =
                    (process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000").replace(/\/+$/, "");

                const res = await fetch(
                    `${baseUrl}/api/v1/studios/${studioId}/movies/${movieId}/trends`,
                    { cache: "no-store" }
                );

                if (!res.ok) {
                    throw new Error(`Failed to load trends: ${res.status}`);
                }

                const json: TrendsResponse = await res.json();
                setData(json);
            } catch (err) {
                console.error(err);
                setError(err instanceof Error ? err.message : "Unknown error");
            } finally {
                setLoading(false);
            }
        }

        loadTrends();
    }, [studioId, movieId]);

    if (loading) {
        return <div className="text-white/70">Loading trends...</div>;
    }

    if (error) {
        return <div className="text-red-300">Error loading trends: {error}</div>;
    }

    const metrics = data?.metrics;
    const volume = data?.reviewVolume ?? [];
    const peakLabel = metrics?.peakWeek
        ? new Date(metrics.peakWeek).toLocaleDateString()
        : "N/A";

    const chartHeights =
        volume.length > 0
            ? (() => {
                const max = Math.max(...volume.map((v) => v.reviewsThisWeek), 1);
                return volume.map((v) => Math.max(8, Math.round((v.reviewsThisWeek / max) * 100)));
            })()
            : [40, 55, 70, 90, 85, 100, 95, 60];

    return (
        <div className="space-y-6">
            <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 2xl:grid-cols-4">
                <MetricCard
                    label="TRENDING TOPICS"
                    value={String(metrics?.trendingTopics ?? 0)}
                    sub="Current discussion topics"
                />
                <MetricCard
                    label="PEAK WEEK"
                    value={peakLabel}
                    sub="Highest review volume"
                />
                <MetricCard
                    label="GROWTH RATE"
                    value={
                        metrics?.growthRate !== null && metrics?.growthRate !== undefined
                            ? `${metrics.growthRate > 0 ? "+" : ""}${metrics.growthRate}%`
                            : "N/A"
                    }
                    sub="Latest vs earliest week"
                />
                <MetricCard
                    label="VIRAL REVIEWS"
                    value={String(metrics?.viralReviews ?? 0)}
                    sub="Over 500k views"
                />
            </section>

            <Panel
                title="Sentiment Timeline"
                subtitle="Positive, negative, and average sentiment over time"
                rightTag={null}
            >
                <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                    <div className="mb-4 flex flex-wrap gap-4">
                        <div className="flex items-center gap-2 text-sm text-white/80">
                            <span className="h-2.5 w-2.5 rounded-full bg-red-400" />
                            Positive
                        </div>
                        <div className="flex items-center gap-2 text-sm text-white/80">
                            <span className="h-2.5 w-2.5 rounded-full bg-white/50" />
                            Negative
                        </div>
                        <div className="flex items-center gap-2 text-sm text-white/80">
                            <span className="h-2.5 w-2.5 rounded-full bg-emerald-300" />
                            Avg sentiment
                        </div>
                    </div>

                    {(data?.sentimentTimeline ?? []).length === 0 ? (
                        <div className="text-sm text-white/60">No sentiment timeline data yet.</div>
                    ) : (
                        <SentimentTimelineChart points={data!.sentimentTimeline} />
                    )}
                </div>
            </Panel>

            <Panel
                title="Review Volume Over Time"
                subtitle="Weekly review count since release"
                rightTag={null}
            >
                <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                    <div className="flex h-56 items-end gap-3">
                        {chartHeights.map((h, i) => (
                            <div key={i} className="flex h-full flex-1 items-end">
                                <AnimatedBar targetHeight={h} delay={i * 60} />
                            </div>
                        ))}
                    </div>

                    <div className="mt-3 flex justify-between text-xs text-white/60">
                        <span>{volume[0] ? new Date(volume[0].weekStart).toLocaleDateString() : "Start"}</span>
                        <span>
              {volume[volume.length - 1]
                  ? new Date(volume[volume.length - 1].weekStart).toLocaleDateString()
                  : "End"}
            </span>
                    </div>
                </div>
            </Panel>

            <Panel
                title="Rising Signals"
                subtitle="Audience emotions gaining momentum"
                rightTag={null}
            >
                <div className="space-y-4">
                    {(data?.risingSignals ?? []).length === 0 ? (
                        <div className="text-sm text-white/60">No mood signal data yet.</div>
                    ) : (
                        data!.risingSignals.map((signal) => (
                            <SignalBar
                                key={signal.label}
                                label={signal.label}
                                value={signal.value}
                                muted={signal.value < 30}
                            />
                        ))
                    )}
                </div>
            </Panel>

            <Panel
                title="Trending Sentiment Words"
                subtitle="Breakout terms this week"
                rightTag={null}
            >
                <div className="flex flex-wrap gap-2">
                    {(data?.topWords ?? []).length === 0 ? (
                        <div className="text-sm text-white/60">No sentiment word data yet.</div>
                    ) : (
                        data!.topWords.map((t) => (
                            <span
                                key={t}
                                className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-sm text-white/80"
                            >
                {t}
              </span>
                        ))
                    )}
                </div>
            </Panel>
        </div>
    );
}