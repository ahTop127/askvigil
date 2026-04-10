import { useNavigate } from "react-router";
import { Shield, ArrowRight } from "lucide-react";
import { Navigation } from "../components/Navigation";
import { scamTypes } from "@lib/constants/scamTypes";

export default function LearningPage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <Navigation />

      {/* Horizontal Scam Type Icons Navigation
      <nav className="bg-white/80 backdrop-blur-md border-b border-gray-200 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex items-center justify-start gap-6 overflow-x-auto py-3 scrollbar-hide">
            {scamTypes.map((scam) => {
              const Icon = scam.icon;
              return (
                <button
                  key={scam.id}
                  type="button"
                  onClick={() => {
                    const element = document.getElementById(scam.id);
                    element?.scrollIntoView({ behavior: 'smooth', block: 'center' });
                  }}
                  className="flex flex-col items-center gap-1 min-w-[50px] group cursor-pointer"
                >
                  <Icon className="w-5 h-5 text-black group-hover:text-[#255832] transition-colors" />
                  <span className="text-[11px] text-gray-600 whitespace-nowrap font-medium group-hover:text-black">
                    {scam.shortTitle}
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      </nav> */}

      {/* Main Content */}
      <main className="pt-10 pb-20">
        {/* Hero Title - Apple Style */}
        <div className="max-w-7xl mx-auto px-4 mb-16">
          <h1 className="text-6xl md:text-7xl font-semibold text-black mb-6 leading-tight tracking-tight">
            Learn about scams.
          </h1>
          <p className="text-2xl text-gray-700 max-w-3xl">
            Knowledge is your best defense. Explore different types of scams and learn how to protect yourself.
          </p>
        </div>

        {/* Scam Type Cards - Grid Layout */}
        <div className="max-w-7xl mx-auto px-4">
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {scamTypes.map((scam) => {
              const Icon = scam.icon;
              const v = scam.learning;

              return (
                <div 
                  key={scam.id} 
                  id={scam.id}
                  className="scroll-mt-32 group cursor-pointer"
                  onClick={() => navigate(`/learning/${scam.id}`)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      navigate(`/learning/${scam.id}`);
                    }
                  }}
                  role="button"
                  tabIndex={0}
                >
                  <div className="bg-white rounded-3xl overflow-hidden shadow-lg hover:shadow-2xl transition-all duration-300 hover:-translate-y-2 border-3 border-green-400">
                    {/* Top: Colored Background + Image */}
                    <div className={`relative h-64 bg-gradient-to-br ${v.bgColor} flex items-center justify-center`}>
                      <div className="w-full h-full flex items-center justify-center overflow-hidden">
                        <img 
                          src={v.image}
                          alt={scam.title}
                          className={`w-full h-full object-cover drop-shadow-2xl`}
                        />
                      </div>
                    </div>
                    {/* Bottom: White Background + Text */}
                    <div className="bg-white p-6 h-50">
                      <h3 className="text-2xl font-semibold text-[#255832] mb-3">
                        {scam.title}
                      </h3>
                      <p className="text-gray-700 leading-relaxed mb-4">
                        {v.description}
                      </p>
                      <div className="flex items-center justify-end">
                        <ArrowRight className="w-5 h-5 text-gray-400 group-hover:text-[#255832] group-hover:translate-x-1 transition-all" />
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Practice CTA */}
        <div className="max-w-7xl mx-auto px-4 mt-20">
          <div className="bg-[#669E84]/20 backdrop-blur-xl border border-[#669E84]/30 rounded-3xl p-8 md:p-12 text-center relative overflow-hidden shadow-lg animate-pulse-slow">
            {/* Decorative elements */}
            <div className="absolute top-0 right-0 w-48 h-48 bg-[#669E84]/10 rounded-full blur-3xl" />
            <div className="absolute bottom-0 left-0 w-56 h-56 bg-[#54A388]/10 rounded-full blur-3xl" />
            
            <div className="relative z-10">
              <h2 className="text-3xl md:text-4xl font-semibold text-[#255832] mb-4">
                Ready to test your knowledge?
              </h2>
              <p className="text-lg text-gray-700 mb-6 max-w-2xl mx-auto">
                Practice identifying scams with interactive scenarios and real-world examples.
              </p>
              <button
                onClick={() => navigate("/practice")}
                className="inline-flex items-center gap-2 bg-[#669E84] hover:bg-[#54A388] text-white px-8 py-4 rounded-full font-semibold transition-all shadow-lg hover:shadow-xl hover:scale-105"
              >
                Start practice
                <ArrowRight className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}