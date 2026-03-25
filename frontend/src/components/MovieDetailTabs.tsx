"use client";

import React from "react";
import { TrendingUp, FileText, BadgeCheck } from "lucide-react";

export type TabKey = "trends" | "narratives" | "claims";

function TabButton({
  active,
  onClick,
  icon,
  label,
}: {
  active: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  label: string;
}) {
  return (
    <button
      onClick={onClick}
      className={`inline-flex items-center gap-2 rounded-xl border px-4 py-2 text-sm font-medium transition ${
        active
          ? "border-red-500 bg-red-600/20 text-white"
          : "border-white/10 bg-white/5 text-white/70 hover:bg-white/10 hover:text-white"
      }`}
    >
      {icon}
      {label}
    </button>
  );
}

export default function MovieDetailTabs({
  activeTab,
  setActiveTab,
}: {
  activeTab: TabKey;
  setActiveTab: (tab: TabKey) => void;
}) {
  return (
    <div className="flex flex-wrap gap-3">
      <TabButton
        active={activeTab === "trends"}
        onClick={() => setActiveTab("trends")}
        icon={<TrendingUp className="h-4 w-4" />}
        label="Trends"
      />
      <TabButton
        active={activeTab === "narratives"}
        onClick={() => setActiveTab("narratives")}
        icon={<FileText className="h-4 w-4" />}
        label="Narratives"
      />
      <TabButton
        active={activeTab === "claims"}
        onClick={() => setActiveTab("claims")}
        icon={<BadgeCheck className="h-4 w-4" />}
        label="Claims"
      />
    </div>
  );
}