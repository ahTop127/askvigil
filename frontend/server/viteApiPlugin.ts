import type { Plugin } from "vite";
import { handleAskvigilApi } from "./httpApi";

export function localAskvigilApiPlugin(
  env: Record<string, string>,
): Plugin {
  return {
    name: "askvigil-local-api",
    configureServer(server) {
      server.middlewares.use(async (req, res, next) => {
        const url = req.url?.split("?")[0] ?? "";
        if (!url.startsWith("/api/")) {
          next();
          return;
        }
        await handleAskvigilApi(req, res, env);
      });
    },
  };
}
