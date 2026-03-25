"use client";

import React from "react";
import { Panel, MetricCard, LegendDot, SignalBar } from "./shared.jsx";

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

export default function TrendsContent() {
  return (
    <div className="space-y-6">
      <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 2xl:grid-cols-4">
        <MetricCard label="TRENDING TOPICS" value="14" sub="+3 this week" />
        <MetricCard label="PEAK WEEK" value="Week 6" sub="1,204 reviews" />
        <MetricCard label="GROWTH RATE" value="+22%" sub="vs last month" />
        <MetricCard label="VIRAL REVIEWS" value="7" sub="Over 500k views" />
      </section>

      <Panel
        title="Sentiment Timeline"
        subtitle="Positive vs. negative trend over time"
        rightTag={
          <span className="rounded-full border border-emerald-400/30 bg-emerald-400/10 px-3 py-1 text-xs text-emerald-200">
            +5% this year
          </span>
        }
      >
        <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
          <div className="mb-4 flex gap-4">
            <LegendDot label="Positive" isMuted={false} />
            <LegendDot label="Negative" isMuted={true} />
          </div>

          <div className="relative h-56 rounded-xl border border-white/10 bg-black/20">
            <div className="absolute inset-x-4 top-1/2 h-px bg-white/10" />
            <div className="absolute inset-x-6 bottom-10 h-24 rounded-full border-t-2 border-red-300/70" />
            <div className="absolute inset-x-6 bottom-16 h-20 rounded-full border-t-2 border-white/80" />
            <div className="absolute right-20 top-16 h-3 w-3 rounded-full bg-white" />
          </div>
        </div>
      </Panel>

      <Panel
        title="Review Volume Over Time"
        subtitle="Weekly review count since release"
        rightTag={null}
      >
        <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
          <div className="flex h-56 items-end gap-3">
            {[40, 55, 70, 90, 85, 100, 95, 60].map((h, i) => (
              <div key={i} className="flex h-full flex-1 items-end">
                <AnimatedBar targetHeight={h} delay={i * 60} />
              </div>
            ))}
          </div>

          <div className="mt-3 flex justify-between text-xs text-white/60">
            <span>Week 1</span>
            <span>Week 8</span>
          </div>
        </div>
      </Panel>

      <Panel
        title="Rising Signals"
        subtitle="Audience emotions gaining momentum"
        rightTag={null}
      >
        <div className="space-y-4">
          <SignalBar label="Hype" value={91} muted={false} />
          <SignalBar label="Excitement" value={82} muted={false} />
          <SignalBar label="Satisfaction" value={74} muted={false} />
          <SignalBar label="Nostalgia" value={67} muted={false} />
          <SignalBar label="Disappointment" value={18} muted={true} />
        </div>
      </Panel>

      <Panel
        title="Trending Sentiment Words"
        subtitle="Breakout terms this week"
        rightTag={null}
      >
        <div className="flex flex-wrap gap-2">
          {[
            "iconic",
            "game-changer",
            "revolutionary",
            "legendary",
            "masterpiece",
            "epic",
            "groundbreaking",
            "stunning",
          ].map((t) => (
            <span
              key={t}
              className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-sm text-white/80"
            >
              {t}
            </span>
          ))}
        </div>
      </Panel>
    </div>
  );
}