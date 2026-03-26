"use client";

import TrendsContent from "../../../../../components/dashboard/TrendsContent";
import NarrativesContent from "../../../../../components/dashboard/NarrativesContent";
import ClaimsContent from "../../../../../components/dashboard/ClaimsContent";
import React from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, TrendingUp, FileText, BadgeCheck, Star } from "lucide-react";

type TabKey = "trends" | "narratives" | "claims";

type MovieDetail = {
  movieid: string;
  studioid: string;
  title: string;
  year?: number | null;
  posterUrl?: string | null;
  rating?: number | null;
};

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

export default function MovieDetailPage() {
  const params = useParams();

  const studioId =
    typeof params?.studioId === "string" ? params.studioId : "";
  const movieId =
    typeof params?.movieId === "string" ? params.movieId : "";

  const [activeTab, setActiveTab] = React.useState<TabKey>("trends");
  const [movie, setMovie] = React.useState<MovieDetail | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    async function loadMovie() {
      if (!studioId || !movieId) {
        setError("Missing studioId or movieId in route.");
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);

        const baseUrl =
          process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8010";

        const res = await fetch(
          `${baseUrl}/api/v1/studios/${studioId}/movies/${movieId}`,
          { cache: "no-store" }
        );

        if (!res.ok) {
          throw new Error(`Failed to load movie: ${res.status}`);
        }

        const data: MovieDetail = await res.json();
        setMovie(data);
      } catch (err) {
        console.error(err);
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    }

    loadMovie();
  }, [studioId, movieId]);

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(120,0,0,0.35),_rgba(0,0,0,1)_45%)] text-white">
      <div className="mx-auto max-w-7xl px-6 py-8">
        <div className="mb-6">
          <Link
            href={`/studio/${studioId}/dashboard`}
            className="inline-flex items-center gap-2 text-sm text-white/70 hover:text-white"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Dashboard
          </Link>
        </div>

        {loading ? (
          <div className="rounded-3xl border border-white/10 bg-black/40 p-8">
            <p className="text-white/70">Loading movie...</p>
          </div>
        ) : error ? (
          <div className="rounded-3xl border border-red-500/30 bg-red-500/10 p-8">
            <p className="text-red-200">Error: {error}</p>
          </div>
        ) : !movie ? (
          <div className="rounded-3xl border border-white/10 bg-black/40 p-8">
            <p className="text-white/70">Movie not found.</p>
          </div>
        ) : (
          <>
            <div className="mb-8 rounded-3xl border border-white/10 bg-black/40 p-6 shadow-2xl">
              <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
                <div>
                  <p className="mb-2 text-sm uppercase tracking-[0.2em] text-red-400/80">
                    Movie Detail
                  </p>
                  <h1 className="text-4xl font-semibold tracking-tight">
                    {movie.title}
                  </h1>
                  <p className="mt-2 text-white/60">Movie ID: {movie.movieid}</p>
                </div>

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
              </div>
            </div>

            <section className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
              <div className="rounded-3xl border border-white/10 bg-black/50 p-6">
                {activeTab === "trends" && <TrendsContent />}
                {activeTab === "narratives" && <NarrativesContent />}
                {activeTab === "claims" && <ClaimsContent />}
              </div>

              <div className="rounded-3xl border border-white/10 bg-black/50 p-6">
                <h3 className="mb-4 text-xl font-semibold">Movie Snapshot</h3>

                <div className="mb-5 aspect-[3/4] w-full rounded-2xl border border-white/10 bg-black flex items-center justify-center overflow-hidden text-6xl text-white/20">
                  {movie.posterUrl ? (
                    <img
                      src={movie.posterUrl}
                      alt={movie.title}
                      className="h-full w-full object-cover"
                    />
                  ) : (
                    <span>Poster</span>
                  )}
                </div>

                <div className="space-y-3 text-sm text-white/70">
                  <div className="rounded-2xl bg-white/5 p-4">
                    <span className="text-white font-medium">Title:</span> {movie.title}
                  </div>

                  <div className="rounded-2xl bg-white/5 p-4">
                    <span className="text-white font-medium">Movie ID:</span> {movie.movieid}
                  </div>

                  <div className="rounded-2xl bg-white/5 p-4">
                    <span className="text-white font-medium">Studio ID:</span> {movie.studioid}
                  </div>

                  <div className="rounded-2xl bg-white/5 p-4 flex items-center gap-2">
                    <Star className="h-4 w-4 text-white" />
                    <span className="text-white font-medium">Rating:</span>{" "}
                    {movie.rating ?? "N/A"}
                  </div>
                </div>
              </div>
            </section>
          </>
        )}
      </div>
    </main>
  );
}