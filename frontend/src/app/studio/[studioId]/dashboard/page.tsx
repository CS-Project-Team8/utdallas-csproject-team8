"use client";

import React, { useMemo, useState } from "react";
import {
  Search,
  Bell,
  Menu,
  Film,
  Star,
  TrendingUp,
  ThumbsUp,
} from "lucide-react";

/** notes to self: 
 * wire it later:
 * - Replace `mockStudio`, `mockMetrics`, `mockRecentMovies` with real API data.
 */

type Studio = {
  id: string;
  name: string; 
  brandAccent: string; 
  initials: string; 
  logoTextLeft?: string; 
  logoTextRight?: string;
};

type Metrics = {
  totalMovies: number;
  avgRating: number; 
  creatorRiskScore: number; 
  profit?: number; 
  extraLabel?: string; 
  extraValue?: number | string;
};

type Movie = {
  id: string;
  title: string;
  year?: number;
};

export default function StudioDashboard() {
  
  const mockStudio: Studio = {
    id: "studio_1",
    name: "Marvel Studios",
    brandAccent: "#E23333",
    initials: "AS",
    logoTextLeft: "MARVEL",
    logoTextRight: "STUDIOS",
  };

  const mockMetrics: Metrics = {
    totalMovies: 34,
    avgRating: 7.8,
    creatorRiskScore: 23,
    profit: 12500000, 
    extraLabel: "Something else here?",
    extraValue: 0,
  };

  const mockRecentMovies: Movie[] = [
    { id: "m1", title: "Movie 1" },
    { id: "m2", title: "Movie 2" },
    { id: "m3", title: "Movie 3" },
    { id: "m4", title: "Movie 4" },
    { id: "m5", title: "Movie 5" },
  ];

  const [query, setQuery] = useState("");

  const accent = mockStudio.brandAccent;

  const kpis = useMemo(
    () => [
      {
        label: "Total Movies",
        value: mockMetrics.totalMovies,
        Icon: Film,
      },
      {
        label: "Avg rating",
        value: mockMetrics.avgRating,
        Icon: Star,
      },
      {
        label: "Creator risk score",
        value: mockMetrics.creatorRiskScore,
        Icon: TrendingUp,
      },
      {
        label: mockMetrics.extraLabel ?? "Profit",
        value:
          mockMetrics.extraLabel && mockMetrics.extraValue !== undefined
            ? mockMetrics.extraValue
            : mockMetrics.profit !== undefined
            ? `$${formatCompact(mockMetrics.profit)}`
            : "—",
        Icon: ThumbsUp,
      },
    ],
    [mockMetrics]
  );

  
  const movieBlocks = useMemo(() => mockRecentMovies.slice(0, 5), [mockRecentMovies]);

  return (
    <div className="h-screen w-screen bg-[#0B0B0B] text-white">
     
      <div className="h-full">
        <div className="relative h-full w-full overflow-hidden bg-black shadow-[0_30px_120px_rgba(0,0,0,0.65)] ring-1 ring-white/10">
         
          <div
            aria-hidden
            className="pointer-events-none absolute inset-0 opacity-80"
            style={{
              backgroundImage: `radial-gradient(1200px 700px at 20% 20%, ${hexToRgba(
                accent,
                0.28
              )}, transparent 60%),
              radial-gradient(900px 600px at 80% 30%, rgba(255,255,255,0.06), transparent 55%),
              linear-gradient(to right, rgba(255,255,255,0.06), transparent 20%, transparent 80%, rgba(255,255,255,0.05))`,
            }}
          />

          {/* content */}
          <div className="relative flex h-full flex-col">
           
            <header className="flex items-center justify-between gap-4 px-6 py-5">
              {/* left: studio logo area */}
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-3">
                  
                  <div className="flex items-center gap-2">
                    <div
                      className="rounded-[6px] px-2.5 py-1 text-sm font-extrabold tracking-wide text-white"
                      style={{ backgroundColor: accent }}
                    >
                      {mockStudio.logoTextLeft ?? mockStudio.name.split(" ")[0].toUpperCase()}
                    </div>
                    <div className="text-xl font-semibold tracking-wide">
                      {mockStudio.logoTextRight ?? mockStudio.name.split(" ").slice(1).join(" ").toUpperCase()}
                    </div>
                  </div>
                </div>
              </div>

            
              <div className="hidden md:flex w-full max-w-2xl items-center gap-3">
                <button
                  className="rounded-xl border border-white/10 bg-white/5 p-2.5 text-white/70 hover:text-white"
                  aria-label="Menu"
                >
                  <Menu className="h-5 w-5" />
                </button>

                <div className="relative w-full">
                  <Search className="absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-white/40" />
                  <input
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Search movies"
                    className="w-full rounded-2xl border border-white/10 bg-white/5 py-3 pl-11 pr-4 text-sm text-white placeholder:text-white/35 outline-none shadow-[inset_0_1px_0_rgba(255,255,255,0.08)] focus:border-white/20"
                  />
                </div>
              </div>

             
              <div className="flex items-center gap-3">
                <button
                  className="rounded-xl border border-white/10 bg-white/5 p-2.5 text-white/70 hover:text-white"
                  aria-label="Notifications"
                >
                  <Bell className="h-5 w-5" />
                </button>

                <div className="flex h-11 w-11 items-center justify-center rounded-full border border-white/10 bg-white/5 text-sm font-semibold shadow-[inset_0_1px_0_rgba(255,255,255,0.08)]">
                  {mockStudio.initials}
                </div>
              </div>
            </header>

            <div className="px-6">
              <div className="h-px w-full bg-white/10" />
            </div>

            <main className="flex-1 overflow-y-auto px-6 py-6">
              
              <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
                {kpis.map(({ label, value, Icon }) => (
                  <div
                    key={label}
                    className="relative flex items-center gap-4 rounded-[18px] border border-white/10 bg-white/5 px-6 py-5 shadow-[inset_0_1px_0_rgba(255,255,255,0.08)]"
                  >
                    <div
                      className="flex h-12 w-12 items-center justify-center rounded-[16px]"
                      style={{ backgroundColor: hexToRgba(accent, 0.25) }}
                    >
                      <Icon className="h-6 w-6" style={{ color: accent }} />
                    </div>

                    <div className="min-w-0">
                      <div className="text-sm text-white/55">{label}</div>
                      <div className="mt-1 text-lg font-semibold text-white">
                        {value}
                      </div>
                    </div>
                  </div>
                ))}
              </section>

              {/* Recent movies blocks area */}
              <section className="mt-6">
                <div className="grid grid-cols-1 gap-6 lg:grid-cols-4">
                  
                  <div className="lg:col-span-1">
                    <MoviePlaceholderCard accent={accent} hoverAccent />
                  </div>

                  {/* 3 blocks to the right */}
                  <div className="lg:col-span-3">
                    <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
                      <MoviePlaceholderCard accent={accent} hoverAccent />
                      <MoviePlaceholderCard accent={accent} hoverAccent/>
                      <MoviePlaceholderCard accent={accent} hoverAccent />
                    </div>
                  </div>

                  <div className="lg:col-span-1">
                    <MoviePlaceholderCard accent={accent} hoverAccent />
                  </div>

                 
                </div>

              </section>
            </main>
          </div>
        </div>
      </div>
    </div>
  );
}

