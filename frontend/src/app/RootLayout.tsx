import { useEffect } from "react";
import { Outlet, useLocation } from "react-router";
import { initSession } from "@lib/api/session";

/**
 * Scrolls to top when entering Learning or Guidance (including detail routes),
 * so navigation from a scrolled page does not keep the old scroll position.
 * Also bootstraps the user session on first mount so every later detection
 * call has a `session_id` available.
 */
export default function RootLayout() {
  const { pathname } = useLocation();

  useEffect(() => {
    /** Fire and forget — failures fall back to anonymous detection on the server. */
    void initSession();
  }, []);

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
