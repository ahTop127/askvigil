import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate, useSearchParams } from "react-router";
import { CheckCircle, XCircle, Sparkles } from "lucide-react";
import { Navigation } from "../components/Navigation";
import { BackButton } from "../components/BackButton";
import { EyeFollowMouse } from "../components/EyeFollowMouse";
import {
  getQuizCategories,
  getQuizQuestions,
  getRandomQuizQuestions,
  initQuizSession,
  submitQuizAnswers,
  type QuizCategory,
  type QuizQuestion,
  type QuizResultItem,
} from "@lib/api/quiz";

/** Map Yes/No UI to backend option ids (two options per question). */
function getScamAndSafeOptionIds(q: QuizQuestion): { scamId: number; safeId: number } {
  const [a, b] = q.options;
  if (!a || !b) {
    return { scamId: -1, safeId: -1 };
  }
  const ta = a.option_text.toLowerCase();
  const tb = b.option_text.toLowerCase();
  const aLeanSafe =
    /\b(safe|legitimate|genuine|not a scam|no)\b/.test(ta) &&
    !/\b(scam|fraud)\b/.test(ta);
  const bLeanSafe =
    /\b(safe|legitimate|genuine|not a scam|no)\b/.test(tb) &&
    !/\b(scam|fraud)\b/.test(tb);
  const aLeanScam =
    /\b(scam|fraud|phish|fake)\b/.test(ta) || /\b(yes)\b/.test(ta);
  const bLeanScam =
    /\b(scam|fraud|phish|fake)\b/.test(tb) || /\b(yes)\b/.test(tb);

  if (aLeanSafe && !bLeanSafe) return { scamId: b.id, safeId: a.id };
  if (bLeanSafe && !aLeanSafe) return { scamId: a.id, safeId: b.id };
  if (aLeanScam && !bLeanScam) return { scamId: a.id, safeId: b.id };
  if (bLeanScam && !aLeanScam) return { scamId: b.id, safeId: a.id };
  return { scamId: a.id, safeId: b.id };
}

function labelForOptionId(
  q: QuizQuestion | undefined,
  optionId: number,
): string {
  if (!q) return `Option #${optionId}`;
  const { scamId, safeId } = getScamAndSafeOptionIds(q);
  if (optionId === scamId) return "Scam";
  if (optionId === safeId) return "Safe";
  return `Option #${optionId}`;
}

