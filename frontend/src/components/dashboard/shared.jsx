"use client";
import React from "react";

export function MetricCard({ label, value, sub }) {
  const [display, setDisplay] = React.useState("0");

  React.useEffect(() => {
    // strip non-numeric chars to get the number, keep suffix like M, k, %
    const match = value.match(/^([+-]?)([0-9,.]+)([A-Za-z%]*)/);
    if (!match) { setDisplay(value); return; }

    const prefix = match[1];
    const num = parseFloat(match[2].replace(/,/g, ""));
    const suffix = match[3];
    const hasComma = match[2].includes(",");

    const duration = 1200;
    const stepTime = 16;
    const steps = duration / stepTime;
    const increment = num / steps;
    let current = 0;
    let frame = 0;

    const timer = setInterval(() => {
      frame++;
      current = Math.min(current + increment, num);

      let formatted;
      if (hasComma) {
        formatted = Math.round(current).toLocaleString();
      } else if (suffix === "%" || Number.isInteger(num)) {
        formatted = Math.round(current).toString();
      } else {
        formatted = current.toFixed(1);
      }

      setDisplay(prefix + formatted + suffix);

      if (frame >= steps) clearInterval(timer);
    }, stepTime);

    return () => clearInterval(timer);
  }, [value]);

  return (
    <div className="metricCard">
      <div className="metricLabel">{label}</div>
      <div className="metricValue">{display}</div>
      <div className="metricSub">{sub}</div>
    </div>
  );
}

export function Panel({ title, subtitle, rightTag, children }) {
  return (
    <section className="panel">
      <div className="panelHeader">
        <div>
          <div className="panelTitle">{title}</div>
          {subtitle ? <div className="panelSubtitle">{subtitle}</div> : null}
        </div>
        {rightTag ? <div className="panelRight">{rightTag}</div> : null}
      </div>
      <div className="panelBody">{children}</div>
    </section>
  );
}

export function LegendDot({ label, isMuted }) {
  return (
    <div className={"legendDot " + (isMuted ? "muted" : "")}>
      <span className="dot" />
      <span>{label}</span>
    </div>
  );
}

export function RiskRow({ name, status, score, tone }) {
  return (
    <div className="riskRow">
      <div className="riskLeft">
        <div className="riskAvatar">{name.slice(0, 2).toUpperCase()}</div>
        <div className="riskMeta">
          <div className="riskName">{name}</div>
          <div className="riskStatus">{status}</div>
        </div>
      </div>
      <div className={"riskScore " + tone}>{score}</div>
    </div>
  );
}

export function BreakRow({ label, value, muted }) {
  return (
    <div className={"breakRow " + (muted ? "muted" : "")}>
      <span className="breakLabel">{label}</span>
      <span className="breakValue">{value}</span>
    </div>
  );
}

export function SignalBar({ label, value, muted }) {
  const [width, setWidth] = React.useState(0);

  React.useEffect(() => {
    const duration = 1000;
    let startTime = null;
    const easeOut = (t) => 1 - Math.pow(1 - t, 5);

    const animate = (timestamp) => {
      if (!startTime) startTime = timestamp;
      const elapsed = timestamp - startTime;
      const progress = Math.min(elapsed / duration, 1);
      setWidth(Math.round(easeOut(progress) * value));
      if (progress < 1) requestAnimationFrame(animate);
    };

    requestAnimationFrame(animate);
  }, [value]);

  return (
    <div className={"signalRow " + (muted ? "muted" : "")}>
      <div className="signalTop">
        <span>{label}</span>
        <span>{width}%</span>
      </div>
      <div className="signalTrack">
        <div className="signalFill" style={{ width: `${width}%` }} />
      </div>
    </div>
  );
}

export function EngagedItem({ title, meta }) {
  return (
    <div className="engagedItem">
      <div className="thumb" />
      <div className="engagedText">
        <div className="engagedTitle">{title}</div>
        <div className="engagedMeta">{meta}</div>
      </div>
    </div>
  );
}

export function TopicBar({ label, value }) {
  const [width, setWidth] = React.useState(0);

  React.useEffect(() => {
    const duration = 1000;
    let startTime = null;
    const easeOut = (t) => 1 - Math.pow(1 - t, 5);

    const animate = (timestamp) => {
      if (!startTime) startTime = timestamp;
      const elapsed = timestamp - startTime;
      const progress = Math.min(elapsed / duration, 1);
      setWidth(Math.round(easeOut(progress) * value));
      if (progress < 1) requestAnimationFrame(animate);
    };

    requestAnimationFrame(animate);
  }, [value]);

  return (
    <div className="topicRow">
      <div className="topicLabel">{label}</div>
      <div className="topicTrack">
        <div className="topicFill" style={{ width: `${width}%` }} />
      </div>
    </div>
  );
}

export function MiniStat({ label, value, hint }) {
  return (
    <div className="miniStat">
      <div className="miniLabel">{label}</div>
      <div className="miniValue">{value}</div>
      <div className="miniHint">{hint}</div>
    </div>
  );
}