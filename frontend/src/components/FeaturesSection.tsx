import { ScrollReveal } from "./ScrollReveal";
import { BarChart3, TrendingUp, MessageSquare, Zap, Shield, Globe } from "lucide-react";

const features = [
  {
    icon: BarChart3,
    title: "Sentiment Breakdown",
    description: "See exactly how audiences feel about your film across thousands of YouTube reviews, broken down by topic and emotion.",
  },
  {
    icon: TrendingUp,
    title: "Trend Tracking",
    description: "Monitor review sentiment over time — from opening weekend buzz to long-tail word-of-mouth impact.",
  },
  {
    icon: MessageSquare,
    title: "Review Aggregation",
    description: "Automatically pull and categorize video reviews from top film critics and audience channels.",
  },
  {
    icon: Zap,
    title: "Real-Time Alerts",
    description: "Get notified instantly when a major review drops or sentiment shifts significantly for your title.",
  },
  {
    icon: Shield,
    title: "Competitive Intel",
    description: "Compare your film's reception against competing releases in the same genre and window.",
  },
  {
    icon: Globe,
    title: "Global Coverage",
    description: "Track reviews across 40+ languages and regional YouTube markets for worldwide reception insights.",
  },
];

export const FeaturesSection = () => {
  return (
    <section className="relative py-32 px-6 bg-black ">
      {/* divider */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-2/3 h-px bg-[linear-gradient(90deg,transparent,hsl(0_72%_51%_/_0.5),transparent)]" />
      {/* noise part I wanted to design something here but changed it */}
      <div className="absolute inset-0 bg-noise opacity-40" />

      <div className="relative z-10 max-w-6xl mx-auto">
        
        {/* header */}
        <ScrollReveal className="text-center mb-20">
          <span className="text-xs font-medium tracking-[0.2em] uppercase text-red-500 mb-4 block">
            Capabilities
          </span>

          <h2 className="text-3xl md:text-5xl font-bold font-display mb-4 leading-[1.1] text-white">
            Every review, every insight,<br />
            <span className="bg-clip-text text-transparent bg-[linear-gradient(135deg,_hsl(0_72%_51%),_hsl(0_100%_70%))]">
              one dashboard
            </span>
          </h2>

          <p className="text-white/60 max-w-xl mx-auto">
            From premiere night to streaming release — understand how YouTube shapes your film's narrative.
          </p>
        </ScrollReveal>

        {/* little cards */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, i) => (
            <ScrollReveal key={feature.title} delay={i * 80} animation="fade-up">
              
              <div className="
                group
                h-full
                flex flex-col
                justify-between
                bg-white/5
                border border-white/10
                rounded-2xl
                p-6
                transition-all duration-300
                hover:border-red-500
                hover:bg-white/10
                active:scale-[0.98]
              ">
                
                {/* iconnn */}
                <div className="w-10 h-10 rounded-xl bg-red-500/10 border border-red-500/20 flex items-center justify-center mb-4 group-hover:shadow-[0_0_20px_-8px_hsl(0_72%_51%_/0.3)] transition-all duration-300">
                  <feature.icon className="w-5 h-5 text-red-500" />
                </div>

                {/* text part */}
                <div>
                  <h3 className="font-display font-semibold text-lg mb-2 text-white">
                    {feature.title}
                  </h3>
                  <p className="text-white/60 text-sm leading-relaxed">
                    {feature.description}
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