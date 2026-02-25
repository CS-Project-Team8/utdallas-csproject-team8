"use client";

import React, { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Mail, Lock, Eye, EyeOff, ArrowRight } from "lucide-react";

export default function StudioAuthScreen() {
  const router = useRouter();
  const [mode, setMode] = useState<"signin" | "signup">("signin");
  const [showPw, setShowPw] = useState(false);

  const isSignIn = mode === "signin";

  const headline = useMemo(
    () => (
      <>
        <span className="text-white">Know what the </span>
        <span className="text-[#E23333]">world thinks</span>
        <span className="text-white"> of your films.</span>
      </>
    ),
    []
  );

  return (
    <div className="min-h-screen w-screen">
      <div className="relative w-full min-h-screen overflow-hidden bg-[#0B0B0B] shadow-[0_30px_120px_rgba(0,0,0,0.65)] flex justify-center items-center">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 opacity-80"
          style={{
            backgroundImage:
              "radial-gradient(1200px 700px at 20% 30%, rgba(226,51,51,0.28), transparent 60%), radial-gradient(900px 600px at 75% 40%, rgba(255,255,255,0.06), transparent 55%), linear-gradient(to right, rgba(255,255,255,0.06), transparent 20%, transparent 80%, rgba(255,255,255,0.05))",
          }}
        />

        <div className="relative grid grid-cols-1 md:grid-cols-2">
          {/* left side */}
          <div className="p-8 sm:p-10 md:p-12">
            <p className="text-[12px] tracking-[0.22em] text-[#E23333] font-semibold">
              FOR MOVIE STUDIOS
            </p>

            <h1 className="mt-4 text-[40px] leading-[1.05] sm:text-[48px] font-semibold">
              {headline}
            </h1>

            <p className="mt-6 max-w-md text-white/55 text-[15px] leading-relaxed">
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

          {/* right side */}
          <div className="p-8 sm:p-10 md:p-12 flex items-center">
            <div className="w-full">
              {/* tabs */}
              <div className="mx-auto flex w-full max-w-md rounded-[16px] border border-white/10 bg-white/5 p-1 shadow-[inset_0_1px_0_rgba(255,255,255,0.08)]">
                <button
                  onClick={() => setMode("signin")}
                  className={[
                    "cursor-pointer flex-1 rounded-[14px] py-2.5 text-sm font-semibold transition",
                    isSignIn
                      ? "bg-[#E23333] text-white shadow-[0_10px_30px_rgba(226,51,51,0.35)]"
                      : "text-white/55 hover:text-white/75",
                  ].join(" ")}
                >
                  Sign In
                </button>
                <button
                  onClick={() => setMode("signup")}
                  className={[
                    "cursor-pointer flex-1 rounded-[14px] py-2.5 text-sm font-semibold transition",
                    !isSignIn
                      ? "bg-[#E23333] text-white shadow-[0_10px_30px_rgba(226,51,51,0.35)]"
                      : "text-white/55 hover:text-white/75",
                  ].join(" ")}
                >
                  Create Account
                </button>
              </div>

              {/* titke */}
              <div className="mx-auto mt-8 max-w-md">
                <h2 className="text-3xl font-semibold text-white">
                  {isSignIn ? "Welcome back" : "Create your account"}
                </h2>
                <p className="mt-2 text-sm text-white/45">
                  {isSignIn
                    ? "Sign in to your studio account to continue."
                    : "Start tracking reviews and narratives in minutes."}
                </p>

                {/* inputs */}
                <div className="mt-8 space-y-4">
                  {/* email */}
                  <div className="relative">
                    <Mail className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-white/30" />
                    <input
                      type="email"
                      placeholder="Work email address"
                      className="w-full rounded-2xl border border-white/10 bg-white/5 px-11 py-3.5 text-sm text-white placeholder:text-white/30 outline-none shadow-[inset_0_1px_0_rgba(255,255,255,0.08)] focus:border-white/20 focus:bg-white/7"
                    />
                  </div>

                  {/* password */}
                  <div className="relative">
                    <Lock className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-white/30" />
                    <input
                      type={showPw ? "text" : "password"}
                      placeholder="Password"
                      className="w-full rounded-2xl border border-white/10 bg-white/5 px-11 py-3.5 pr-12 text-sm text-white placeholder:text-white/30 outline-none shadow-[inset_0_1px_0_rgba(255,255,255,0.08)] focus:border-white/20 focus:bg-white/7"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPw((v) => !v)}
                      className="cursor-pointer absolute right-4 top-1/2 -translate-y-1/2 text-white/35 hover:text-white/60"
                      aria-label={showPw ? "Hide password" : "Show password"}
                    >
                      {showPw ? (
                        <EyeOff className="h-4 w-4" />
                      ) : (
                        <Eye className="h-4 w-4" />
                      )}
                    </button>
                  </div>

                  {/* fogot password */}
                  {isSignIn && (
                    <div className="flex justify-end">
                      <button className="text-xs text-white/35 hover:text-white/60 cursor-pointer">
                        Forgot password?
                      </button>
                    </div>
                  )}

                  {/* primary cta*/}
                  <button
                    onClick={() => {
                      if (isSignIn) {
                        router.push("/dashboard");
                      } else {
                        router.push("/dashboard"); // you can change later for signup flow
                      }
                    }}
                    className="cursor-pointer group mt-2 w-full rounded-2xl bg-[#E23333] py-4 text-sm font-semibold text-white shadow-[0_18px_40px_rgba(226,51,51,0.25)] transition hover:brightness-105 active:brightness-95"
                  >                    
                  <span className="inline-flex items-center justify-center gap-2">
                      {isSignIn ? "Sign In to Studio" : "Create Studio Account"}
                      <ArrowRight className="h-4 w-4 transition group-hover:translate-x-0.5" />
                    </span>
                  </button>

                  

                  

                  {/* bottom part */}
                  <p className="pt-4 text-center text-xs text-white/35">
                    {isSignIn ? "Don't have an account? " : "Already have an account? "}
                    <button
                      onClick={() => setMode(isSignIn ? "signup" : "signin")}
                      className="font-semibold text-[#E23333] hover:brightness-110 cursor-pointer"
                    >
                      {isSignIn ? "Sign up" : "Sign in"}
                    </button>
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* highlight*/}
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 rounded-[28px] ring-1 ring-white/10"
        />
      </div>
    </div>
  );
}