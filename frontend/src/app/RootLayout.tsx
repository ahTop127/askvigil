import { useEffect } from "react";
import { Outlet, useLocation } from "react-router";

/**
 * Scrolls to top when entering Learning or Guidance (including detail routes),
 * so navigation from a scrolled page does not keep the old scroll position.
 */
export default function RootLayout() {
  const { pathname } = useLocation();

  useEffect(() => {
    const learning =
      pathname === "/learning" || pathname.startsWith("/learning/");
    const guidance =
      pathname === "/guidance" || pathname.startsWith("/guidance/");
    if (learning || guidance) {
      window.scrollTo({ top: 0, left: 0, behavior: "auto" });
    }
  }, [pathname]);

  return <Outlet />;
}
