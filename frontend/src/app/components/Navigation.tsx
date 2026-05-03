import { useNavigate, useLocation } from "react-router";
import Logo from "@assets/AskVigilLogo.png";

export function Navigation() {
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogoClick = () => {
    if (location.pathname !== "/") {
      navigate("/");
      return;
    }
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const isActive = (path: string) => {
    if (path === "/guidance") {
      return location.pathname.startsWith("/guidance");
    }
    if (path === "/learning") {
      return (
        location.pathname.startsWith("/learning") ||
        location.pathname.startsWith("/quiz")
      );
    }
    if (path === "/cases") {
      return location.pathname.startsWith("/cases");
    }
    return location.pathname === path;
  };

  return (
    <header className="backdrop-blur-md bg-transparent border-b border-white/10 sticky top-0 z-50">
      <div className="w-full px-4 py-5">
        <div className="flex items-center gap-8">
          {/* Logo - Clickable to home */}
          <button
            onClick={handleLogoClick}
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
                  ? "text-primary font-semibold bg-primary/15"
                  : "text-foreground/80 hover:text-foreground"
              }`}
            >
              Home
            </button>
            <button
              onClick={() => navigate("/guidance")}
              className={`transition-colors px-3 py-1 rounded-md ${
                isActive("/guidance")
                  ? "text-primary font-semibold bg-primary/15"
                  : "text-foreground/80 hover:text-foreground"
              }`}
            >
              Scam Help
            </button>
            <div className="relative group">
              <button
                type="button"
                onClick={() => navigate("/learning")}
                className={`transition-colors px-3 py-1 rounded-md ${
                  isActive("/learning")
                    ? "text-primary font-semibold bg-primary/15"
                    : "text-foreground/80 hover:text-foreground"
                }`}
              >
                Learning
              </button>
              <div
                className="absolute left-0 top-full z-50 pt-1 opacity-0 invisible transition-[opacity,visibility] duration-150 group-hover:opacity-100 group-hover:visible group-focus-within:opacity-100 group-focus-within:visible"
                role="menu"
                aria-label="Learning submenu"
              >
                <div className="rounded-md border border-white/10 bg-background/95 backdrop-blur-md shadow-lg py-1 min-w-[9rem]">
                  <button
                    type="button"
                    role="menuitem"
                    onClick={() => navigate("/quiz")}
                    className={`w-full text-left transition-colors px-3 py-1 rounded-md ${
                      location.pathname.startsWith("/quiz")
                        ? "text-primary font-semibold bg-primary/15"
                        : "text-foreground/80 hover:text-foreground bg-[#F9FAFB] hover:bg-gray-100"
                    }`}
                  >
                    Quiz
                  </button>
                </div>
              </div>
            </div>
            <button
              onClick={() => navigate("/cases")}
              className={`transition-colors px-3 py-1 rounded-md ${
                isActive("/cases")
                  ? "text-primary font-semibold bg-primary/15"
                  : "text-foreground/80 hover:text-foreground"
              }`}
            >
              Scam Feed
            </button>
          </nav>
        </div>
      </div>
    </header>
  );
}
