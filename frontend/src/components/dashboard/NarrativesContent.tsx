"use client";

import React from "react";
import { Panel, MetricCard } from "./shared.jsx";

const NARRATIVES = [
  {
    title: "The Reluctant Hero Arc",
    desc: "Tony Stark's transformation from self-serving billionaire to hero is cited as the defining emotional journey of the MCU.",
    strength: 88,
    reviews: 412,
  },
  {
    title: "Practical Suits vs CGI Debate",
    desc: "Ongoing discussion about whether early practical suit elements aged better than later all-digital sequences.",
    strength: 64,
    reviews: 238,
  },
  {
    title: "MCU Kickoff Mythology",
    desc: "Iron Man is consistently framed as the origin point of a cinematic revolution — for better or worse.",
    strength: 97,
    reviews: 601,
  },
  {
    title: "Capitalist Hero Critique",
    desc: "A counter-narrative critiques the film's uncritical portrayal of weapons manufacturing and military glorification.",
    strength: 41,
    reviews: 109,
  },
  {
    title: "Pepper Potts Underutilization",
    desc: "Reviewers frequently argue Potts was wasted as a love interest despite strong chemistry with Stark.",
    strength: 55,
    reviews: 177,
  },
];

export default function NarrativesContent() {
  return (
    <div className="space-y-6">
      <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 2xl:grid-cols-4">
        <MetricCard label="ACTIVE NARRATIVES" value="5" sub="Identified this month" />
        <MetricCard label="DOMINANT" value="MCU Origin" sub="97% narrative strength" />
        <MetricCard label="COUNTER-NARRATIVES" value="2" sub="Gaining traction" />
        <MetricCard label="REVIEW COVERAGE" value="89%" sub="Narratives found in" />
      </section>

      <Panel
        title="Narrative Map"
        subtitle="Key storytelling themes across review content"
        rightTag={null}
      >
        <div className="space-y-0">
          {NARRATIVES.map((n, index) => (
            <div
              key={n.title}
              className={`py-4 ${index !== NARRATIVES.length - 1 ? "border-b border-white/10" : ""}`}
            >
              <div className="mb-2 flex items-start justify-between gap-4">
                <div className="text-sm font-semibold text-white">{n.title}</div>
                <div className="whitespace-nowrap text-xs text-white/50">
                  {n.reviews} reviews
                </div>
              </div>

              <div className="mb-3 text-sm leading-6 text-white/70">
                {n.desc}
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
          ))}
        </div>
      </Panel>
    </div>
  );
}