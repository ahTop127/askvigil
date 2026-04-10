import { useNavigate } from "react-router";
import { AlertCircle, Home } from "lucide-react";
import { Navigation } from "../components/Navigation";

export default function NotFoundPage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-white">
      <Navigation />
      
      <main className="pt-20 pb-20">
        <div className="max-w-3xl mx-auto px-4 text-center">
          <AlertCircle className="w-20 h-20 text-[#FFA00E] mx-auto mb-6" />
          
          <h1 className="text-6xl font-semibold text-black mb-4">
            404
          </h1>
          
          <h2 className="text-3xl font-semibold text-gray-800 mb-4">
            Page not found
          </h2>
          
          <p className="text-xl text-gray-600 mb-8">
            The page you're looking for doesn't exist or has been moved.
          </p>
          
          <button
            onClick={() => navigate("/")}
            className="inline-flex items-center gap-2 bg-[#FFA00E] hover:bg-[#E69000] text-white px-8 py-4 rounded-full font-semibold transition-all shadow-lg hover:shadow-xl hover:scale-105"
          >
            <Home className="w-5 h-5" />
            Back to Home
          </button>
        </div>
      </main>
    </div>
  );
}
