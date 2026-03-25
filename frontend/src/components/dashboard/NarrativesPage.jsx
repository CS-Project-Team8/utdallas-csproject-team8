"use client";
import React from "react";
import { Panel, MetricCard } from "./shared";

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

export default function NarrativesPage() {
  return (
      <div className="pageWrap">
      <section className="metricRow">
        <MetricCard label="ACTIVE NARRATIVES"  value="5"         sub="Identified this month" />
        <MetricCard label="DOMINANT"           value="MCU Origin" sub="97% narrative strength" />
        <MetricCard label="COUNTER-NARRATIVES" value="2"         sub="Gaining traction" />
        <MetricCard label="REVIEW COVERAGE"    value="89%"       sub="Narratives found in" />
      </section>

      <section className="bottomSection">
        <Panel title="Narrative Map" subtitle="Key storytelling themes across review content">
          <div className="list" style={{ gap: 0 }}>
            {NARRATIVES.map((n) => (
              <div
                key={n.title}
                style={{ padding: "16px 0", borderBottom: "1px solid var(--border)" }}
              >
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    marginBottom: 6,
                  }}
                >
                  <div className="riskName">{n.title}</div>
                  <div style={{ fontSize: 11, color: "var(--muted)", whiteSpace: "nowrap", marginLeft: 16 }}>
                    {n.reviews} reviews
                  </div>
                </div>
                <div className="riskStatus" style={{ marginBottom: 10 }}>{n.desc}</div>
                <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                  <div style={{ fontSize: 10, color: "var(--muted)", width: 110 }}>
                    Narrative strength
                  </div>
                  <div className="topicTrack" style={{ flex: 1 }}>
                    <div className="topicFill" style={{ width: `${n.strength}%` }} />
                  </div>
                  <div
                    style={{
                      fontSize: 12,
                      fontWeight: 600,
                      color: "var(--accent)",
                      width: 36,
                      textAlign: "right",
                    }}
                  >
                    {n.strength}%
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Panel>
      </section>
    </div>
  );
}