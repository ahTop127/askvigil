import { memo } from "react";
import { motion } from "motion/react";
import { CheckCircle } from "lucide-react";

/**
 * Social proof metrics grid beside marketing copy.
 */
export const StatisticsSection = memo(function StatisticsSection() {
  return (
    <section className="py-20 bg-gradient-to-br from-[#F5F7F9] to-white">
      <div className="max-w-7xl mx-auto px-4">
        <div className="grid lg:grid-cols-2 gap-16 items-center">
          <motion.div
            initial={{ opacity: 0, x: -50 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true, margin: "-100px" }}
            transition={{ duration: 0.6 }}
          >
            <h2 className="font-bold text-[#213034] mb-6 leading-tight text-[36px]">
              Protecting Malaysians from Online Scams
            </h2>

            <p className="text-xl text-gray-600 mb-8 leading-relaxed">
              We help young adults stay safe online, detect suspicious content,
              and make informed decisions with intelligent, easy-to-use scam
              detection tools.
            </p>

            <div className="flex flex-wrap gap-4 mb-8">
              <div className="flex items-center gap-2 text-gray-700">
                <CheckCircle className="w-5 h-5 text-secondary" aria-hidden />
                <span>Instant Detection</span>
              </div>
              <div className="flex items-center gap-2 text-gray-700">
                <CheckCircle className="w-5 h-5 text-secondary" aria-hidden />
                <span>Expert Guidance</span>
              </div>
              <div className="flex items-center gap-2 text-gray-700">
                <CheckCircle className="w-5 h-5 text-secondary" aria-hidden />
                <span>Free to Use</span>
              </div>
            </div>
          </motion.div>

          <div className="grid grid-cols-2 gap-4">
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-100px" }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="bg-white rounded-2xl p-6 border border-gray-200 hover:shadow-lg transition-shadow"
            >
              <div className="text-sm text-gray-500 mb-3">Users Protected</div>
              <div className="text-4xl font-bold text-[#213034] mb-1">
                12,500+
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-100px" }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="bg-gradient-to-br from-[#FFF4E6] to-[#FFF8F0] rounded-2xl p-6 border border-orange-200 hover:shadow-lg transition-shadow"
            >
              <div className="text-sm text-gray-500 mb-3">Checks Daily</div>
              <div className="text-4xl font-bold text-[#213034] mb-1">2K+</div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-100px" }}
              transition={{ duration: 0.5, delay: 0.3 }}
              className="bg-gradient-to-br from-[#F0F9F6] to-[#F5FBF8] rounded-2xl p-6 border border-emerald-200 hover:shadow-lg transition-shadow"
            >
              <div className="text-sm text-gray-500 mb-3">Links Analysed</div>
              <div className="text-4xl font-bold text-[#213034] mb-1">
                5,00+
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-100px" }}
              transition={{ duration: 0.5, delay: 0.4 }}
              className="bg-white rounded-2xl p-6 border border-gray-200 hover:shadow-lg transition-shadow"
            >
              <div className="text-sm text-gray-500 mb-3">Scams Detected</div>
              <div className="text-4xl font-bold text-[#213034] mb-1">98%</div>
            </motion.div>
          </div>
        </div>
      </div>
    </section>
  );
});
