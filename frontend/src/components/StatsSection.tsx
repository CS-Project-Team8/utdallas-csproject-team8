"use client";
import { ScrollReveal } from "@/components/ScrollReveal";
import { useEffect, useRef, useState } from "react";

const stats = [
  { value: 2400000, suffix: "+", label: "Reviews Analyzed", format: "compact" },
  { value: 847, suffix: "", label: "Studios Served", format: "number" },
  { value: 42, suffix: "", label: "Languages Covered", format: "number" },
  { value: 98.7, suffix: "%", label: "Sentiment Accuracy", format: "decimal" },
];

const AnimatedNumber = ({ value, suffix, format }: { value: number; suffix: string; format: string }) => {
  const [display, setDisplay] = useState("0");
  const ref = useRef<HTMLSpanElement>(null);
  const hasAnimated = useRef(false);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !hasAnimated.current) {
          hasAnimated.current = true;
          const duration = 1500;
          const start = performance.now();

          const animate = (now: number) => {
            const elapsed = now - start;
            const progress = Math.min(elapsed / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            const current = eased * value;

            if (format === "compact") {
              if (current >= 1000000) setDisplay(`${(current / 1000000).toFixed(1)}M`);
              else if (current >= 1000) setDisplay(`${Math.floor(current / 1000)}K`);
              else setDisplay(Math.floor(current).toString());
            } else if (format === "decimal") {
              setDisplay(current.toFixed(1));
            } else {
              setDisplay(Math.floor(current).toLocaleString());
            }

            if (progress < 1) requestAnimationFrame(animate);
          };
          requestAnimationFrame(animate);
        }
      },
      { threshold: 0.5 }
    );

    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, [value, format]);

  return (
    <span ref={ref} className="tabular-nums">
      {display}{suffix}
    </span>
  );
};

export const StatsSection = () => {
  return (
    <section className="relative py-32 px-6 bg-black">
      
      {/* divider */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-2/3 h-px bg-[linear-gradient(90deg,transparent,hsl(0_72%_51%_/_0.5),transparent)]" />

      {/* glow and the noise */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_600px_400px_at_50%_0%,hsl(0_72%_51%_/_0.08),transparent)]" />
      <div className="absolute inset-0 bg-noise opacity-40" />

      <div className="relative z-10 max-w-5xl mx-auto">
        
        {/* header */}
        <ScrollReveal className="text-center mb-16">
          <span className="text-xs font-medium tracking-[0.2em] uppercase text-red-500 mb-4 block">
            By the numbers
          </span>

          <h2 className="text-3xl md:text-5xl font-bold font-display leading-[1.1] text-white">
            Trusted by the industry's
            <br />
            <span className="bg-clip-text text-transparent bg-[linear-gradient(135deg,_hsl(0_72%_51%),_hsl(0_100%_70%))]">
              biggest names
            </span>
          </h2>
        </ScrollReveal>

        {/* stats section */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          {stats.map((stat, i) => (
            <ScrollReveal key={stat.label} delay={i * 100} animation="fade-up">
              
              <div className="text-center p-6 rounded-2xl bg-white/5 border border-white/10">
                
                <div className="text-3xl md:text-4xl font-bold font-display bg-clip-text text-transparent bg-[linear-gradient(135deg,_hsl(0_72%_51%),_hsl(0_100%_70%))] mb-2">
                  <AnimatedNumber value={stat.value} suffix={stat.suffix} format={stat.format} />
                </div>

                <div className="text-sm text-white/60">
                  {stat.label}
                </div>

              </div>

            </ScrollReveal>
          ))}
        </div>

        {/* logos  */}
        <ScrollReveal className="mt-16" delay={200}>
          <p className="text-center text-xs text-white/40 tracking-widest uppercase mb-8">
            Trusted by leading studios worldwide
          </p>

          <div className="flex items-center justify-center gap-12 flex-wrap opacity-30">
            {["Universal Pictures", "Marvel Studios", "Columbia Pictures", "DreamWorks", "ESPN"].map((name) => (
              <span key={name} className="font-display text-lg font-semibold tracking-wider text-white">
                {name}
              </span>
            ))}
          </div>
        </ScrollReveal>

      </div>
    </section>
  );
};