function MoviePlaceholderCard({
  accent,
  hoverAccent,
}: {
  accent: string;
  hoverAccent?: boolean;
}) {
  return (
    <div
      className={[
        "cursor-pointer group relative h-90 w-full rounded-[22px] border bg-white/5",
        "border-white/10 shadow-[inset_0_1px_0_rgba(255,255,255,0.08)]",
      ].join(" ")}
        style={
            hoverAccent
            ? {
                borderColor: "rgba(255,255,255,0.10)",
                }
            : undefined
        }
    >

      {hoverAccent && (
        <div
          className="pointer-events-none absolute inset-0 rounded-[22px] opacity-0 transition-opacity duration-200 group-hover:opacity-100"
          style={{
            boxShadow: `0 0 0 1px ${hexToRgba(accent, 0.9)}, 0 25px 60px rgba(0,0,0,0.55)`,
            border: `1px solid ${hexToRgba(accent, 0.9)}`,
          }}
        />
      )}

      {/* empty block content */}
      <div className="absolute inset-0 rounded-[22px] bg-gradient-to-b from-white/0 to-black/10" />

      {/* little floating circle */}
      <div className="absolute left-1/2 top-1/2 flex h-12 w-12 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full bg-[#2E3440] text-white/80 shadow-[0_10px_25px_rgba(0,0,0,0.6)] ring-1 ring-white/10">
        A
      </div>
    </div>
  );
}

/* helpers */
function hexToRgba(hex: string, alpha: number) {
  const h = hex.replace("#", "").trim();
  const full = h.length === 3 ? h.split("").map((c) => c + c).join("") : h;
  const num = parseInt(full, 16);
  const r = (num >> 16) & 255;
  const g = (num >> 8) & 255;
  const b = num & 255;
  return `rgba(${r},${g},${b},${alpha})`;
}

function formatCompact(n: number) {
 
  const abs = Math.abs(n);
  if (abs >= 1_000_000_000) return `${(n / 1_000_000_000).toFixed(1)}B`;
  if (abs >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (abs >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return `${n}`;
}