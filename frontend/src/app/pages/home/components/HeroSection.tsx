import { memo } from "react";
import { motion } from "motion/react";

export interface HeroSectionProps {
  heroImage: string;
  onScrollToCheck: () => void;
  titleLine1: string;
  titleLine2: string;
  subtitle: string;
  ctaLabel: string;
  imageAlt: string;
}

/**
 * Full-viewport hero with background image and primary CTA.
 */
export const HeroSection = memo(function HeroSection({
  heroImage,
  onScrollToCheck,
  titleLine1,
  titleLine2,
  subtitle,
  ctaLabel,
  imageAlt,
}: HeroSectionProps) {
  return (
    <section className="relative min-h-[90vh] overflow-hidden">
      <div className="absolute inset-0">
        <img
          src={heroImage}
          alt={imageAlt}
          className="w-full h-full object-cover blur-[3px]"
        />
      </div>

      <div className="max-w-7xl mx-auto px-4 pt-12 pb-8 relative z-10">
        <motion.div
          initial={{ opacity: 0, x: -50 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="text-white text-left max-w-2xl py-12"
        >
          <h1 className="text-6xl font-bold mb-6 leading-tight text-white drop-shadow-lg">
            {titleLine1}
            <br />
            {titleLine2}
          </h1>
          <p className="text-xl text-white/95 mb-8 leading-relaxed drop-shadow-md">
            {subtitle}
          </p>
          <button
            type="button"
            onClick={onScrollToCheck}
            className="inline-flex items-center gap-2 bg-white/90 backdrop-blur-sm hover:bg-white text-slate-900 px-8 py-4 rounded-full font-semibold transition-all shadow-lg hover:shadow-xl"
          >
            {ctaLabel}
            <svg
              className="w-5 h-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              aria-hidden
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 7l5 5m0 0l-5 5m5-5H6"
              />
            </svg>
          </button>
        </motion.div>
      </div>
    </section>
  );
});
