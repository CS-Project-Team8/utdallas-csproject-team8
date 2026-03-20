import { ScrollReveal } from "@/components/ScrollReveal";
import { Search, Cpu, BarChart3, Bell } from "lucide-react";

const steps = [
  {
    icon: Search,
    step: "01",
    title: "We find the reviews",
    description:
      "ReelPulse continuously crawls YouTube for reviews mentioning your film titles — critics, audiences, reaction channels, and more.",
  },
  {
    icon: Cpu,
    step: "02",
    title: "AI does the analysis",
    description:
      "Our models extract sentiment, key talking points, audience demographics, and emotional reactions from every video.",
  },
  {
    icon: BarChart3,
    step: "03",
    title: "You see the picture",
    description:
      "Clean dashboards surface what matters — overall reception, scene-by-scene feedback, and audience segments that love (or hate) your film.",
  },
  {
    icon: Bell,
    step: "04",
    title: "Stay ahead of the curve",
    description:
      "Automated alerts and weekly digests ensure your marketing and distribution teams always know the narrative around your title.",
  },
];

export const HowItWorksSection = () => {
  return (
    <section className="relative py-32 px-6 bg-black">
      {/*  divider */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-2/3 h-px bg-[linear-gradient(90deg,transparent,hsl(0_72%_51%_/_0.5),transparent)]" />

      {/* the same noise here too */}
      <div className="absolute inset-0 bg-noise opacity-40" />

      <div className="relative z-10 max-w-5xl mx-auto">
        <ScrollReveal className="text-center mb-20">
          <span className="text-xs font-medium tracking-[0.2em] uppercase text-red-500 mb-4 block">
            How it works
          </span>

          <h2 className="text-3xl md:text-5xl font-bold font-display leading-[1.1] text-white">
            From raw footage to
            <br />
            <span className="bg-clip-text text-transparent bg-[linear-gradient(135deg,_hsl(0_72%_51%),_hsl(0_100%_70%))]">
              actionable intelligence
            </span>
          </h2>
        </ScrollReveal>

        <div className="space-y-6">
          {steps.map((step, i) => (
            <ScrollReveal
              key={step.step}
              animation={i % 2 === 0 ? "slide-left" : "slide-right"}
              delay={i * 100}
            >
              <div className="group flex items-start gap-6 md:gap-10 rounded-2xl border border-white/10 bg-white/5 px-6 py-8 transition-all duration-300 ">
                <div className="shrink-0">
                  <div className="w-14 h-14 rounded-2xl bg-red-500/10 border border-red-500/20 flex items-center justify-center group-hover:shadow-[0_0_20px_-8px_hsl(0_72%_51%_/0.3)] transition-all duration-500">
                    <step.icon className="w-6 h-6 text-red-500" />
                  </div>
                </div>

                <div className="flex-1">
                  <span className="text-xs font-mono text-red-500/70 tracking-wider">
                    {step.step}
                  </span>
                  <h3 className="font-display text-xl font-semibold mt-1 mb-2 text-white">
                    {step.title}
                  </h3>
                  <p className="text-white/60 text-sm leading-relaxed max-w-lg">
                    {step.description}
                  </p>
                </div>
              </div>
            </ScrollReveal>
          ))}
        </div>
      </div>
    </section>
  );
};