export default function PracticePage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const [hasStarted, setHasStarted] = useState(false);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [userAnswers, setUserAnswers] = useState<number[]>([]);
  const [isComplete, setIsComplete] = useState(false);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const [selectedCategoryId, setSelectedCategoryId] = useState<number | null>(null);
  const [sessionId, setSessionId] = useState<string>("");
  const [questions, setQuestions] = useState<QuizQuestion[]>([]);
  const [results, setResults] = useState<QuizResultItem[]>([]);
  const [loadError, setLoadError] = useState<string>("");
  const [isLoadingCategories, setIsLoadingCategories] = useState(false);
  const [isLoadingQuiz, setIsLoadingQuiz] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const currentQuestion = questions[currentQuestionIndex] ?? null;

  const score = useMemo(
    () => results.filter((r) => r.is_correct).length,
    [results],
  );
  const percentage = useMemo(
    () => (results.length ? Math.round((score / results.length) * 100) : 0),
    [results.length, score],
  );

  const scamType = searchParams.get("scamType");
  const categoryIdParam = searchParams.get("categoryId");
  const isRandomQuizMode = location.pathname === "/quiz";

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setMousePosition({ x: e.clientX, y: e.clientY });
    };
    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, []);

  useEffect(() => {
    const loadCategories = async () => {
      if (isRandomQuizMode) {
        // Random quiz mode does not require category selection.
        setSelectedCategoryId(0);
        return;
      }
      setIsLoadingCategories(true);
      setLoadError("");
      try {
        const parsed = categoryIdParam ? Number(categoryIdParam) : NaN;
        if (categoryIdParam && Number.isFinite(parsed)) {
          setSelectedCategoryId(parsed);
          return;
        }
        const list = await getQuizCategories();
        if (!list.length) {
          setLoadError("No quiz categories returned from server.");
          return;
        }
        const picked = pickCategoryFromScamType(list, scamType);
        setSelectedCategoryId(picked?.id ?? list[0].id);
      } catch {
        setLoadError("Failed to load quiz categories.");
      } finally {
        setIsLoadingCategories(false);
      }
    };
    void loadCategories();
  }, [scamType, categoryIdParam, isRandomQuizMode]);

  const handleStart = async () => {
    if (selectedCategoryId === null) {
      setLoadError("Quiz is still loading. Please try again.");
      return;
    }
    setIsLoadingQuiz(true);
    setLoadError("");
    try {
      const [sid, quizQuestions] = await Promise.all([
        initQuizSession(),
        isRandomQuizMode ? getRandomQuizQuestions() : getQuizQuestions(selectedCategoryId),
      ]);
      if (!quizQuestions.length) {
        setLoadError(
          isRandomQuizMode
            ? "No quiz questions available right now."
            : "No quiz questions available for this scam category.",
        );
        return;
      }
      setSessionId(sid);
      setQuestions(quizQuestions);
      setUserAnswers([]);
      setCurrentQuestionIndex(0);
      setResults([]);
      setIsComplete(false);
      setHasStarted(true);
    } catch {
      setLoadError("Failed to load quiz questions. Please try again.");
    } finally {
      setIsLoadingQuiz(false);
    }
  };

  const submitCurrentAnswers = async (answers: number[]) => {
    if (selectedCategoryId === null || !sessionId || !questions.length) {
      setLoadError("Quiz session data is incomplete. Please restart quiz.");
      return;
    }
    setIsSubmitting(true);
    setLoadError("");
    try {
      const payload = {
        session_id: sessionId,
        category_id: selectedCategoryId,
        answers: questions.map((q, index) => ({
          question_id: q.id,
          selected_option_id: answers[index],
        })),
      };
      const summary = await submitQuizAnswers(payload);
      setResults(summary.results);
      setIsComplete(true);
    } catch {
      setLoadError("Failed to submit quiz answers. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleAnswer = (selectedOptionId: number) => {
    const newAnswers = [...userAnswers, selectedOptionId];
    setUserAnswers(newAnswers);

    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
    } else {
      void submitCurrentAnswers(newAnswers);
    }
  };

  const handleRestart = () => {
    setHasStarted(false);
    setCurrentQuestionIndex(0);
    setUserAnswers([]);
    setIsComplete(false);
    setResults([]);
    setQuestions([]);
    setSessionId("");
    setLoadError("");
  };

  // Welcome Screen
  if (!hasStarted && !isComplete) {
    return (
      <div className="min-h-screen bg-[#F5F3E8] relative overflow-hidden">
        <div
          className="absolute inset-0 bg-cover bg-center opacity-40"
          style={{
            backgroundImage: `url('https://images.unsplash.com/photo-1662092560436-5bdae9a1acea?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxpc29tZXRyaWMlMjBjaXR5JTIwaWxsdXN0cmF0aW9uJTIwY29sb3JmdWx8ZW58MXx8fHwxNzc1MDI3ODkxfDA&ixlib=rb-4.1.0&q=80&w=1080')`,
          }}
        />
        <Navigation />
        <main className="relative z-10 flex items-center justify-center min-h-screen px-4 py-20">
          <div className="max-w-2xl w-full">
            <div className="mb-8 flex justify-center">
              <EyeFollowMouse mousePosition={mousePosition} />
            </div>
            <div className="bg-white/95 backdrop-blur-sm rounded-3xl shadow-2xl p-8 md:p-12 text-center border border-gray-200 animate-fade-in-up bg-[#ffffff66]">
              <h1 className="text-4xl md:text-5xl font-bold text-[#FF6B35] mb-4">
                Will Scammers Makan You?
              </h1>
              <p className="text-lg text-gray-700 mb-8 leading-relaxed max-w-xl mx-auto">
                Take this quiz to find out how vulnerable you are to scams and
                learn how to stay off the scammers' plates.
              </p>
              <button
                onClick={() => void handleStart()}
                disabled={isLoadingCategories || isLoadingQuiz || selectedCategoryId === null}
                className="inline-flex items-center gap-3 bg-[#FF6B35] hover:bg-[#E55A28] text-white px-10 py-5 rounded-full text-lg font-semibold transition-all shadow-lg hover:shadow-xl hover:scale-105 animate-pulse-soft"
              >
                <Sparkles className="w-5 h-5" />
                {isLoadingQuiz ? "Loading..." : "Let's Find Out"}
                <Sparkles className="w-5 h-5" />
              </button>
              {loadError && (
                <p className="mt-4 text-sm text-red-600 font-medium">{loadError}</p>
              )}
              <p className="mt-6 text-sm text-gray-500">
                5 questions • 5 minutes
              </p>
            </div>
          </div>
        </main>
      </div>
    );
  }

  // Results Screen
  if (isComplete) {
    const getMessage = () => {
      if (percentage >= 80) return "Excellent! You're great at spotting scams.";
      if (percentage >= 60) return "Good job! Keep learning to improve.";
      return "Keep practicing! Review the learning materials to get better.";
    };

    const getEmoji = () => {
      if (percentage >= 80) return "🛡️";
      if (percentage >= 60) return "👍";
      return "📚";
    };

    return (
      <div className="min-h-screen bg-[#FFFDF2]">
        <Navigation />
        <main className="max-w-5xl mx-auto px-4 py-12">
          <div className="bg-white rounded-3xl shadow-xl border border-gray-200 p-8 md:p-12">
            <div className="text-center mb-12">
              <div className="text-7xl mb-6 animate-bounce-once">{getEmoji()}</div>
              <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
                Quiz Complete!
              </h1>
              <div className="mb-6">
                <div className="text-7xl font-bold text-[#669E84] mb-2">
                  {score}/{questions.length}
                </div>
                <p className="text-2xl text-gray-700">{getMessage()}</p>
              </div>
              <div className="bg-[#669E84]/10 border border-[#669E84]/30 rounded-2xl p-6 mb-8 max-w-md mx-auto">
                <p className="text-gray-700 text-lg">
                  You correctly identified{" "}
                  <span className="font-bold text-[#669E84]">{score}</span> out
                  of <span className="font-bold">{questions.length}</span> scam
                  scenarios.
                </p>
              </div>
            </div>

            <div className="space-y-6 mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">
                Review Your Answers
              </h2>
              {results.map((result, index) => {
                const q = questions.find((item) => item.id === result.question_id);
                const userLabel = labelForOptionId(q, result.user_selected_option_id);
                const correctLabel = labelForOptionId(q, result.correct_option_id);

                return (
                  <div
                    key={result.question_id}
                    className={`border-2 rounded-2xl p-6 ${
                      result.is_correct
                        ? "border-green-200 bg-green-50"
                        : "border-red-200 bg-red-50"
                    }`}
                  >
                    <div className="flex items-start gap-4 mb-4">
                      {result.is_correct ? (
                        <CheckCircle className="w-7 h-7 text-green-600 flex-shrink-0 mt-1" />
                      ) : (
                        <XCircle className="w-7 h-7 text-red-600 flex-shrink-0 mt-1" />
                      )}
                      <div className="flex-1">
                        <h3
                          className={`font-semibold text-lg mb-2 ${
                            result.is_correct ? "text-green-900" : "text-red-900"
                          }`}
                        >
                          Question {index + 1}:{" "}
                          {result.is_correct ? "Correct" : "Incorrect"}
                        </h3>
                        <div className="bg-white rounded-xl p-4 mb-3 border border-gray-200">
                          <p className="text-gray-800 leading-relaxed">
                            {result.scenario_text}
                          </p>
                        </div>
                        <p
                          className={`text-sm ${
                            result.is_correct ? "text-green-800" : "text-red-800"
                          }`}
                        >
                          <span className="font-semibold">Your answer:</span>{" "}
                          {userLabel}
                        </p>
                        <p
                          className={`text-sm mb-2 ${
                            result.is_correct ? "text-green-800" : "text-red-800"
                          }`}
                        >
                          <span className="font-semibold">Correct answer:</span>{" "}
                          {correctLabel}
                        </p>
                        <p
                          className={`leading-relaxed ${
                            result.is_correct ? "text-green-800" : "text-red-800"
                          }`}
                        >
                          {result.explanation}
                        </p>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="grid md:grid-cols-2 gap-4 max-w-md mx-auto">
              <button
                onClick={handleRestart}
                className="h-14 border-2 border-[#669E84] text-[#669E84] hover:bg-[#669E84] hover:text-white rounded-full font-semibold transition-all"
              >
                Try Again
              </button>
              <button
                onClick={() => navigate("/learning")}
                className="h-14 bg-[#669E84] hover:bg-[#54A388] text-white rounded-full font-semibold transition-all shadow-lg"
              >
                Learn More
              </button>
            </div>
          </div>
        </main>
      </div>
    );
  }

  // Quiz Screen — same layout as before; data from API only
  if (!currentQuestion || !questions.length) {
    return null;
  }

  const { scamId, safeId } = getScamAndSafeOptionIds(currentQuestion);
  const canAnswer = scamId > 0 && safeId > 0 && !isSubmitting;

  return (
    <div className="min-h-screen bg-[#FFFDF2]">
      <Navigation />
      <BackButton />
      <main className="max-w-4xl mx-auto px-4 py-12">
        <div className="mb-8">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-semibold text-gray-700">
              Question {currentQuestionIndex + 1} of {questions.length}
            </span>
            <span className="text-sm text-gray-600">
              Answered:{" "}
              <span className="font-semibold text-[#669E84]">
                {userAnswers.length}
              </span>{" "}
              / {questions.length}
            </span>
          </div>
          <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-[#669E84] transition-all duration-500"
              style={{
                width: `${(userAnswers.length / questions.length) * 100}%`,
              }}
            />
          </div>
        </div>

        <div className="bg-white rounded-3xl shadow-xl border border-gray-200 p-8 md:p-10 animate-fade-in">
          <h2 className="text-2xl md:text-3xl font-bold text-gray-900 mb-6">
            Is this message a scam?
          </h2>
          <div className="bg-gradient-to-br from-gray-50 to-gray-100 border-2 border-gray-200 rounded-2xl p-6 md:p-8 mb-8 shadow-inner">
            <p className="text-gray-800 text-lg leading-relaxed whitespace-pre-line">
              {currentQuestion.scenario_text}
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <button
              type="button"
              onClick={() => handleAnswer(scamId)}
              disabled={!canAnswer}
              className="h-14 border-3 border-red-500 bg-red-50 hover:bg-red-500 text-red-700 hover:text-white rounded-xl text-lg font-semibold transition-all shadow-md hover:shadow-xl hover:scale-105"
            >
              ⚠️ Yes, it&apos;s a scam
            </button>
            <button
              type="button"
              onClick={() => handleAnswer(safeId)}
              disabled={!canAnswer}
              className="h-14 border-3 border-green-500 bg-green-50 hover:bg-green-500 text-green-700 hover:text-white rounded-xl text-lg font-semibold transition-all shadow-md hover:shadow-xl hover:scale-105"
            >
              ✅ No, it&apos;s safe
            </button>
          </div>
          {loadError && <p className="mt-4 text-sm text-red-600">{loadError}</p>}
          {isSubmitting && (
            <p className="mt-4 text-sm text-gray-600">Submitting your answers...</p>
          )}
        </div>
      </main>
    </div>
  );
}

function pickCategoryFromScamType(
  categories: QuizCategory[],
  scamType: string | null,
): QuizCategory | null {
  if (!scamType) return null;
  const normalized = scamType.toLowerCase();

  const alias: Record<string, string[]> = {
    "job-scam": ["job"],
    phishing: ["phishing"],
    "otp-scam": ["otp"],
    "qr-scam": ["qr"],
    "suspicious-link": ["link", "url", "suspicious"],
  };

  const keywords = alias[normalized] ?? [normalized];
  return (
    categories.find((category) => {
      const name = category.name.toLowerCase();
      return keywords.some((keyword) => name.includes(keyword));
    }) ?? null
  );
}
