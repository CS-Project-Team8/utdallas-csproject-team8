"use client";
import { useParams } from "next/navigation";
import React, { useMemo, useState, useEffect } from "react";
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
  posterUrl?: string;
  summary?: string;
  sentimentLabel?: string;
  engagementLabel?: string;
};

type DashboardResponse = {
  studio: Studio;
  metrics: Metrics;
  recentMovies: Movie[];
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

  const [dashboardData, setDashboardData] = useState<DashboardResponse | null>(null);
  const [movieResults, setMovieResults] = useState<Movie[] | null>(null);
  const [loadingDashboard, setLoadingDashboard] = useState(true);
  const [loadingSearch, setLoadingSearch] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const params = useParams();
  const studioId = params.studioId as string;
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;

  const [query, setQuery] = useState("");

  useEffect(() => {
    const loadDashboard = async () => {
      try {
        setLoadingDashboard(true);
        setError(null);

        const res = await fetch(
            `${apiBaseUrl}/api/v1/studios/${studioId}`,
            { cache: "no-store" }
        );

        if (!res.ok) {
          throw new Error(`Failed to load dashboard: ${res.status}`);
        }

        const data: DashboardResponse = await res.json();
        setDashboardData(data);
      } catch (err) {
        console.error(err);
        setError("Failed to load dashboard data.");
      } finally {
        setLoadingDashboard(false);
      }
    };

    if (!apiBaseUrl) {
      setError("Missing NEXT_PUBLIC_API_BASE_URL");
      setLoadingDashboard(false);
      return;
    }

    if (!studioId) {
      return;
    }

    loadDashboard();
  }, [apiBaseUrl, studioId]);

  useEffect(() => {
    if (!apiBaseUrl || !studioId) return;

    const timeout = setTimeout(async () => {
      try {
        setLoadingSearch(true);

        const res = await fetch(
            `${apiBaseUrl}/api/v1/studios/${studioId}/movies/search?query=${encodeURIComponent(query)}&limit=12`,
            { cache: "no-store" }
        );

        if (!res.ok) {
          throw new Error(`Search failed: ${res.status}`);
        }

        const data: Movie[] = await res.json();
        setMovieResults(data);
      } catch (err) {
        console.error(err);
        setMovieResults(null);
      } finally {
        setLoadingSearch(false);
      }
    }, 250);

    return () => clearTimeout(timeout);
  }, [apiBaseUrl, studioId, query]);

  const studio = dashboardData?.studio ?? mockStudio;
  const metrics = dashboardData?.metrics ?? mockMetrics;
  const fallbackMovies = dashboardData?.recentMovies ?? mockRecentMovies;

  const displayedMovies =
      query.trim().length > 0
          ? movieResults ?? []
          : fallbackMovies;

  const accent = studio.brandAccent;

  const kpis = useMemo(
      () => [
        {
          label: "Total Movies",
          value: metrics.totalMovies,
          Icon: Film,
        },
        {
          label: "Avg rating",
          value: metrics.avgRating,
          Icon: Star,
        },
        {
          label: "Creator risk score",
          value: metrics.creatorRiskScore,
          Icon: TrendingUp,
        },
        {
          label: metrics.extraLabel ?? "Profit",
          value:
              metrics.extraLabel && metrics.extraValue !== undefined
                  ? metrics.extraValue
                  : metrics.profit !== undefined
                      ? `$${formatCompact(metrics.profit)}`
                      : "—",
          Icon: ThumbsUp,
        },
      ],
      [metrics]
  );


  const movieBlocks = useMemo(() => displayedMovies.slice(0, 5), [displayedMovies]);

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
                      {studio.logoTextLeft ?? studio.name.split(" ")[0].toUpperCase()}
                    </div>
                    <div className="text-xl font-semibold tracking-wide">
                      {studio.logoTextRight ?? studio.name.split(" ").slice(1).join(" ").toUpperCase()}
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
                  {studio.initials}
                </div>
              </div>
            </header>

            <div className="px-6">
              <div className="h-px w-full bg-white/10" />
            </div>

            <main className="flex-1 overflow-y-auto px-6 py-6">
              {loadingDashboard && (
                  <div className="mb-4 rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white/70">
                    Loading dashboard...
                  </div>
              )}

              {error && (
                  <div className="mb-4 rounded-xl border border-red-400/20 bg-red-500/10 px-4 py-3 text-sm text-red-200">
                    {error}
                  </div>
              )}

              {loadingSearch && query.trim().length > 0 && (
                  <div className="mb-4 rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white/70">
                    Searching movies...
                  </div>
              )}
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
                <div className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-4">
                  {movieBlocks.map((movie) => (
                      <MoviePlaceholderCard
                          key={movie.id}
                          accent={accent}
                          hoverAccent
                          movie={movie}
                      />
                  ))}
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
                                movie,
                              }: {
  accent: string;
  hoverAccent?: boolean;
  movie?: Movie;
}) {
  const [imgFailed, setImgFailed] = useState(false);

  useEffect(() => {
    setImgFailed(false);
  }, [movie?.posterUrl]);

  const showPoster = Boolean(movie?.posterUrl) && !imgFailed;

  return (
      <div
          className={[
            "cursor-pointer group relative h-90 w-full overflow-hidden rounded-[22px] border bg-white/5",
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
        {showPoster ? (
            <img
                src={movie!.posterUrl}
                alt={movie?.title ?? "Movie poster"}
                className="absolute inset-0 h-full w-full object-cover"
                onError={() => setImgFailed(true)}
            />
        ) : (
            <div className="absolute inset-0 bg-black">
              <div
                  className="absolute inset-x-0 top-0 h-1"
                  style={{ backgroundColor: accent }}
              />
              <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(255,255,255,0.08),transparent_35%)]" />
              <div className="flex h-full w-full flex-col items-center justify-center px-6 text-center">
                <div className="text-3xl font-extrabold uppercase tracking-[0.12em] text-white">
                  {movie?.title ?? "Untitled"}
                </div>
                {movie?.year && (
                    <div className="mt-2 text-sm tracking-[0.2em] text-white/50">
                      {movie.year}
                    </div>
                )}
              </div>
            </div>
        )}

        <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/30 to-transparent" />

        {hoverAccent && (
            <div
                className="pointer-events-none absolute inset-0 rounded-[22px] opacity-0 transition-opacity duration-200 group-hover:opacity-100"
                style={{
                  boxShadow: `0 0 0 1px ${hexToRgba(accent, 0.9)}, 0 25px 60px rgba(0,0,0,0.55)`,
                  border: `1px solid ${hexToRgba(accent, 0.9)}`,
                }}
            />
        )}

        <div className="absolute inset-x-0 bottom-0 p-4">
          {showPoster && (
              <>
                <div className="text-lg font-semibold text-white">
                  {movie?.title ?? "No title"}
                </div>

                {movie?.year && (
                    <div className="mt-1 text-sm text-white/70">{movie.year}</div>
                )}
              </>
          )}

          {movie?.summary && (
              <p className={`${showPoster ? "mt-2" : ""} line-clamp-3 text-sm text-white/75`}>
                {movie.summary}
              </p>
          )}

          <div className="mt-3 flex flex-wrap gap-2">
            {movie?.sentimentLabel && (
                <span className="rounded-full bg-white/10 px-2.5 py-1 text-xs text-white/85">
              {movie.sentimentLabel}
            </span>
            )}
            {movie?.engagementLabel && (
                <span className="rounded-full bg-white/10 px-2.5 py-1 text-xs text-white/85">
              {movie.engagementLabel}
            </span>
            )}
          </div>
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