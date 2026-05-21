import { Navigation } from "@components/Navigation";
import { useScamDetection } from "./hooks/useScamDetection";
import { DetectionSection } from "./components/DetectionSection";
import { StatisticsSection } from "./components/StatisticsSection";
import { HowItWorks } from "./components/HowItWorks";
import { FAQSection } from "./components/FAQSection";

/**
 * Home landing: hero, detection hub, stats, how-it-works, FAQ.
 */
export default function HomePage() {
  const detection = useScamDetection();

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />

      <DetectionSection detection={detection} />

      <StatisticsSection />

      <HowItWorks />

      <FAQSection />
    </div>
  );
}
