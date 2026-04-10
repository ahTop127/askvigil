import { useCallback } from "react";
import { Navigation } from "@components/Navigation";
import { UI_TEXT } from "@lib/constants/text";
import heroImage from "@assets/malaysianhomepage.png";
import { useScamDetection } from "./hooks/useScamDetection";
import { usePersonalization } from "./hooks/usePersonalization";
import { HeroSection } from "./components/HeroSection";
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

  const scrollToCheck = useCallback(() => {
    document.getElementById("check-section")?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />

      <HeroSection
        heroImage={heroImage}
        onScrollToCheck={scrollToCheck}
        titleLine1={UI_TEXT.hero.titleLine1}
        titleLine2={UI_TEXT.hero.titleLine2}
        subtitle={UI_TEXT.hero.subtitle}
        ctaLabel={UI_TEXT.hero.cta}
        imageAlt={UI_TEXT.hero.heroImageAlt}
      />

      <DetectionSection detection={detection} />

      <StatisticsSection />

      <HowItWorks onScrollToCheck={scrollToCheck} />

      <FAQSection />

      <PersonalizationCard p={personalization} />
    </div>
  );
}
