import { useNavigate, useLocation } from "react-router";
import Logo from "@assets/AskVigilLogo.png";

export function Navigation() {
  const navigate = useNavigate();
  const location = useLocation();

  const isActive = (path: string) => {
    if (path === "/guidance") {
      return location.pathname.startsWith("/guidance");
    }
    if (path === "/learning") {
      return location.pathname.startsWith("/learning");
    }
    return location.pathname === path;
  };

  return (
    <header className="backdrop-blur-md bg-transparent border-b border-white/10 sticky top-0 z-50">
      <div className="w-full px-4 py-5">
        <div className="flex items-center gap-8">
          {/* Logo - Clickable to home */}
          <button
            onClick={() => navigate("/")}
            className="flex items-center gap-3 hover:opacity-80 transition-opacity shrink-0"
          >
            <div className="w-10 h-10 flex items-center justify-center mt-4">
              <img
                src={Logo}
                alt="AskVigil Logo"
                className="w-full h-full object-contain scale-500 ml-20"
              />
            </div>
          </button>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center gap-8 ml-14">
            <button
              onClick={() => navigate("/")}
              className={`transition-colors px-3 py-1 rounded-md ${
                isActive("/")
                  ? "text-[#8A5A2B] font-semibold bg-[#EAA866]/25"
                  : "text-slate-700 hover:text-slate-900"
              }`}
            >
              Home
            </button>
            <button
              onClick={() => navigate("/guidance")}
              className={`transition-colors px-3 py-1 rounded-md ${
                isActive("/guidance")
                  ? "text-[#8A5A2B] font-semibold bg-[#EAA866]/25"
                  : "text-slate-700 hover:text-slate-900"
              }`}
            >
              Guidance
            </button>
            <button
              onClick={() => navigate("/learning")}
              className={`transition-colors px-3 py-1 rounded-md ${
                isActive("/learning")
                  ? "text-[#8A5A2B] font-semibold bg-[#EAA866]/25"
                  : "text-slate-700 hover:text-slate-900"
              }`}
            >
              Learning
            </button>
            <button
              onClick={() => navigate("/quiz")}
              className={`transition-colors px-3 py-1 rounded-md ${
                isActive("/quiz")
                  ? "text-[#8A5A2B] font-semibold bg-[#EAA866]/25"
                  : "text-slate-700 hover:text-slate-900"
              }`}
            >
              Quiz
            </button>
          </nav>
        </div>
      </div>
    </header>
  );
}
