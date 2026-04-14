import { APP_CONFIG } from "@lib/config/app";

export interface QuizCategory {
  id: number;
  name: string;
  description: string | null;
}

export interface QuizOption {
  id: number;
  option_text: string;
}

export interface QuizQuestion {
  id: number;
  scenario_text: string;
  options: QuizOption[];
}

export interface QuizResultItem {
  question_id: number;
  scenario_text: string;
  user_selected_option_id: number;
  correct_option_id: number;
  is_correct: boolean;
  explanation: string;
}

export interface QuizSubmitSummary {
  total_questions: number;
  correct_answers: number;
  results: QuizResultItem[];
}

type SessionInitResponse = {
  session_id?: string;
};

function buildUrl(path: string): string {
  return `${APP_CONFIG.api.baseUrl.replace(/\/$/, "")}${path}`;
}

async function fetchWith404Fallback(
  paths: string[],
  init: RequestInit,
): Promise<Response> {
  let lastResponse: Response | null = null;
  for (const path of paths) {
    const response = await fetch(buildUrl(path), init);
    if (response.ok) return response;
    lastResponse = response;
    if (response.status !== 404) break;
  }
  if (!lastResponse) {
    throw new Error("Request failed before receiving a response");
  }
  return lastResponse;
}

function getCookie(name: string): string | null {
  const escaped = name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const match = document.cookie.match(new RegExp(`(?:^|; )${escaped}=([^;]*)`));
  return match ? decodeURIComponent(match[1]) : null;
}

export async function initQuizSession(): Promise<string> {
  const response = await fetch(buildUrl("/v1/session/init"), {
    method: "GET",
    headers: { Accept: "application/json" },
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error(`Session init failed (${response.status})`);
  }

  let payload: SessionInitResponse = {};
  try {
    payload = (await response.json()) as SessionInitResponse;
  } catch {
    // some deployments may return empty body for session init
  }

  const cookieSession = getCookie("session_id");
  const sessionId = payload.session_id ?? cookieSession;
  if (!sessionId) {
    throw new Error("Session ID missing from /session/init");
  }

  return sessionId;
}

export async function getQuizCategories(): Promise<QuizCategory[]> {
  const response = await fetch(buildUrl("/v1/learning/categories"), {
    method: "GET",
    headers: { Accept: "application/json" },
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch quiz categories (${response.status})`);
  }

  return (await response.json()) as QuizCategory[];
}

export async function getQuizQuestions(
  categoryId: number,
): Promise<QuizQuestion[]> {
  const response = await fetch(
    buildUrl(
      `/v1/learning/quizzes?category_id=${encodeURIComponent(String(categoryId))}`,
    ),
    {
      method: "GET",
      headers: { Accept: "application/json" },
      credentials: "include",
    },
  );
  if (!response.ok) {
    throw new Error(`Failed to fetch quiz questions (${response.status})`);
  }
  return (await response.json()) as QuizQuestion[];
}

export async function getRandomQuizQuestions(): Promise<QuizQuestion[]> {
  const response = await fetch(buildUrl("/v1/learning/quizzes"), {
    method: "GET",
    headers: { Accept: "application/json" },
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch quiz questions (${response.status})`);
  }
  return (await response.json()) as QuizQuestion[];
}

export async function submitQuizAnswers(input: {
  session_id: string;
  category_id: number;
  answers: Array<{ question_id: number; selected_option_id: number }>;
}): Promise<QuizSubmitSummary> {
  const body = JSON.stringify(input);
  const response = await fetchWith404Fallback(
    [
      "/v1/learning/quizzes/submit",
      "/v1/learning/quiz/submit",
      "/v1/quizzes/submit",
      "/v1/quiz/submit",
    ],
    {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      credentials: "include",
      body,
    },
  );
  if (!response.ok) {
    throw new Error(`Failed to submit quiz answers (${response.status})`);
  }
  return (await response.json()) as QuizSubmitSummary;
}
