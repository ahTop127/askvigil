import type { IncomingMessage, ServerResponse } from "node:http";
import { handleAskvigilApi } from "../server/httpApi";

export const config = {
  maxDuration: 30,
  api: {
    bodyParser: false,
  },
};

export default async function handler(
  req: IncomingMessage,
  res: ServerResponse,
): Promise<void> {
  await handleAskvigilApi(
    req,
    res,
    process.env as Record<string, string | undefined>,
  );
}
