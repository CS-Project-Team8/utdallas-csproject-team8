"use client";
import React from "react";
import {
  Panel, MetricCard, LegendDot, RiskRow,
  BreakRow, SignalBar, EngagedItem, TopicBar, MiniStat,
} from "./shared";

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

function getColor(value) {
  // 0-50: red to yellow, 50-100: yellow to green
  if (value <= 50) {
    const t = value / 50;
    const r = 255;
    const g = Math.round(t * 204); // 0 → 204
    return `rgb(${r}, ${g}, 0)`;
  } else {
    const t = (value - 50) / 50;
    const r = Math.round(255 * (1 - t)); // 255 → 0
    const g = Math.round(204 + t * 51);  // 204 → 255
    return `rgb(${r}, ${g}, 0)`;
  }
}

export default function OverviewPage() {
  const [donutVal, setDonutVal] = React.useState(0);

  React.useEffect(() => {
    const target = 68;
    const duration = 1000;
    let startTime = null;
    const easeOut = (t) => 1 - Math.pow(1 - t, 5);

    const animate = (timestamp) => {
      if (!startTime) startTime = timestamp;
      const elapsed = timestamp - startTime;
      const progress = Math.min(elapsed / duration, 1);
      setDonutVal(Math.round(easeOut(progress) * target));
      if (progress < 1) requestAnimationFrame(animate);
    };

    requestAnimationFrame(animate);
  }, []);

  return (
    <div className="pageWrap">
      <section className="metricRow">
        <MetricCard label="TOTAL REVIEWS" value="2,847" sub="+124 this week" />
        <MetricCard label="AVERAGE SENTIMENT" value="78%"   sub="Positive" />
        <MetricCard label="TOTAL VIEWS"   value="42.6M" sub="Across all reviews" />
        <MetricCard label="TOTAL LIKES"   value="3.2M"  sub="+180k this month" />
      </section>

      <section className="grid">
        <div className="colLeft">
          <Panel
            title="Sentiment Timeline"
            subtitle="Reviews sentiment & engagement over time"
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

          <Panel title="Top Sentiment Words" subtitle="Most common across all reviews">
            <div className="chips">
              {[
                "masterpiece","iconic","revolutionary","overrated","brilliant",
                "boring","game-changer","epic","disappointing","legendary",
                "nostalgic","predictable","stunning","groundbreaking","meh",
              ].map((t) => (
                <span key={t} className="chip">{t}</span>
              ))}
            </div>
          </Panel>

          <Panel title="Creator Risk Assessment" subtitle="Credibility analysis of top reviewers">
            <div className="list">
              <RiskRow name="FilmCriticX"    status="High Risk" score="87" tone="high" />
              <RiskRow name="MovieMaven"     status="Moderate"  score="64" tone="mid" />
              <RiskRow name="CinephileDaily" status="Low Risk"  score="12" tone="low" />
              <RiskRow name="PopcornReviews" status="High Risk" score="91" tone="high" />
              <RiskRow name="SceneByScene"   status="Low Risk"  score="9"  tone="low" />
            </div>
          </Panel>
        </div>

        <div className="colRight">
          <Panel title="Sentiment Breakdown" subtitle="Overall audience mood distribution">
            <div className="split">
              <div className="donutPlaceholder">
               <div
                className="donutRing"
                  style={{background: `conic-gradient(${getColor(donutVal)} 0 ${donutVal}%, rgba(255,255,255,0.12) ${donutVal}% 100%)`}}
              >
              <div className="donutCenter">
                <div className="donutValue" style={{ color: getColor(donutVal) }}>{donutVal}%</div>
              <div className="donutLabel">Positive</div>
              </div>
            </div>
              </div>
              <div className="breakdownList">
                <BreakRow label="Positive" value="68%" />
                <BreakRow label="Neutral"  value="18%" muted />
                <BreakRow label="Negative" value="14%" muted />
              </div>
            </div>
            <div className="divider" />
            <div className="signals">
              <div className="signalsTitle">AUDIENCE MOOD SIGNALS</div>
              <SignalBar label="Excitement"     value={82} />
              <SignalBar label="Nostalgia"      value={67} />
              <SignalBar label="Satisfaction"   value={74} />
              <SignalBar label="Disappointment" value={18} muted />
              <SignalBar label="Hype"           value={91} />
            </div>
          </Panel>

          <Panel title="Review Velocity" subtitle="New reviews per week since release">
            <div className="barChartPlaceholder">
              {Array.from({ length: 8 }).map((_, i) => (
                <AnimatedBar key={i} targetHeight={30 + i * 7} delay={i * 60} />
              ))}
            </div>
            <div className="barLabels">
              <span>Week 1</span>
              <span>Week 8</span>
            </div>
          </Panel>

          <Panel title="Most Engaged Reviews" subtitle="Highest-performing review videos">
            <div className="engagedList">
              <EngagedItem title="Iron Man Changed Everything — Here's Why" meta="FilmCriticX • 2 days ago" />
              <EngagedItem title="The REAL reason Iron Man works so well"   meta="MovieMaven • 1 week ago" />
              <EngagedItem title="Rewatching Iron Man in 2026..."           meta="SceneByScene • 2 weeks ago" />
            </div>
          </Panel>
        </div>
      </section>

      <section className="bottomSection">
        <Panel title="Key Discussion Topics" subtitle="Most discussed aspects from review transcripts">
          <div className="topicBars">
            <TopicBar label="RDJ Acting"    value={92} />
            <TopicBar label="Visual FX"     value={78} />
            <TopicBar label="Origin Story"  value={66} />
            <TopicBar label="Humor"         value={58} />
            <TopicBar label="Villain"       value={52} />
            <TopicBar label="Soundtrack"    value={44} />
            <TopicBar label="Action Scenes" value={40} />
            <TopicBar label="Post-Credits"  value={34} />
          </div>
          <div className="miniStats">
            <MiniStat label="RDJ Acting"   value="95%" hint="sentiment" />
            <MiniStat label="Visual FX"    value="82%" hint="sentiment" />
            <MiniStat label="Origin Story" value="88%" hint="sentiment" />
            <MiniStat label="Humor"        value="91%" hint="sentiment" />
          </div>
        </Panel>
      </section>
    </div>
  );
}