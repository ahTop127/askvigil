import { useNavigate, useLocation } from "react-router";
import { ArrowLeft } from "lucide-react";

type BackButtonProps = {
  fallbackTo?: string;
};

export function BackButton({ fallbackTo }: BackButtonProps) {
  const navigate = useNavigate();
  const location = useLocation();

  const handleBack = () => {
    if (fallbackTo) {
      navigate(fallbackTo);
      return;
    }

    const path = location.pathname;

    if (path.startsWith("/guidance/")) {
      navigate("/guidance");
      return;
    }

    if (path.startsWith("/learning/")) {
      navigate("/learning");
      return;
    }

    navigate(-1);
  };

  return (
    <div className="bg-white border-b border-gray-200 py-3 sticky top-[73px] z-40">
      <div className="max-w-7xl mx-auto px-4">
        <button
          onClick={handleBack}
          className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
          <span className="font-medium">Back</span>
        </button>
      </div>
    </div>
  );
}
