import { memo, useCallback } from "react";
import { motion } from "motion/react";
import { useNavigate } from "react-router";
import { Shield, FolderOpen } from "lucide-react";

/**
 * Feature narrative blocks with CTAs into product areas.
 */
export const HowItWorks = memo(function HowItWorks() {
  const navigate = useNavigate();

  const goLearning = useCallback(() => {
    navigate("/learning");
  }, [navigate]);

  const goGuidance = useCallback(() => {
    navigate("/guidance");
  }, [navigate]);

  const goCases = useCallback(() => {
    navigate("/cases");
  }, [navigate]);

  return (
    <section className="py-24 bg-gradient-to-br from-[#F5F7F9] to-white relative overflow-hidden">
      <div className="absolute top-0 right-0 w-96 h-96 bg-secondary/5 rounded-full blur-3xl" />
      <div className="absolute bottom-0 left-0 w-96 h-96 bg-[#FFA00E]/5 rounded-full blur-3xl" />

      <div className="max-w-7xl mx-auto px-4 relative z-10">
        <div className="text-center mb-20">
          <h2 className="font-bold text-[#213034] mb-4 text-[48px]">
            How it works
          </h2>
          <p className="text-xl text-gray-600">
            Four simple ways to stay safe online
          </p>
        </div>

        <div className="space-y-24">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <motion.div
              initial={{ opacity: 0, x: -60 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true, margin: "-100px" }}
              transition={{ duration: 0.7, ease: "easeOut" }}
              className="order-2 lg:order-1"
            >
              <h3 className="text-3xl font-bold text-[#213034] mb-4">
                Check suspicious content
              </h3>
              <p className="text-lg text-gray-600 mb-6 leading-relaxed">
                Check messages, images, URLs, or QR codes for potential scams
                instantly. Our intelligent system analyzes content patterns and
                provides immediate risk assessments to help you make safer
                decisions.
              </p>
            </motion.div>
            <motion.div
              initial={{ opacity: 0, scale: 0.9, x: 60 }}
              whileInView={{ opacity: 1, scale: 1, x: 0 }}
              viewport={{ once: true, margin: "-100px" }}
              transition={{ duration: 0.7, delay: 0.2, ease: "easeOut" }}
              className="order-1 lg:order-2"
            >
              <img
                src="https://images.unsplash.com/photo-1526045612212-70caf35c14df?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxwZXJzb24lMjBjaGVja2luZyUyMHBob25lJTIwbWVzc2FnZSUyMHNlY3VyaXR5fGVufDF8fHx8MTc3NTAyNDU5NXww&ixlib=rb-4.1.0&q=80&w=1080"
                alt="Person checking phone for security"
                className="w-full h-80 object-cover rounded-2xl shadow-2xl hover:shadow-3xl transition-shadow duration-300"
                loading="lazy"
              />
            </motion.div>
          </div>

          <div className="grid lg:grid-cols-2 gap-12 items-center lg:pl-20">
            <motion.div
              initial={{ opacity: 0, scale: 0.9, x: -60 }}
              whileInView={{ opacity: 1, scale: 1, x: 0 }}
              viewport={{ once: true, margin: "-100px" }}
              transition={{ duration: 0.7, delay: 0.2, ease: "easeOut" }}
            >
              <img
                src="https://images.unsplash.com/photo-1712885609367-3d49c2e0fae8?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxzaGllbGQlMjBwcm90ZWN0aW9uJTIwc2FmZXR5JTIwZ3VpZGFuY2V8ZW58MXx8fHwxNzc1MDI0NTk1fDA&ixlib=rb-4.1.0&q=80&w=1080"
                alt="Shield protection and guidance"
                className="w-full h-80 object-cover rounded-2xl shadow-2xl hover:shadow-3xl transition-shadow duration-300"
                loading="lazy"
              />
            </motion.div>
            <motion.div
              initial={{ opacity: 0, x: 60 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true, margin: "-100px" }}
              transition={{ duration: 0.7, ease: "easeOut" }}
            >
              <h3 className="text-3xl font-bold text-[#213034] mb-4">
                Get help after a scam
              </h3>
              <p className="text-lg text-gray-600 mb-6 leading-relaxed">
                View scam-type guidance and learn what to do after being
                targeted or scammed. Access step-by-step instructions tailored
                to different scam scenarios to minimize damage and protect
                yourself.
              </p>
              <button
                type="button"
                onClick={goGuidance}
                className="inline-flex items-center gap-2 bg-gradient-to-r from-[#E0AB71] to-[#D09A5F] hover:from-[#D09A5F] hover:to-[#C08850] text-white px-6 py-3 rounded-xl font-medium transition-all shadow-lg hover:shadow-xl hover:scale-105"
              >
                <Shield className="w-5 h-5" aria-hidden />
                View guidance
              </button>
            </motion.div>
          </div>

          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <motion.div
              initial={{ opacity: 0, x: -60 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true, margin: "-100px" }}
              transition={{ duration: 0.7, ease: "easeOut" }}
              className="order-2 lg:order-1"
            >
              <h3 className="text-3xl font-bold text-[#213034] mb-4">
                Learn and stay aware
              </h3>
              <p className="text-lg text-gray-600 mb-6 leading-relaxed">
                Explore scam knowledge, learning content, and practice
                questions. Build your scam detection skills through interactive
                modules, real case studies, and expert insights.
              </p>
              <button
                type="button"
                onClick={goLearning}
                className="inline-flex items-center gap-2 bg-gradient-to-r from-[#213034] to-[#3D5660] hover:from-[#3D5660] hover:to-[#213034] text-white px-6 py-3 rounded-xl font-medium transition-all shadow-lg hover:shadow-xl hover:scale-105"
              >
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
                    d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
                  />
                </svg>
                Start learning
              </button>
            </motion.div>
            <motion.div
              initial={{ opacity: 0, scale: 0.9, x: 60 }}
              whileInView={{ opacity: 1, scale: 1, x: 0 }}
              viewport={{ once: true, margin: "-100px" }}
              transition={{ duration: 0.7, delay: 0.2, ease: "easeOut" }}
              className="order-1 lg:order-2"
            >
              <img
                src="https://images.unsplash.com/photo-1771408427146-09be9a1d4535?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxzdHVkZW50JTIwbGVhcm5pbmclMjBvbmxpbmUlMjBlZHVjYXRpb258ZW58MXx8fHwxNzc0OTYxNzk5fDA&ixlib=rb-4.1.0&q=80&w=1080"
                alt="Student learning online"
                className="w-full h-80 object-cover rounded-2xl shadow-2xl hover:shadow-3xl transition-shadow duration-300"
                loading="lazy"
              />
            </motion.div>
          </div>

          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <motion.div
              initial={{ opacity: 0, x: -60 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true, margin: "-100px" }}
              transition={{ duration: 0.7, ease: "easeOut" }}
              className="order-2 lg:order-1"
            >
              <h3 className="text-3xl font-bold text-[#213034] mb-4">
                Browse real scam cases
              </h3>
              <p className="text-lg text-gray-600 mb-6 leading-relaxed">
                Explore organised examples from reliable online sources. Filter
                by scam type or communication channel to see how similar scams
                unfold on the platforms you use every day. Open a case to read
                full context, tactics, and warning signs so you can recognise
                patterns faster next time.
              </p>
              <button
                type="button"
                onClick={goCases}
                className="inline-flex items-center gap-2 bg-gradient-to-r from-[#E0AB71] to-[#D09A5F] hover:from-[#D09A5F] hover:to-[#C08850] text-white px-6 py-3 rounded-xl font-medium transition-all shadow-lg hover:shadow-xl hover:scale-105"
              >
                <FolderOpen className="w-5 h-5" aria-hidden />
                Browse cases
              </button>
            </motion.div>
            <motion.div
              initial={{ opacity: 0, scale: 0.9, x: 60 }}
              whileInView={{ opacity: 1, scale: 1, x: 0 }}
              viewport={{ once: true, margin: "-100px" }}
              transition={{ duration: 0.7, delay: 0.2, ease: "easeOut" }}
              className="order-1 lg:order-2"
            >
              <img
                src="https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixlib=rb-4.1.0&q=80&w=1080"
                alt="Reviewing documents and case examples"
                className="w-full h-80 object-cover rounded-2xl shadow-2xl hover:shadow-3xl transition-shadow duration-300"
                loading="lazy"
              />
            </motion.div>
          </div>
        </div>
      </div>
    </section>
  );
});
