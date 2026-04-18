import { Navigation } from "@components/Navigation";
import { useScamDetection } from "./hooks/useScamDetection";
import { usePersonalization } from "./hooks/usePersonalization";
import { DetectionSection } from "./components/DetectionSection";
import { StatisticsSection } from "./components/StatisticsSection";
import { HowItWorks } from "./components/HowItWorks";
import { FAQSection } from "./components/FAQSection";
import { PersonalizationCard } from "./components/PersonalizationCard";

/**
 * Home landing: hero, detection hub, stats, how-it-works, FAQ, personalization.
 */
export default function HomePage() {
  const detection = useScamDetection();
  const personalization = usePersonalization();

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />

      <DetectionSection detection={detection} />

      <StatisticsSection />

      <HowItWorks />

      <FAQSection />

      <PersonalizationCard p={personalization} />
    </div>
  );
}
