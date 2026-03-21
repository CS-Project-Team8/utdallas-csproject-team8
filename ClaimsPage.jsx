import React from "react";
import { Panel, MetricCard } from "../components/shared";

const CLAIMS = [
  { claim: "Iron Man single-handedly launched the MCU",     freq: 94, verdict: "Verified",   tone: "low" },
  { claim: "RDJ improvised most of his best lines",         freq: 81, verdict: "Disputed",   tone: "mid" },
  { claim: "The film had a $200M+ production budget",       freq: 76, verdict: "Misleading",  tone: "high" },
  { claim: "Pepper Potts was originally a minor character", freq: 62, verdict: "Verified",   tone: "low" },
  { claim: "The suit-up scene took 3 years to render",      freq: 58, verdict: "Unverified",  tone: "mid" },
  { claim: "Jon Favreau rewrote the script daily on set",   freq: 47, verdict: "Disputed",   tone: "mid" },
  { claim: "The post-credits scene was added last minute",  freq: 43, verdict: "Verified",   tone: "low" },
  { claim: "Iron Man flopped in its opening weekend",       freq: 29, verdict: "Misleading",  tone: "high" },
];

export default function ClaimsPage() {
  return (
      <div className="pageWrap">
      <section className="metricRow">
        <MetricCard label="TOTAL CLAIMS" value="38"  sub="Across all reviews" />
        <MetricCard label="VERIFIED"     value="14"  sub="37% of claims" />
        <MetricCard label="DISPUTED"     value="11"  sub="29% of claims" />
        <MetricCard label="MISLEADING"   value="13"  sub="34% of claims" />
      </section>

      <section className="bottomSection">
        <Panel title="Claim Tracker" subtitle="Most frequently made claims across review transcripts">
          <div className="list">
            {CLAIMS.map((c) => (
              <div key={c.claim} className="riskRow" style={{ alignItems: "flex-start", gap: "12px" }}>
                <div style={{ flex: 1 }}>
                  <div className="riskName" style={{ marginBottom: 4 }}>{c.claim}</div>
                  <div className="topicTrack" style={{ maxWidth: 360 }}>
                    <div className="topicFill" style={{ width: `${c.freq}%` }} />
                  </div>
                  <div className="riskStatus" style={{ marginTop: 4 }}>
                    Mentioned in {c.freq}% of reviews
                  </div>
                </div>
                <div className={"riskScore " + c.tone} style={{ minWidth: 80, textAlign: "center", fontSize: 11 }}>
                  {c.verdict}
                </div>
              </div>
            ))}
          </div>
        </Panel>
      </section>
    </div>
  );
}
