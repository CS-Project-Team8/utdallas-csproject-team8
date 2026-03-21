import React from "react";
import { Panel, MetricCard, LegendDot, SignalBar } from "../components/shared";

function AnimatedBar({ targetHeight, delay }) {
  const [height, setHeight] = React.useState(0);

  React.useEffect(() => {
    const timeout = setTimeout(() => {
      const duration = 1000;
      let startTime = null;
      const easeOut = (t) => 1 - Math.pow(1 - t, 5);

      const animate = (timestamp) => {
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

  return <div className="bar" style={{ height: `${height}%` }} />;
}

export default function TrendsPage() {
  return (
    <div className="pageWrap">
      <section className="metricRow">
        <MetricCard label="TRENDING TOPICS" value="14"      sub="+3 this week" />
        <MetricCard label="PEAK WEEK"        value="Week 6"  sub="1,204 reviews" />
        <MetricCard label="GROWTH RATE"      value="+22%"   sub="vs last month" />
        <MetricCard label="VIRAL REVIEWS"    value="7"      sub="Over 500k views" />
      </section>

      <section className="grid">
        <div className="colLeft">
          <Panel
            title="Sentiment Timeline"
            subtitle="Positive vs. negative trend over time"
            rightTag={<span className="tag tagGood">+5% this year</span>}
          >
            <div className="chartPlaceholder">
              <div className="chartHeader">
                <LegendDot label="Positive" />
                <LegendDot label="Negative" isMuted />
              </div>
              <div className="fakeChartArea">
                <div className="fakeLine" />
                <div className="fakeMarker" />
              </div>
            </div>
          </Panel>

          <Panel title="Review Volume Over Time" subtitle="Weekly review count since release">
            <div className="barChartPlaceholder">
              {[40, 55, 70, 90, 85, 100, 95, 60].map((h, i) => (
                <AnimatedBar key={i} targetHeight={h} delay={i * 60} />
              ))}
            </div>
            <div className="barLabels">
              <span>Week 1</span>
              <span>Week 8</span>
            </div>
          </Panel>
        </div>

        <div className="colRight">
          <Panel title="Rising Signals" subtitle="Audience emotions gaining momentum">
            <div className="signals">
              <SignalBar label="Hype"           value={91} />
              <SignalBar label="Excitement"     value={82} />
              <SignalBar label="Satisfaction"   value={74} />
              <SignalBar label="Nostalgia"      value={67} />
              <SignalBar label="Disappointment" value={18} muted />
            </div>
          </Panel>

          <Panel title="Trending Sentiment Words" subtitle="Breakout terms this week">
            <div className="chips">
              {["iconic","game-changer","revolutionary","legendary","masterpiece","epic","groundbreaking","stunning"].map((t) => (
                <span key={t} className="chip">{t}</span>
              ))}
            </div>
          </Panel>
        </div>
      </section>
    </div>
  );
}