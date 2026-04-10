import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router";
import { ArrowLeft, CheckCircle, XCircle, Sparkles, Star } from "lucide-react";
import { Button } from "../components/ui/button";
import { Navigation } from "../components/Navigation";
import { BackButton } from "../components/BackButton";
import { EyeFollowMouse } from "../components/EyeFollowMouse";

interface Question {
  id: number;
  message: string;
  isScam: boolean;
  explanation: string;
}

const questions: Question[] = [
  {
    id: 1,
    message: "URGENT! Your bank account has been suspended. Click here immediately to verify: bit.ly/verify-acc",
    isScam: true,
    explanation: "This is a scam. Banks never ask you to verify accounts via links in messages. The urgent language and shortened URL are red flags.",
  },
  {
    id: 2,
    message: "Hi! This is Sarah from ABC Company. Thanks for your interview yesterday. We'll contact you next week with our decision.",
    isScam: false,
    explanation: "This appears legitimate. It's a normal follow-up message after an interview with no requests for money or personal information.",
  },
  {
    id: 3,
    message: "Congratulations! You've been selected for a work-from-home job earning RM5000/month. Send RM300 registration fee to confirm your position.",
    isScam: true,
    explanation: "This is a job scam. Legitimate employers never ask for upfront payment. The high salary for minimal work is too good to be true.",
  },
  {
    id: 4,
    message: "Your delivery package is waiting. Track it here: pos-malaysia-track.com/track123",
    isScam: true,
    explanation: "This is a phishing scam. The domain is fake (real Pos Malaysia uses poslaju.com.my). Scammers create fake tracking sites to steal information.",
  },
  {
    id: 5,
    message: "Hi, I'm calling from your bank. Someone is trying to withdraw money from your account. Please share the OTP we just sent you to block the transaction.",
    isScam: true,
    explanation: "This is an OTP scam. Real banks will NEVER ask for your OTP. They're using urgency to trick you into giving access to your account.",
  },
];

