"use client";

import React from "react";
import { Panel, MetricCard } from "./shared.jsx";

const CLAIMS = [
  { claim: "Iron Man single-handedly launched the MCU", freq: 94, verdict: "Verified", tone: "low" },
  { claim: "RDJ improvised most of his best lines", freq: 81, verdict: "Disputed", tone: "mid" },
  { claim: "The film had a $200M+ production budget", freq: 76, verdict: "Misleading", tone: "high" },
  { claim: "Pepper Potts was originally a minor character", freq: 62, verdict: "Verified", tone: "low" },
  { claim: "The suit-up scene took 3 years to render", freq: 58, verdict: "Unverified", tone: "mid" },
  { claim: "Jon Favreau rewrote the script daily on set", freq: 47, verdict: "Disputed", tone: "mid" },
  { claim: "The post-credits scene was added last minute", freq: 43, verdict: "Verified", tone: "low" },
  { claim: "Iron Man flopped in its opening weekend", freq: 29, verdict: "Misleading", tone: "high" },
];

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
  return (
    <div className="space-y-6">
      <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 2xl:grid-cols-4">
        <MetricCard label="TOTAL CLAIMS" value="38" sub="Across all reviews" />
        <MetricCard label="VERIFIED" value="14" sub="37% of claims" />
        <MetricCard label="DISPUTED" value="11" sub="29% of claims" />
        <MetricCard label="MISLEADING" value="13" sub="34% of claims" />
      </section>

      <Panel
        title="Claim Tracker"
        subtitle="Most frequently made claims across review transcripts"
        rightTag={null}
      >
        <div className="space-y-4">
          {CLAIMS.map((c) => (
            <div
              key={c.claim}
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
                      style={{ width: `${c.freq}%` }}
                    />
                  </div>
                </div>

                <div className="mt-2 text-xs text-white/55">
                  Mentioned in {c.freq}% of reviews
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
          ))}
        </div>
      </Panel>
    </div>
  );
}