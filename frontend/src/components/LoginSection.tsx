"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { Mail, Lock, Eye, EyeOff, ArrowRight } from "lucide-react";

export default function StudioAuthScreen() {
  const router = useRouter();
  const [showPw, setShowPw] = useState(false);

  return (
    <div className="min-h-screen w-screen bg-black">
      <div className="relative flex min-h-screen w-full items-center justify-center overflow-hidden bg-black shadow-[0_30px_120px_rgba(0,0,0,0.65)]">
        {/* animated red glow background - i tried group */}
        <div aria-hidden className="pointer-events-none absolute inset-0">
          <div className="absolute -left-24 top-[-8%] h-80 w-80 animate-[floatOne_18s_ease-in-out_infinite] rounded-full bg-red-500/20 blur-[120px]" />
          <div className="absolute right-[-8%] top-[12%] h-72 w-72 animate-[floatTwo_22s_ease-in-out_infinite] rounded-full bg-red-600/20 blur-[110px]" />
          <div className="absolute left-[12%] bottom-[8%] h-96 w-96 animate-[floatThree_24s_ease-in-out_infinite] rounded-full bg-red-500/15 blur-[140px]" />
          <div className="absolute right-[18%] bottom-[-10%] h-80 w-80 animate-[floatFour_20s_ease-in-out_infinite] rounded-full bg-red-700/20 blur-[130px]" />
          <div className="absolute left-[45%] top-[22%] h-64 w-64 animate-[floatFive_26s_ease-in-out_infinite] rounded-full bg-red-400/10 blur-[100px]" />
          <div className="absolute left-[58%] bottom-[18%] h-60 w-60 animate-[floatSix_19s_ease-in-out_infinite] rounded-full bg-red-500/15 blur-[110px]" />

          <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,transparent_0%,rgba(0,0,0,0.18)_55%,rgba(0,0,0,0.55)_100%)]" />
        </div>

        <div className="relative z-10 grid grid-cols-1 md:grid-cols-2">
          {/* left side */}
          <div className="p-8 sm:p-10 md:p-12">
            <p className="text-[12px] font-semibold tracking-[0.22em] text-[#E23333]">
              FOR MOVIE STUDIOS
            </p>

            <h1 className="mt-4 text-[40px] font-semibold leading-[1.05] text-white sm:text-[48px]">
              Know what the <span className="text-[#E23333]">world thinks</span> of your films.
            </h1>

            <p className="mt-6 max-w-md text-[15px] leading-relaxed text-white/55">
              Real-time YouTube review analysis, sentiment tracking, and creator
              credibility scoring — built for production studios.
            </p>

            <div className="mt-10 flex flex-wrap gap-3">
              {[
                "Sentiment Analysis",
                "Creator Risk",
                "Review Velocity",
                "Audience Mood",
              ].map((t) => (
                <span
                  key={t}
                  className="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-xs text-white/65 shadow-[inset_0_1px_0_rgba(255,255,255,0.08)]"
                >
                  {t}
                </span>
              ))}
            </div>
          </div>

          {/*  right side */}
          <div className="flex items-center p-8 sm:p-10 md:p-12">
            <div className="w-full">
              <div className="mx-auto mt-8 max-w-md">
                <h2 className="text-3xl font-semibold text-white">Welcome back</h2>
                <p className="mt-2 text-sm text-white/45">
                  Sign in to your studio account to continue.
                </p>

                <div className="mt-8 space-y-4">
                  {/* email entry */}
                  <div className="relative">
                    <Mail className="absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-white/30" />
                    <input
                      type="email"
                      placeholder="Work email address"
                      className="w-full rounded-2xl border border-white/10 bg-white/5 px-11 py-3.5 text-sm text-white placeholder:text-white/30 outline-none shadow-[inset_0_1px_0_rgba(255,255,255,0.08)] focus:border-white/20"
                    />
                  </div>

                  {/* password here */}
                  <div className="relative">
                    <Lock className="absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-white/30" />
                    <input
                      type={showPw ? "text" : "password"}
                      placeholder="Password"
                      className="w-full rounded-2xl border border-white/10 bg-white/5 px-11 py-3.5 pr-12 text-sm text-white placeholder:text-white/30 outline-none shadow-[inset_0_1px_0_rgba(255,255,255,0.08)] focus:border-white/20"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPw((v) => !v)}
                      className="absolute right-4 top-1/2 -translate-y-1/2 text-white/35 hover:text-white/60"
                    >
                      {showPw ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>

                  {/* you forgot your password? that's crazy */}
                  <div className="flex justify-end">
                    <button className="text-xs text-white/35 hover:text-white/60">
                      Forgot password?
                    </button>
                  </div>

                  
                  <button
                    onClick={() => router.push("/dashboard")}
                    className="group mt-2 w-full rounded-2xl bg-[#E23333] py-4 text-sm font-semibold text-white shadow-[0_18px_40px_rgba(226,51,51,0.25)] transition hover:brightness-105"
                  >
                    <span className="inline-flex items-center justify-center gap-2">
                      Sign In to Studio
                      <ArrowRight className="h-4 w-4 transition group-hover:translate-x-0.5" />
                    </span>
                  </button>

                  <p className="pt-4 text-center text-xs text-white/35">
                    Access is invite-only. Contact your admin if you need access.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="pointer-events-none absolute inset-0 rounded-[28px] ring-1 ring-white/10" />

        <style jsx>{`
          @keyframes floatOne {
            0%,
            100% {
              transform: translate3d(0, 0, 0) scale(1);
            }
            25% {
              transform: translate3d(90px, 40px, 0) scale(1.08);
            }
            50% {
              transform: translate3d(40px, 110px, 0) scale(0.96);
            }
            75% {
              transform: translate3d(120px, 20px, 0) scale(1.04);
            }
          }

          @keyframes floatTwo {
            0%,
            100% {
              transform: translate3d(0, 0, 0) scale(1);
            }
            25% {
              transform: translate3d(-70px, 60px, 0) scale(1.06);
            }
            50% {
              transform: translate3d(-120px, 20px, 0) scale(0.95);
            }
            75% {
              transform: translate3d(-50px, 100px, 0) scale(1.02);
            }
          }

          @keyframes floatThree {
            0%,
            100% {
              transform: translate3d(0, 0, 0) scale(1);
            }
            33% {
              transform: translate3d(60px, -70px, 0) scale(1.07);
            }
            66% {
              transform: translate3d(130px, -10px, 0) scale(0.94);
            }
          }

          @keyframes floatFour {
            0%,
            100% {
              transform: translate3d(0, 0, 0) scale(1);
            }
            30% {
              transform: translate3d(-80px, -50px, 0) scale(1.05);
            }
            60% {
              transform: translate3d(-20px, -120px, 0) scale(0.97);
            }
          }

          @keyframes floatFive {
            0%,
            100% {
              transform: translate3d(0, 0, 0) scale(1);
            }
            25% {
              transform: translate3d(-50px, 80px, 0) scale(1.04);
            }
            50% {
              transform: translate3d(70px, 30px, 0) scale(0.96);
            }
            75% {
              transform: translate3d(20px, -60px, 0) scale(1.03);
            }
          }

          @keyframes floatSix {
            0%,
            100% {
              transform: translate3d(0, 0, 0) scale(1);
            }
            20% {
              transform: translate3d(40px, -40px, 0) scale(1.02);
            }
            50% {
              transform: translate3d(-60px, -90px, 0) scale(1.08);
            }
            80% {
              transform: translate3d(-20px, 20px, 0) scale(0.95);
            }
          }
        `}</style>
      </div>
    </div>
  );
}