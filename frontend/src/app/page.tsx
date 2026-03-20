import LoginSection from "@/components/LoginSection";
import { FeaturesSection } from "@/components/FeaturesSection";
import { HowItWorksSection } from "@/components/HowItWorksSection";
import { StatsSection } from "@/components/StatsSection";


const Index = () => {
  return (
    <div className="min-h-screen bg-background overflow-x-hidden">
      <LoginSection />
      <FeaturesSection />
      <HowItWorksSection />
      <StatsSection />
    </div>
  );
};

export default Index;
