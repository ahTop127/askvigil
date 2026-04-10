import { useEffect, useState } from "react";
import { useNavigate } from "react-router";
import { Shield, AlertCircle, CheckCircle, AlertTriangle, ArrowLeft } from "lucide-react";
import { Button } from "../components/ui/button";
import { Navigation } from "../components/Navigation";

type RiskLevel = "low" | "medium" | "high";

interface ScanResult {
  input: string;
  type: string;
  riskLevel: RiskLevel;
  explanation: string;
  scamType?: string;
}

export default function DetectionResultPage() {
  const navigate = useNavigate();
  const [result, setResult] = useState<ScanResult | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    const storedResult = localStorage.getItem("lastScanResult");
    if (storedResult) {
      try {
        setResult(JSON.parse(storedResult));
      } catch {
        setError(true);
      }
    } else {
      setError(true);
    }
  }, []);

  const getScamTypeInfo = (scamType?: string) => {
    const scamTypes: Record<string, { name: string; guidancePath: string }> = {
      "job-scam": { name: "Job Scam", guidancePath: "/guidance/job-scam" },
      "phishing": { name: "Phishing", guidancePath: "/guidance/phishing" },
      "otp-scam": { name: "OTP Scam", guidancePath: "/guidance/otp-scam" },
      "qr-scam": { name: "QR Scam", guidancePath: "/guidance/qr-scam" },
      "suspicious-link": { name: "Suspicious Link", guidancePath: "/guidance/suspicious-link" },
    };
    
    return scamType ? scamTypes[scamType] : null;
  };

  if (error || !result) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navigation />

        <main className="max-w-4xl mx-auto px-4 py-12">
          <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-12 text-center">
            <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
            <h2 className="text-2xl font-semibold text-gray-900 mb-2">
              Something Went Wrong
            </h2>
            <p className="text-gray-600 mb-6">
              We could not generate a risk score. Please try again.
            </p>
            <Button onClick={() => navigate("/")}>
              Return to Home
            </Button>
          </div>
        </main>
      </div>
    );
  }

  const getRiskConfig = (level: RiskLevel) => {
    switch (level) {
      case "high":
        return {
          color: "text-red-600",
          bgColor: "bg-red-50",
          borderColor: "border-red-200",
          icon: AlertTriangle,
          label: "High Risk",
          description: "This message shows strong indicators of a scam",
        };
      case "medium":
        return {
          color: "text-orange-600",
          bgColor: "bg-orange-50",
          borderColor: "border-orange-200",
          icon: AlertCircle,
          label: "Medium Risk",
          description: "This message has some suspicious elements",
        };
      case "low":
        return {
          color: "text-green-600",
          bgColor: "bg-green-50",
          borderColor: "border-green-200",
          icon: CheckCircle,
          label: "Low Risk",
          description: "This message appears safe",
        };
    }
  };

  const config = getRiskConfig(result.riskLevel);
  const Icon = config.icon;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <Navigation />

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 py-12">
        {/* Result Card */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8 mb-8">
          {/* Risk Score Display */}
          <div className={`${config.bgColor} ${config.borderColor} border-2 rounded-2xl p-8 text-center mb-8`}>
            <Icon className={`w-20 h-20 ${config.color} mx-auto mb-4`} />
            <h1 className={`text-4xl font-bold ${config.color} mb-2`}>
              {config.label}
            </h1>
            <p className="text-gray-600 text-lg">
              {config.description}
            </p>
          </div>

          {/* Explanation */}
          <div className="mb-8">
            <h2 className="font-semibold text-gray-900 mb-3">Analysis:</h2>
            <p className="text-gray-700 leading-relaxed">
              {result.explanation}
            </p>
          </div>

          {/* Action Buttons */}
          <div className="grid md:grid-cols-2 gap-4">
            <Button
              onClick={() => navigate(getScamTypeInfo(result.scamType)?.guidancePath || "/guidance")}
              variant="default"
              className="h-12"
            >
              View Guidance
            </Button>
            <Button
              onClick={() => navigate("/learning")}
              variant="outline"
              className="h-12"
            >
              Learn More
            </Button>
          </div>
        </div>

        {/* Additional Actions */}
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
          <div className="flex items-start gap-3">
            <Shield className="w-6 h-6 text-blue-600 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-semibold text-gray-900 mb-1">
                Stay Protected
              </h3>
              <p className="text-sm text-gray-600 mb-3">
                Practice identifying scams to improve your detection skills.
              </p>
              <Button
                onClick={() => navigate("/practice")}
                variant="outline"
                size="sm"
              >
                Start Practice
              </Button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}