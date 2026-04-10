import { useNavigate } from "react-router";
import { Shield, ArrowRight } from "lucide-react";
import { Navigation } from "../components/Navigation";
import { scamTypes } from "@lib/constants/scamTypes";

export default function GuidancePage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <Navigation />

      {/* Horizontal Scam Type Icons Navigation
      <nav className="bg-white/80 backdrop-blur-md border-b border-gray-200 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex items-center justify-start gap-6 overflow-x-auto scrollbar-hide py-3">
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
                  <Icon className="w-5 h-5 text-black group-hover:text-[#D89654] transition-colors" />
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
            Get help after a scam.
          </h1>
          <p className="text-2xl text-gray-700 max-w-3xl">
            Immediate guidance for what to do next. Select your situation to get step-by-step support.
          </p>
        </div>

        {/* Scam Type Cards - Grid Layout */}
        <div className="max-w-7xl mx-auto px-4">
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {scamTypes.map((scam) => {
              const Icon = scam.icon;
              const v = scam.guidance;

              return (
                <div 
                  key={scam.id} 
                  id={scam.id}
                  className="scroll-mt-32 group cursor-pointer"
                  onClick={() => navigate(`/guidance/${scam.id}`)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      navigate(`/guidance/${scam.id}`);
                    }
                  }}
                  role="button"
                  tabIndex={0}
                >
                  <div className="bg-white rounded-3xl overflow-hidden shadow-lg hover:shadow-2xl transition-all duration-300 hover:-translate-y-2 border-3 border-orange-400">
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
                      <h3 className="text-2xl font-semibold text-[#D89654] mb-3">
                        {scam.title}
                      </h3>
                      <p className="text-gray-700 leading-relaxed mb-4">
                        {v.description}
                      </p>
                      <div className="flex items-center justify-end">
                        <ArrowRight className="w-5 h-5 text-gray-400 group-hover:text-[#D89654] group-hover:translate-x-1 transition-all" />
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Emergency CTA */}
        <div className="max-w-7xl mx-auto px-4 mt-20">
          <div className="bg-[#EAA866]/20 backdrop-blur-xl border border-[#EAA866]/30 rounded-3xl p-8 md:p-12 text-center relative overflow-hidden shadow-lg">
            {/* Decorative elements */}
            <div className="absolute top-0 right-0 w-48 h-48 bg-[#EAA866]/10 rounded-full blur-3xl" />
            <div className="absolute bottom-0 left-0 w-56 h-56 bg-[#D89654]/10 rounded-full blur-3xl" />
            
            <div className="relative z-10">
              <Shield className="w-16 h-16 text-[#D89654] mx-auto mb-4" />
              <h2 className="text-3xl md:text-4xl font-semibold text-[#D89654] mb-4">
                Need immediate help?
              </h2>
              <p className="text-lg text-gray-700 mb-6 max-w-2xl mx-auto">
                If you've lost money or shared sensitive information, contact the authorities immediately.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
                <div className="bg-white rounded-2xl px-6 py-4 shadow-md">
                  <p className="text-sm text-gray-600 mb-1">Malaysia Police Hotline</p>
                  <p className="text-2xl font-bold text-[#D89654]">999</p>
                </div>
                <div className="bg-white rounded-2xl px-6 py-4 shadow-md">
                  <p className="text-sm text-gray-600 mb-1">NSRC Scam Hotline</p>
                  <p className="text-2xl font-bold text-[#D89654]">997</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}