export default function PracticePage() {
  const navigate = useNavigate();
  const [hasStarted, setHasStarted] = useState(false);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [userAnswers, setUserAnswers] = useState<boolean[]>([]);
  const [isComplete, setIsComplete] = useState(false);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });

  const currentQuestion = questions[currentQuestionIndex];

  // Track mouse position
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setMousePosition({ x: e.clientX, y: e.clientY });
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  const handleStart = () => {
    setHasStarted(true);
  };

  const handleAnswer = (answer: boolean) => {
    const newAnswers = [...userAnswers, answer];
    setUserAnswers(newAnswers);

    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
    } else {
      setIsComplete(true);
    }
  };

  const handleRestart = () => {
    setHasStarted(false);
    setCurrentQuestionIndex(0);
    setUserAnswers([]);
    setIsComplete(false);
  };

  // Welcome Screen - Fortune Cookie Style
  if (!hasStarted && !isComplete) {
    return (
      <div className="min-h-screen bg-[#F5F3E8] relative overflow-hidden">
        {/* Background Illustration */}
        <div 
          className="absolute inset-0 bg-cover bg-center opacity-40"
          style={{
            backgroundImage: `url('https://images.unsplash.com/photo-1662092560436-5bdae9a1acea?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxpc29tZXRyaWMlMjBjaXR5JTIwaWxsdXN0cmF0aW9uJTIwY29sb3JmdWx8ZW58MXx8fHwxNzc1MDI3ODkxfDA&ixlib=rb-4.1.0&q=80&w=1080')`,
          }}
        />

        {/* Navigation */}
        <Navigation />

        {/* Main Content */}
        <main className="relative z-10 flex items-center justify-center min-h-screen px-4 py-20">
          <div className="max-w-2xl w-full">
            {/* Fortune Cookie Image Container */}
            <div className="mb-8 flex justify-center">
              <EyeFollowMouse mousePosition={mousePosition} />
            </div>

            {/* White Card */}
            <div className="bg-white/95 backdrop-blur-sm rounded-3xl shadow-2xl p-8 md:p-12 text-center border border-gray-200 animate-fade-in-up bg-[#ffffff66]">
              <h1 className="text-4xl md:text-5xl font-bold text-[#FF6B35] mb-4">
                Will Scammers Makan You?
              </h1>
              
              <p className="text-lg text-gray-700 mb-8 leading-relaxed max-w-xl mx-auto">
                Take this quiz to find out how vulnerable you are to scams and learn how to stay off the scammers' plates.
              </p>

              <button
                onClick={handleStart}
                className="inline-flex items-center gap-3 bg-[#FF6B35] hover:bg-[#E55A28] text-white px-10 py-5 rounded-full text-lg font-semibold transition-all shadow-lg hover:shadow-xl hover:scale-105 animate-pulse-soft"
              >
                <Sparkles className="w-5 h-5" />
                Let's Find Out
                <Sparkles className="w-5 h-5" />
              </button>

              <p className="mt-6 text-sm text-gray-500">
                {questions.length} questions • 5 minutes
              </p>
            </div>
          </div>
        </main>
      </div>
    );
  }

  // Results Screen
  if (isComplete) {
    const score = userAnswers.filter((answer, index) => answer === questions[index].isScam).length;
    const percentage = Math.round((score / questions.length) * 100);
    
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
        {/* Navigation */}
        <Navigation />

        {/* Results */}
        <main className="max-w-5xl mx-auto px-4 py-12">
          <div className="bg-white rounded-3xl shadow-xl border border-gray-200 p-8 md:p-12">
            {/* Score Display */}
            <div className="text-center mb-12">
              <div className="text-7xl mb-6 animate-bounce-once">
                {getEmoji()}
              </div>
              
              <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
                Quiz Complete!
              </h1>
              
              <div className="mb-6">
                <div className="text-7xl font-bold text-[#669E84] mb-2">
                  {score}/{questions.length}
                </div>
                <p className="text-2xl text-gray-700">
                  {getMessage()}
                </p>
              </div>

              <div className="bg-[#669E84]/10 border border-[#669E84]/30 rounded-2xl p-6 mb-8 max-w-md mx-auto">
                <p className="text-gray-700 text-lg">
                  You correctly identified <span className="font-bold text-[#669E84]">{score}</span> out of <span className="font-bold">{questions.length}</span> scam scenarios.
                </p>
              </div>
            </div>

            {/* Detailed Results */}
            <div className="space-y-6 mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Review Your Answers</h2>
              
              {questions.map((question, index) => {
                const userAnswer = userAnswers[index];
                const isCorrect = userAnswer === question.isScam;
                
                return (
                  <div
                    key={question.id}
                    className={`border-2 rounded-2xl p-6 ${
                      isCorrect
                        ? 'border-green-200 bg-green-50'
                        : 'border-red-200 bg-red-50'
                    }`}
                  >
                    <div className="flex items-start gap-4 mb-4">
                      {isCorrect ? (
                        <CheckCircle className="w-7 h-7 text-green-600 flex-shrink-0 mt-1" />
                      ) : (
                        <XCircle className="w-7 h-7 text-red-600 flex-shrink-0 mt-1" />
                      )}
                      <div className="flex-1">
                        <h3 className={`font-semibold text-lg mb-2 ${
                          isCorrect ? 'text-green-900' : 'text-red-900'
                        }`}>
                          Question {index + 1}: {isCorrect ? 'Correct' : 'Incorrect'}
                        </h3>
                        <div className="bg-white rounded-xl p-4 mb-3 border border-gray-200">
                          <p className="text-gray-800 leading-relaxed">
                            {question.message}
                          </p>
                        </div>
                        <p className={`text-sm ${
                          isCorrect ? 'text-green-800' : 'text-red-800'
                        }`}>
                          <span className="font-semibold">Your answer:</span> {userAnswer ? 'Scam' : 'Safe'}
                        </p>
                        <p className={`text-sm mb-2 ${
                          isCorrect ? 'text-green-800' : 'text-red-800'
                        }`}>
                          <span className="font-semibold">Correct answer:</span> {question.isScam ? 'Scam' : 'Safe'}
                        </p>
                        <p className={`leading-relaxed ${
                          isCorrect ? 'text-green-800' : 'text-red-800'
                        }`}>
                          {question.explanation}
                        </p>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Action Buttons */}
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

  // Quiz Screen
  return (
    <div className="min-h-screen bg-[#FFFDF2]">
      {/* Navigation */}
      <Navigation />
      
      {/* Back Button */}
      <BackButton />

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 py-12">
        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-semibold text-gray-700">
              Question {currentQuestionIndex + 1} of {questions.length}
            </span>
            <span className="text-sm text-gray-600">
              Answered: <span className="font-semibold text-[#669E84]">{userAnswers.length}</span> / {questions.length}
            </span>
          </div>
          <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-[#669E84] transition-all duration-500"
              style={{ width: `${(userAnswers.length / questions.length) * 100}%` }}
            />
          </div>
        </div>

        {/* Question Card */}
        <div className="bg-white rounded-3xl shadow-xl border border-gray-200 p-8 md:p-10 animate-fade-in">
          <h2 className="text-2xl md:text-3xl font-bold text-gray-900 mb-6">
            Is this message a scam?
          </h2>

          {/* Message Display */}
          <div className="bg-gradient-to-br from-gray-50 to-gray-100 border-2 border-gray-200 rounded-2xl p-6 md:p-8 mb-8 shadow-inner">
            <p className="text-gray-800 text-lg leading-relaxed whitespace-pre-line">
              {currentQuestion.message}
            </p>
          </div>

          {/* Answer Buttons */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <button
              onClick={() => handleAnswer(true)}
              className="h-14 border-3 border-red-500 bg-red-50 hover:bg-red-500 text-red-700 hover:text-white rounded-xl text-lg font-semibold transition-all shadow-md hover:shadow-xl hover:scale-105"
            >
              ⚠️ Yes, it's a scam
            </button>
            <button
              onClick={() => handleAnswer(false)}
              className="h-14 border-3 border-green-500 bg-green-50 hover:bg-green-500 text-green-700 hover:text-white rounded-xl text-lg font-semibold transition-all shadow-md hover:shadow-xl hover:scale-105"
            >
              ✅ No, it's safe
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}