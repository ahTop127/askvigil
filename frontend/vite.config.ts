/// <reference types="vitest/config" />
import { defineConfig, loadEnv } from "vite";
import path from "path";
import https from "node:https";
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const proxyTarget =
    env.VITE_PROXY_TARGET?.trim() || "https://sleepunderflow.duckdns.org";

  let proxyHttpsAgent: https.Agent | undefined;
  try {
    const { hostname, protocol } = new URL(proxyTarget);
    if (protocol === "https:" && hostname) {
      proxyHttpsAgent = new https.Agent({
        // Fixes TLS "unrecognized name" / SNI issues when proxying to HTTPS upstreams.
        servername: hostname,
      });
    }
  } catch {
    // invalid VITE_PROXY_TARGET — fall back to default agent behavior
  }

  return {
    plugins: [
      // The React and Tailwind plugins are both required for Make, even if
      // Tailwind is not being actively used – do not remove them
      react(),
      tailwindcss(),
    ],
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "./src"),
        "@components": path.resolve(__dirname, "./src/app/components"),
        "@pages": path.resolve(__dirname, "./src/app/pages"),
        "@lib": path.resolve(__dirname, "./src/lib"),
        "@hooks": path.resolve(__dirname, "./src/app/hooks"),
        "@assets": path.resolve(__dirname, "./src/assets"),
      },
    },

    // Local dev proxy: browser hits same-origin /api, Vite forwards to remote backend.
    server: {
      proxy: {
        "/api": {
          target: proxyTarget,
          changeOrigin: true,
          secure: true,
          ...(proxyHttpsAgent ? { agent: proxyHttpsAgent } : {}),
        },
      },
    },

    // File types to support raw imports. Never add .css, .tsx, or .ts files to this.
    assetsInclude: ["**/*.svg", "**/*.csv"],

    // After removing react-easy-crop, clear stale optimizer cache if you see ENOENT on it.
    optimizeDeps: {
      include: ["react-image-crop"],
    },

    test: {
      globals: true,
      environment: "jsdom",
      setupFiles: "./src/test/setup.ts",
      css: true,
    },
  };
});
